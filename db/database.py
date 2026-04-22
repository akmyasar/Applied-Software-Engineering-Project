import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "23025328-seeding.db"

ALLOWED_FILE_STATUS = {
    "SUCCEEDED",
    "FAILED_LOGIN_REQUIRED",
    "FAILED_SERVER_UNRESPONSIVE",
    "FAILED_TOO_LARGE",
}

ALLOWED_PERSON_ROLE = {
    "AUTHOR",
    "UPLOADER",
    "OWNER",
    "OTHER",
    "UNKNOWN",
}

QDA_EXTENSIONS = {
    "qdpx", "qdpx", "qdp", "qda", "nvp", "nvpx", "nva", "mx", "mx24",
    "maxqda", "maxqdaproject", "atlproj"
}

PRIMARY_DATA_EXTENSIONS = {
    "txt", "pdf", "rtf", "doc", "docx", "odt", "md"
}


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS REPOSITORIES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS PROJECTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_string TEXT,
            repository_id INTEGER NOT NULL,
            repository_url TEXT NOT NULL,
            project_url TEXT NOT NULL,
            version TEXT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            language TEXT,
            doi TEXT,
            upload_date TEXT,
            download_date TEXT NOT NULL,
            download_repository_folder TEXT NOT NULL,
            download_project_folder TEXT NOT NULL,
            download_version_folder TEXT,
            download_method TEXT NOT NULL,
            FOREIGN KEY (repository_id) REFERENCES REPOSITORIES(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS FILES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS KEYWORDS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS PERSON_ROLE (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS LICENSES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            license TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
        )
    """)

    conn.commit()
    conn.close()


def upsert_repository(name, url):
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id FROM REPOSITORIES WHERE name = ? AND url = ?",
        (name, url)
    ).fetchone()
    if row:
        conn.close()
        return row["id"]

    cur.execute(
        "INSERT INTO REPOSITORIES (name, url) VALUES (?, ?)",
        (name, url)
    )
    conn.commit()
    repo_id = cur.lastrowid
    conn.close()
    return repo_id


def project_doi_exists(doi):
    if not doi:
        return False
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM PROJECTS WHERE doi = ? LIMIT 1",
        (doi,)
    ).fetchone()
    conn.close()
    return row is not None


def insert_project(
    query_string,
    repository_id,
    repository_url,
    project_url,
    version,
    title,
    description,
    language,
    doi,
    upload_date,
    download_repository_folder,
    download_project_folder,
    download_version_folder,
    download_method,
    project_type=None,
    **kwargs,
):
    """
    project_type is accepted only for compatibility with the current murray_scraper.py.
    It is intentionally ignored in Part 1 because the current PROJECTS schema does not
    include a 'type' column.
    """
    conn = get_conn()
    cur = conn.cursor()

    download_date = datetime.now().isoformat(timespec="seconds")

    cur.execute("""
        INSERT INTO PROJECTS (
            query_string,
            repository_id,
            repository_url,
            project_url,
            version,
            title,
            description,
            language,
            doi,
            upload_date,
            download_date,
            download_repository_folder,
            download_project_folder,
            download_version_folder,
            download_method
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        query_string,
        repository_id,
        repository_url,
        project_url,
        version,
        title or "",
        description or "",
        language,
        doi,
        upload_date,
        download_date,
        download_repository_folder,
        download_project_folder,
        download_version_folder,
        download_method,
    ))

    conn.commit()
    project_id = cur.lastrowid
    conn.close()
    return project_id


def insert_file(project_id, file_name, file_type, status):
    status = (status or "").strip().upper()
    if status not in ALLOWED_FILE_STATUS:
        status = "FAILED_SERVER_UNRESPONSIVE"

    conn = get_conn()
    conn.execute(
        "INSERT INTO FILES (project_id, file_name, file_type, status) VALUES (?, ?, ?, ?)",
        (project_id, file_name or "", file_type or "", status)
    )
    conn.commit()
    conn.close()


def insert_keyword(project_id, keyword):
    if not keyword:
        return
    conn = get_conn()
    conn.execute(
        "INSERT INTO KEYWORDS (project_id, keyword) VALUES (?, ?)",
        (project_id, str(keyword))
    )
    conn.commit()
    conn.close()


def insert_person_role(project_id, name, role):
    if not name:
        return
    role = (role or "UNKNOWN").strip().upper()
    if role not in ALLOWED_PERSON_ROLE:
        role = "UNKNOWN"

    conn = get_conn()
    conn.execute(
        "INSERT INTO PERSON_ROLE (project_id, name, role) VALUES (?, ?, ?)",
        (project_id, str(name), role)
    )
    conn.commit()
    conn.close()


def insert_license(project_id, license_value):
    value = (license_value or "UNKNOWN").strip()
    conn = get_conn()
    conn.execute(
        "INSERT INTO LICENSES (project_id, license) VALUES (?, ?)",
        (project_id, value)
    )
    conn.commit()
    conn.close()


def classify_project(files_list):
    """
    Kept only so the current murray_scraper.py can still import and call it.
    Part 1 does not store this in the DB yet.
    """
    exts = set()

    for file_entry in files_list or []:
        filename = ""
        if isinstance(file_entry, dict):
            df = file_entry.get("dataFile", {})
            filename = df.get("filename") or file_entry.get("label") or ""
        if "." in filename:
            exts.add(filename.rsplit(".", 1)[-1].lower())

    if exts & QDA_EXTENSIONS:
        return "QDA_PROJECT"
    if exts & PRIMARY_DATA_EXTENSIONS:
        return "QD_PROJECT"
    if exts:
        return "OTHER_PROJECT"
    return "NOT_A_PROJECT"


def print_stats():
    conn = get_conn()
    tables = [
        "REPOSITORIES",
        "PROJECTS",
        "FILES",
        "KEYWORDS",
        "PERSON_ROLE",
        "LICENSES",
    ]
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
        print(f"  {table:<24}: {count:5d} rows")
    conn.close()
