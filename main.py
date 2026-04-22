import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from db.database import init_db, print_stats
from scrapers.ada_scraper import run as run_ada
from scrapers.murray_scraper import run as run_murray
from export.export import run as run_export

def parse_args():
    p = argparse.ArgumentParser(description="QDArchive seeding pipeline")
    p.add_argument("--test", type=int, default=None, metavar="N")
    p.add_argument("--skip-ada", action="store_true")
    p.add_argument("--skip-murray", action="store_true")
    p.add_argument("--export-only", action="store_true")
    return p.parse_args()

def main():
    args = parse_args()
    print("="*60)
    print("QDArchive Seeding - Part 1: Data Acquisition")
    print("Student: 23025328")
    print("="*60)
    init_db()
    if args.export_only:
        run_export()
        return
    if not args.skip_ada:
        run_ada(max_datasets=args.test)
    if not args.skip_murray:
        run_murray(max_datasets=args.test)
    run_export()
    print("\n" + "="*60)
    print("DATABASE SUMMARY")
    print("="*60)
    print_stats()
    print("="*60)

if __name__ == "__main__":
    main()
