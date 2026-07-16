"""Part 2 Step 1: merge the seeding database(s), remove duplicates and derive
the PROJECT_TYPE of every project.

    python -m part2.build_db

Reads config.SEEDING_DB (plus config.EXTRA_SEEDING_DBS) and writes
config.CLASSIFICATION_DB.
"""
import sqlite3
from collections import Counter
from pathlib import Path

from part2 import config, isic

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

PROJECT_COLUMNS = [
    "query_string", "repository_id", "repository_url", "project_url", "version",
    "title", "description", "language", "doi", "upload_date", "download_date",
    "download_repository_folder", "download_project_folder",
    "download_version_folder", "download_method",
]


def dedup_key(project, repo_name):
    """Identity of a project across databases.

    A DOI identifies a project globally, so it wins when present. Otherwise the
    project URL is used, and the repository-scoped title is the last resort.
    """
    doi = (project["doi"] or "").strip().lower()
    if doi and doi not in {d.lower() for d in config.PLACEHOLDER_DOIS}:
        return ("doi", doi)
    url = (project["project_url"] or "").strip().lower()
    if url:
        return ("url", url)
    return ("title", repo_name.lower(), (project["title"] or "").strip().lower())


def derive_project_type(categories, is_placeholder=False):
    """Part 2 Step 1: derive the PROJECT_TYPE from the file types.

    * QDA_PROJECT   if there is a file with a QDA file extension
    * QD_PROJECT    if not a QDA_PROJECT and there are primary data files
    * OTHER_PROJECT if not a QD_PROJECT and there are valid data files
    * NOT_A_PROJECT if nothing can be derived about file types
    """
    if is_placeholder:
        return "NOT_A_PROJECT"

    categories = set(categories)
    if "QDA" in categories:
        return "QDA_PROJECT"
    if "PRIMARY" in categories:
        return "QD_PROJECT"
    if "OTHER" in categories:
        return "OTHER_PROJECT"
    return "NOT_A_PROJECT"


def local_path_for(project, file_name):
    """Where the Part 1 pipeline stored a file, if it stored it at all."""
    parts = [
        project["download_repository_folder"],
        project["download_project_folder"],
        project["download_version_folder"],
    ]
    folder = config.DATA_DIR.joinpath(*[p for p in parts if p])
    candidate = folder / (file_name or "").strip()
    if candidate.is_file():
        return str(candidate.relative_to(config.ROOT))
    # Some versions of the pipeline wrote straight into the project folder.
    parts = [project["download_repository_folder"], project["download_project_folder"]]
    candidate = config.DATA_DIR.joinpath(*[p for p in parts if p]) / (file_name or "").strip()
    if candidate.is_file():
        return str(candidate.relative_to(config.ROOT))
    return None


def create_schema(conn):
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.executemany(
        "INSERT INTO ISIC_CLASSES (division, section, section_name, name) VALUES (?, ?, ?, ?)",
        [
            (code, isic.section_of(code), isic.section_name(isic.section_of(code)),
             isic.division_name(code))
            for code in isic.DIVISION_CODES
        ],
    )


