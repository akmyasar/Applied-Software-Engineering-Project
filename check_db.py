import sqlite3
conn = sqlite3.connect('23025328-seeding.db')
conn.row_factory = sqlite3.Row

print('=== PROJECTS columns ===')
cols = conn.execute("PRAGMA table_info(PROJECTS)").fetchall()
for c in cols:
    print(f"  {c['cid']}. {c['name']} ({c['type']})")

print()
print('=== FILES columns ===')
cols = conn.execute("PRAGMA table_info(FILES)").fetchall()
for c in cols:
    print(f"  {c['cid']}. {c['name']} ({c['type']})")

print()
print('=== SAMPLE PROJECTS ===')
for r in conn.execute("SELECT * FROM PROJECTS LIMIT 3").fetchall():
    print(dict(r))

print()
print('=== SAMPLE FILES ===')
for r in conn.execute("SELECT * FROM FILES LIMIT 5").fetchall():
    print(dict(r))

conn.close()
