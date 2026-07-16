"""Run the whole of Part 2 end to end.

    python -m part2

Equivalent to running the three steps in order:

    python -m part2.build_db             # Step 1: merge, dedup, PROJECT_TYPE
    python -m part2.run_classification   # Steps 2 + 3: classify
    python -m part2.reports              # Step 4: db, xlsx, pdf
"""
from part2 import build_db, reports, run_classification


def main():
    print("=" * 72)
    print("Part 2 Step 1: merge, deduplicate, derive PROJECT_TYPE")
    print("=" * 72)
    build_db.build()

    print()
    print("=" * 72)
    print("Part 2 Steps 2 + 3: classify projects and primary data files")
    print("=" * 72)
    run_classification.run()

    print()
    print("=" * 72)
    print("Part 2 Step 4: deliverables")
    print("=" * 72)
    reports.main()


if __name__ == "__main__":
    main()