def build(source_dbs=None, verbose=True):
    source_dbs = source_dbs or [config.SEEDING_DB, *config.EXTRA_SEEDING_DBS]
    source_dbs = [Path(p) for p in source_dbs]

    for path in source_dbs:
        if not path.is_file():
            raise FileNotFoundError(f"seeding database not found: {path}")

    if config.CLASSIFICATION_DB.exists():
        config.CLASSIFICATION_DB.unlink()

    out = sqlite3.connect(config.CLASSIFICATION_DB)
    out.row_factory = sqlite3.Row
    create_schema(out)

    repo_ids = {}          # (name, url) -> new repository id
    seen = {}              # dedup key -> new project id
    duplicates = 0
    type_counts = Counter()

    for db_path in source_dbs:
        src = sqlite3.connect(db_path)
        src.row_factory = sqlite3.Row

        repo_names = {
            r["id"]: r["name"] for r in src.execute("SELECT id, name FROM REPOSITORIES")
        }

        for repo in src.execute("SELECT * FROM REPOSITORIES"):
            key = (repo["name"], repo["url"])
            if key not in repo_ids:
                cur = out.execute(
                    "INSERT INTO REPOSITORIES (name, url) VALUES (?, ?)", key
                )
                repo_ids[key] = cur.lastrowid

        for project in src.execute("SELECT * FROM PROJECTS"):
            repo = src.execute(
                "SELECT name, url FROM REPOSITORIES WHERE id = ?",
                (project["repository_id"],),
            ).fetchone()
            repo_name = repo["name"] if repo else str(project["repository_id"])
            new_repo_id = repo_ids[(repo["name"], repo["url"])] if repo else None

            key = dedup_key(project, repo_name)
            if key in seen:
                duplicates += 1
                continue

            files = src.execute(
                "SELECT * FROM FILES WHERE project_id = ?", (project["id"],)
            ).fetchall()

            is_placeholder = (project["doi"] or "") in config.PLACEHOLDER_DOIS
            categories = {
                "UNKNOWN" if is_placeholder
                else config.file_category(f["file_name"], f["file_type"])
                for f in files
            }
            project_type = derive_project_type(categories, is_placeholder)
            type_counts[project_type] += 1

            values = [project[c] for c in PROJECT_COLUMNS]
            values[PROJECT_COLUMNS.index("repository_id")] = new_repo_id
            cur = out.execute(
                f"""INSERT INTO PROJECTS ({", ".join(PROJECT_COLUMNS)},
                        type, no_project_files, source_db, source_project_id)
                    VALUES ({", ".join("?" * len(PROJECT_COLUMNS))}, ?, ?, ?, ?)""",
                (*values, project_type, len(files), db_path.name, project["id"]),
            )
            new_project_id = cur.lastrowid
            seen[key] = new_project_id

            for f in files:
                ext = config.normalize_extension(f["file_name"])
                category = ("UNKNOWN" if is_placeholder
                            else config.file_category(f["file_name"], f["file_type"]))
                out.execute(
                    """INSERT INTO FILES (project_id, file_name, file_type, status,
                                          file_extension, file_category, local_path)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (new_project_id, f["file_name"], f["file_type"], f["status"],
                     ext, category, local_path_for(project, f["file_name"])),
                )

            for table, columns in (
                ("KEYWORDS", ("keyword",)),
                ("PERSON_ROLE", ("name", "role")),
                ("LICENSES", ("license",)),
            ):
                rows = src.execute(
                    f"SELECT {', '.join(columns)} FROM {table} WHERE project_id = ?",
                    (project["id"],),
                ).fetchall()
                out.executemany(
                    f"""INSERT INTO {table} (project_id, {', '.join(columns)})
                        VALUES (?, {', '.join('?' * len(columns))})""",
                    [(new_project_id, *[r[c] for c in columns]) for r in rows],
                )

        src.close()

    out.commit()

    if verbose:
        print(f"merged {len(source_dbs)} database(s) -> {config.CLASSIFICATION_DB.name}")
        print(f"  repositories     : {len(repo_ids)}")
        print(f"  projects         : {len(seen)}")
        print(f"  duplicates removed: {duplicates}")
        files_with_text = out.execute(
            "SELECT COUNT(*) FROM FILES WHERE local_path IS NOT NULL"
        ).fetchone()[0]
        print(f"  files            : {out.execute('SELECT COUNT(*) FROM FILES').fetchone()[0]}"
              f" ({files_with_text} present on disk)")
        print("  project types:")
        for project_type, count in type_counts.most_common():
            print(f"    {project_type:<15}: {count}")

    out.close()
    return type_counts


if __name__ == "__main__":
    build()
