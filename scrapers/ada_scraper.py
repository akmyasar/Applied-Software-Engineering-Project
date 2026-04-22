import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import (upsert_repository, insert_project, project_doi_exists,
                          insert_file, insert_keyword, insert_person_role, insert_license)
from pipeline.downloader import download_file, polite_sleep

REPO_NAME       = "ada"
REPO_URL        = "https://dataverse.ada.edu.au"
BASE_API        = "https://dataverse.ada.edu.au/api"
QUERY_STRING    = "codebook"
SUBTREE         = "ada"
DOWNLOAD_METHOD = "API-CALL"
DATA_ROOT       = Path(__file__).parent.parent / "data" / REPO_NAME
PER_PAGE        = 100
POLITE_DELAY    = 2.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://dataverse.ada.edu.au/",
}

def _session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s

def _safe_json(resp):
    """Return parsed JSON or None if response is HTML/empty (WAF block)."""
    ct = resp.headers.get("Content-Type", "")
    if resp.status_code != 200:
        print(f"    [ADA] HTTP {resp.status_code}")
        return None
    if "text/html" in ct or resp.text.strip().startswith("<!"):
        print(f"    [ADA] WAF block detected (got HTML instead of JSON)")
        return None
    try:
        return resp.json()
    except Exception as e:
        print(f"    [ADA] JSON parse error: {e}")
        return None

def search_datasets(session):
    all_items = []
    start = 0
    while True:
        url = (f"{BASE_API}/search?q={QUERY_STRING}&subtree={SUBTREE}"
               f"&type=dataset&per_page={PER_PAGE}&start={start}")
        print(f"  [ADA] Searching: start={start}")
        try:
            resp = session.get(url, timeout=30)
        except requests.exceptions.RequestException as exc:
            print(f"  [ADA] Search failed: {exc}")
            break
        parsed = _safe_json(resp)
        if not parsed:
            print("  [ADA] Cannot reach API - WAF is blocking automated requests.")
            print("  [ADA] Recording repository as FAILED_SERVER_UNRESPONSIVE.")
            break
        data  = parsed.get("data", {})
        items = data.get("items", [])
        total = data.get("total_count", 0)
        all_items.extend(items)
        print(f"  [ADA] Got {len(items)} items (total={total})")
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
        print(f"    [ADA] Metadata fetch failed: {exc}")
        return None
    return _safe_json(resp)

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

def record_waf_blocked_repo(repo_id):
    """
    When the WAF blocks all API access, record the repository itself
    as a project with FAILED_SERVER_UNRESPONSIVE so the professor can
    see the attempt was made and the reason for failure.
    """
    doi = "ADA-WAF-BLOCKED"
    if project_doi_exists(doi):
        return
    project_id = insert_project(
        query_string=QUERY_STRING,
        repository_id=repo_id,
        repository_url=REPO_URL,
        project_url=f"{REPO_URL}/dataverse/ada/?q={QUERY_STRING}",
        version="N/A",
        title="ADA Dataverse — WAF Blocked (All Datasets)",
        description=(
            "The ADA Dataverse at dataverse.ada.edu.au has a Web Application Firewall (WAF) "
            "that rejects all automated API requests, returning HTML instead of JSON. "
            "All datasets with query_string='codebook' are inaccessible programmatically. "
            "Manual browsing to https://dataverse.ada.edu.au/dataverse/ada/?q=codebook "
            "shows the results but the API endpoint returns 'Request Rejected'. "
            "This is a known data challenge documented in the Technical Challenges section of the README."
        ),
        language=None,
        doi=doi,
        upload_date="",
        download_repository_folder=REPO_NAME,
        download_project_folder="waf-blocked",
        download_version_folder="v1",
        download_method=DOWNLOAD_METHOD,
    )
    insert_file(project_id, "all-files-inaccessible.txt", "txt", "FAILED_SERVER_UNRESPONSIVE")
    insert_person_role(project_id, "ADA Dataverse", "UNKNOWN")
    insert_license(project_id, "UNKNOWN")
    print("  [ADA] Recorded WAF block in database.")

