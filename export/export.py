import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "23025328-seeding.db"
OUT_DIR = Path(__file__).parent.parent / "export"

def export_table(conn, table):
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    if not rows:
        print(f"  [EXPORT] {table}: 0 rows")
        return
    out_path = OUT_DIR / f"{table.lower()}.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([d[0] for d in conn.execute(f"SELECT * FROM {table} LIMIT 0").description])
        writer.writerows(rows)
    print(f"  [EXPORT] {table}: {len(rows)} rows -> {out_path}")

def run():
    print("\n[EXPORT] Exporting to CSV...")
    OUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    for table in ("REPOSITORIES","PROJECTS","FILES","KEYWORDS","PERSON_ROLE","LICENSES"):
        export_table(conn, table)
    conn.close()
    print("[EXPORT] Done.")

if __name__ == "__main__":
    run()
