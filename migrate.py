import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "23025328-seeding.db"

def column_exists(conn, table, column):
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in cols)

def main():
    print(f"Migrating: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    changes = 0

    if not column_exists(conn, "PROJECTS", "type"):
        conn.execute("""ALTER TABLE PROJECTS ADD COLUMN type TEXT CHECK(type IN ('QDA_PROJECT','QD_PROJECT','OTHER_PROJECT','NOT_A_PROJECT'))""")
        conn.execute("UPDATE PROJECTS SET type = 'QD_PROJECT' WHERE type IS NULL")
        print("  Added PROJECTS.type, backfilled with QD_PROJECT")
        changes += 1
    else:
        print("  PROJECTS.type already exists")

    if not column_exists(conn, "PROJECTS", "class"):
        conn.execute('ALTER TABLE PROJECTS ADD COLUMN "class" TEXT')
        print("  Added PROJECTS.class (NULL for now)")
        changes += 1
    else:
        print("  PROJECTS.class already exists")

    if not column_exists(conn, "FILES", "class"):
        conn.execute('ALTER TABLE FILES ADD COLUMN "class" TEXT')
        print("  Added FILES.class (NULL for now)")
        changes += 1
    else:
        print("  FILES.class already exists")

    conn.commit()

    print("\nPROJECTS columns now:")
    for row in conn.execute("PRAGMA table_info(PROJECTS)").fetchall():
        print(f"  {row[1]} ({row[2]})")

    print("\nRow counts:")
    for t in ("REPOSITORIES","PROJECTS","FILES","KEYWORDS","PERSON_ROLE","LICENSES"):
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n}")

    conn.close()
    print(f"\nDone. {changes} column(s) added.")

if __name__ == "__main__":
    main()
