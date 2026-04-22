import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import (upsert_repository, insert_project, project_doi_exists,
                          insert_file, insert_keyword, insert_person_role, insert_license)
from pipeline.downloader import download_file, polite_sleep

REPO_NAME       = "harvard-murray-archive"
REPO_URL        = "https://www.murray.harvard.edu"
DATAVERSE_BASE  = "https://dataverse.harvard.edu"
BASE_API        = f"{DATAVERSE_BASE}/api"
SUBTREE         = "mra"
QUERY_STRING    = "*"
DOWNLOAD_METHOD = "API-CALL"
DATA_ROOT       = Path(__file__).parent.parent / "data" / REPO_NAME
PER_PAGE        = 100
POLITE_DELAY    = 2.0


def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": "QDArchive-Seeder/1.0 (FAU Erlangen; student 23025328)"})
    return s


def search_datasets(session):
    all_items = []
    start = 0
    while True:
        url = (f"{BASE_API}/search?q={QUERY_STRING}&subtree={SUBTREE}"
               f"&type=dataset&per_page={PER_PAGE}&start={start}")
        print(f"  [MRA] Searching: start={start}")
        try:
            resp = session.get(url, timeout=30)
        except requests.exceptions.RequestException as exc:
            print(f"  [MRA] Search failed: {exc}")
            break
        if resp.status_code != 200:
            print(f"  [MRA] HTTP {resp.status_code}")
            break
        data  = resp.json().get("data", {})
        items = data.get("items", [])
        total = data.get("total_count", 0)
        all_items.extend(items)
        print(f"  [MRA] Got {len(items)} items (total={total})")
        if start + PER_PAGE >= total:
            break
        start += PER_PAGE
        polite_sleep(POLITE_DELAY)
    return all_items


def fetch_dataset_metadata(session, global_id):
    url = f"{BASE_API}/datasets/:persistentId/?persistentId={global_id}"
    try:
        resp = session.get(url, timeout=30)
    except requests.exceptions.RequestException as exc:
        print(f"    [MRA] Metadata fetch failed: {exc}")
        return None
    if resp.status_code != 200:
        print(f"    [MRA] HTTP {resp.status_code} for {global_id}")
        return None
    return resp.json().get("data", {})


def _get_all_fields(metadata):
    fields = []
    for block in metadata.get("metadataBlocks", {}).values():
        fields.extend(block.get("fields", []))
    return fields


def _extract_field(fields, type_name):
    for f in fields:
        if f.get("typeName") == type_name:
            val = f.get("value")
            if isinstance(val, list):
                parts = []
                for item in val:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict):
                        for v in item.values():
                            if isinstance(v, dict) and "value" in v:
                                parts.append(str(v["value"]))
                return "; ".join(parts) if parts else None
            return str(val) if val else None
    return None


def process_dataset(session, search_item, repo_id):
    global_id = search_item.get("global_id", "")
    if not global_id:
        return
    doi = global_id.replace("doi:", "").replace("hdl:", "")
    if project_doi_exists(doi):
        print(f"    [MRA] Already processed {doi}, skipping.")
        return

    print(f"    [MRA] Processing: {global_id}")
    polite_sleep(POLITE_DELAY)

    meta = fetch_dataset_metadata(session, global_id)
    if not meta:
        return

    latest  = meta.get("latestVersion", {})
    fields  = _get_all_fields(latest)

    title       = _extract_field(fields, "title") or search_item.get("name", "")
    description = _extract_field(fields, "dsDescription") or search_item.get("description", "")
    language    = _extract_field(fields, "language")
    upload_date = (latest.get("releaseTime") or "")[:10]
    version     = f"{latest.get('versionNumber','')}.{latest.get('versionMinorNumber','')}".strip(".")
    project_url = search_item.get("url", f"{DATAVERSE_BASE}/dataset.xhtml?persistentId={global_id}")
    doi_slug    = doi.replace("/", "_").replace(":", "_")
    ver_folder  = f"v{version}" if version else "v1"

    project_id = insert_project(
        query_string=QUERY_STRING, repository_id=repo_id, repository_url=REPO_URL,
        project_url=project_url, version=version, title=title, description=description,
        language=language, doi=doi, upload_date=upload_date,
        download_repository_folder=REPO_NAME, download_project_folder=doi_slug,
        download_version_folder=ver_folder, download_method=DOWNLOAD_METHOD)

    # Authors
    for f in fields:
        if f.get("typeName") == "author":
            for entry in f.get("value", []):
                if isinstance(entry, dict):
                    nf = entry.get("authorName", {})
                    name = nf.get("value", "") if isinstance(nf, dict) else str(nf)
                    if name:
                        insert_person_role(project_id, name, "AUTHOR")

    # Keywords
    for f in fields:
        if f.get("typeName") == "keyword":
            for kw in f.get("value", []):
                if isinstance(kw, dict):
                    kv = kw.get("keywordValue", {})
                    val = kv.get("value", "") if isinstance(kv, dict) else str(kv)
                    if val:
                        insert_keyword(project_id, val)

    # License
    terms = latest.get("termsOfUse", "") or latest.get("license", {})
    if isinstance(terms, dict):
        license_str = terms.get("name", "") or terms.get("uri", "")
    else:
        license_str = str(terms) if terms else ""
    insert_license(project_id, license_str or "UNKNOWN")

    # Files
    dest_root = DATA_ROOT / doi_slug / ver_folder
    dest_root.mkdir(parents=True, exist_ok=True)
    files_list = latest.get("files", [])
    print(f"    [MRA] {len(files_list)} files for project_id={project_id}")

    for file_entry in files_list:
        df           = file_entry.get("dataFile", {})
        file_id      = df.get("id")
        filename     = df.get("filename", f"file_{file_id}")
        content_type = df.get("contentType", "")
        file_type    = content_type.split("/")[-1] if content_type else Path(filename).suffix.lstrip(".")
        restricted   = file_entry.get("restricted", False)

        if restricted or df.get("embargo"):
            insert_file(project_id, filename, file_type, "FAILED_LOGIN_REQUIRED")
            print(f"      [MRA] RESTRICTED: {filename}")
            continue

        download_url = f"{BASE_API}/access/datafile/{file_id}"
        dest_path    = dest_root / filename
        polite_sleep(0.5)
        status, nbytes = download_file(download_url, dest_path)
        insert_file(project_id, filename, file_type, status)
        print(f"      [MRA] {status}: {filename} ({nbytes} bytes)")


def run(max_datasets=None):
    print("\n" + "="*60)
    print("Murray Research Archive Scraper (Harvard Dataverse)")
    print("="*60)
    session = _session()
    repo_id = upsert_repository(REPO_NAME, REPO_URL)
    print(f"[MRA] Repository id={repo_id}")
    items = search_datasets(session)
    print(f"[MRA] Total datasets found: {len(items)}")
    if max_datasets:
        items = items[:max_datasets]
    for i, item in enumerate(items, 1):
        print(f"\n[MRA] Dataset {i}/{len(items)}")
        try:
            process_dataset(session, item, repo_id)
        except Exception as exc:
            print(f"  [MRA] ERROR: {exc}")
        polite_sleep(POLITE_DELAY)
    print("\n[MRA] Done.")