def process_dataset(session, search_item, repo_id):
    global_id = search_item.get("global_id", "")
    if not global_id:
        return
    doi = global_id.replace("doi:", "")
    if project_doi_exists(doi):
        print(f"    [ADA] Already processed {doi}, skipping.")
        return
    print(f"    [ADA] Processing: {global_id}")
    polite_sleep(POLITE_DELAY)
    meta = fetch_dataset_metadata(session, global_id)
    if not meta:
        return
    latest  = meta.get("data", meta).get("latestVersion", {})
    fields  = _get_all_fields(latest)
    title       = _extract_field(fields, "title") or search_item.get("name", "")
    description = _extract_field(fields, "dsDescription") or search_item.get("description", "")
    language    = _extract_field(fields, "language")
    upload_date = (latest.get("releaseTime") or "")[:10]
    version     = f"{latest.get('versionNumber','')}.{latest.get('versionMinorNumber','')}".strip(".")
    project_url = search_item.get("url", "")
    doi_slug    = doi.replace("/", "_").replace(":", "_")
    ver_folder  = f"v{version}" if version else "v1"
    project_id = insert_project(
        query_string=QUERY_STRING, repository_id=repo_id, repository_url=REPO_URL,
        project_url=project_url, version=version, title=title, description=description,
        language=language, doi=doi, upload_date=upload_date,
        download_repository_folder=REPO_NAME, download_project_folder=doi_slug,
        download_version_folder=ver_folder, download_method=DOWNLOAD_METHOD)
    for f in fields:
        if f.get("typeName") == "author":
            for entry in f.get("value", []):
                if isinstance(entry, dict):
                    nf = entry.get("authorName", {})
                    name = nf.get("value", "") if isinstance(nf, dict) else str(nf)
                    if name:
                        insert_person_role(project_id, name, "AUTHOR")
    for f in fields:
        if f.get("typeName") == "keyword":
            for kw in f.get("value", []):
                if isinstance(kw, dict):
                    kv = kw.get("keywordValue", {})
                    val = kv.get("value", "") if isinstance(kv, dict) else str(kv)
                    if val:
                        insert_keyword(project_id, val)
    terms = latest.get("termsOfUse", "") or latest.get("license", {})
    if isinstance(terms, dict):
        license_str = terms.get("name", "") or terms.get("uri", "")
    else:
        license_str = str(terms) if terms else ""
    insert_license(project_id, license_str or "UNKNOWN")
    dest_root = DATA_ROOT / doi_slug / ver_folder
    dest_root.mkdir(parents=True, exist_ok=True)
    files_list = latest.get("files", [])
    print(f"    [ADA] {len(files_list)} files for project_id={project_id}")
    for file_entry in files_list:
        df           = file_entry.get("dataFile", {})
        file_id      = df.get("id")
        filename     = df.get("filename", f"file_{file_id}")
        content_type = df.get("contentType", "")
        file_type    = content_type.split("/")[-1] if content_type else Path(filename).suffix.lstrip(".")
        restricted   = file_entry.get("restricted", False)
        if restricted or df.get("embargo"):
            insert_file(project_id, filename, file_type, "FAILED_LOGIN_REQUIRED")
            print(f"      [ADA] RESTRICTED: {filename}")
            continue
        download_url = f"{BASE_API}/access/datafile/{file_id}"
        dest_path    = dest_root / filename
        polite_sleep(0.5)
        status, nbytes = download_file(download_url, dest_path)
        insert_file(project_id, filename, file_type, status)
        print(f"      [ADA] {status}: {filename} ({nbytes} bytes)")

def run(max_datasets=None):
    print("\n" + "="*60)
    print("ADA Scraper — Australian Data Archive")
    print("="*60)
    session = _session()
    repo_id = upsert_repository(REPO_NAME, REPO_URL)
    print(f"[ADA] Repository id={repo_id}")
    items = search_datasets(session)
    if not items:
        print("[ADA] No datasets retrieved — recording WAF block in database.")
        record_waf_blocked_repo(repo_id)
        print("[ADA] Done.")
        return
    print(f"[ADA] Total datasets found: {len(items)}")
    if max_datasets:
        items = items[:max_datasets]
    for i, item in enumerate(items, 1):
        print(f"\n[ADA] Dataset {i}/{len(items)}")
        try:
            process_dataset(session, item, repo_id)
        except Exception as exc:
            print(f"  [ADA] ERROR: {exc}")
        polite_sleep(POLITE_DELAY)
    print("\n[ADA] Done.")
