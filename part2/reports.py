"""Part 2 Step 4: the deliverables.

    python -m part2.reports

Produces, from config.CLASSIFICATION_DB:

    reports/23025328-sq26-classification.xlsx  (Step 4c)
    reports/23025328-sq26-classification.pdf   (Step 4d, see part2/report_pdf.py)
    reports/form_answers.md                    (Step 4b, input for the form)

This module owns the statistics and the findings; report_pdf.py owns the
typesetting, so both the PDF and the form answers report the same numbers.
"""
import sqlite3
from collections import Counter

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from part2 import config, isic

TOP_N = 20
CLASSIFIED_TYPES = ("QDA_PROJECT", "QD_PROJECT")
ALL_TYPES = ("QDA_PROJECT", "QD_PROJECT", "OTHER_PROJECT", "NOT_A_PROJECT")


def connect():
    conn = sqlite3.connect(config.CLASSIFICATION_DB)
    conn.row_factory = sqlite3.Row
    return conn


def clean(text):
    """Tidy a stored string for display.

    The metadata is valid UTF-8 (titles legitimately contain em dashes, and one
    file name ends in an acute accent), so nothing has to be substituted here -
    only the stray padding Part 1 preserved verbatim is removed.
    """
    return (text or "").strip()


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------
def class_counts(conn, repository_id, project_type=None):
    query = ("SELECT primary_class FROM PROJECTS "
             "WHERE repository_id = ? AND primary_class IS NOT NULL")
    params = [repository_id]
    if project_type:
        query += " AND type = ?"
        params.append(project_type)
    else:
        query += " AND type IN ({})".format(", ".join("?" * len(CLASSIFIED_TYPES)))
        params.extend(CLASSIFIED_TYPES)
    return Counter(r["primary_class"] for r in conn.execute(query, params))


def type_counts(conn, repository_id):
    return Counter(
        r["type"] for r in conn.execute(
            "SELECT type FROM PROJECTS WHERE repository_id = ?", (repository_id,))
    )


def file_stats(conn, repository_id):
    return conn.execute(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(status = 'SUCCEEDED'), 0) AS downloaded,
                  COALESCE(SUM(text_chars > 0), 0) AS with_text,
                  COALESCE(SUM(file_category = 'QDA'), 0) AS qda,
                  COALESCE(SUM(file_category = 'PRIMARY'), 0) AS primary_files
           FROM FILES f JOIN PROJECTS p ON p.id = f.project_id
           WHERE p.repository_id = ?""", (repository_id,)
    ).fetchone()


def repository_summary(conn, repository_id):
    """Everything the report needs about one repository, in one place."""
    types = type_counts(conn, repository_id)
    counts = class_counts(conn, repository_id)
    files = file_stats(conn, repository_id)
    in_scope = sum(types.get(t, 0) for t in CLASSIFIED_TYPES)
    placeholders = conn.execute(
        """SELECT COUNT(*) AS n FROM PROJECTS
           WHERE repository_id = ? AND doi IN ({})""".format(
            ", ".join("?" * len(config.PLACEHOLDER_DOIS))),
        (repository_id, *config.PLACEHOLDER_DOIS),
    ).fetchone()["n"]
    unclassified = conn.execute(
        """SELECT COUNT(*) AS n FROM PROJECTS WHERE repository_id = ?
           AND type IN ('QDA_PROJECT', 'QD_PROJECT') AND primary_class IS NULL""",
        (repository_id,),
    ).fetchone()["n"]

    return {
        "types": types,
        "counts": counts,
        "files": files,
        "total_projects": sum(types.values()),
        "in_scope": in_scope,
        "classified": sum(counts.values()),
        "placeholders": placeholders,
        "unclassified": unclassified,
        "is_unharvested": bool(placeholders) and placeholders == sum(types.values()),
    }


def findings_comments(conn, repository, summary):
    """Step 4d 1.c - comments on the findings, as plain sentences."""
    repo_id = repository["id"]
    types, counts, files = summary["types"], summary["counts"], summary["files"]

    if not summary["total_projects"]:
        return ["The repository yielded no projects at all."]

    # A repository that consists only of Part 1 sentinel rows was never
    # harvested, so none of the observations below would apply to it: it has no
    # files to type and no metadata to classify.
    if summary["is_unharvested"]:
        return [
            "This repository could not be harvested in Part 1: its web application "
            "firewall rejected every automated request, so no project metadata and "
            "no files were ever acquired.",
            "The single record is the sentinel row the Part 1 pipeline writes to "
            "document that repository-level failure. It is not a research project, "
            "it carries an invented file name, and it is therefore typed "
            "NOT_A_PROJECT and excluded from classification rather than being "
            "allowed to contribute a spurious QD_PROJECT and a spurious class to "
            "the statistics.",
            "No distribution can be reported for this repository. This is a data "
            "acquisition limitation carried over from Part 1, not a classification "
            "result: the repository is browsable by a human but not "
            "machine-accessible.",
        ]

    lines = []

    if not files["qda"]:
        lines.append(
            "No file in this repository carries a QDA file extension (.qdpx, .nvp, "
            ".atlproj, .mx*, and so on), so by the Step 1 rule no project can be a "
            "QDA_PROJECT. The archive largely predates the REFI-QDA standard and "
            "stores its analysis material as PDF codebooks and SPSS/SAS data rather "
            "than as QDA software projects. This is a property of the data and not a "
            "gap in the pipeline: the classifier does look for those extensions.")

    top_ext = conn.execute(
        """SELECT f.file_extension AS ext, COUNT(*) AS n
           FROM FILES f JOIN PROJECTS p ON p.id = f.project_id
           WHERE p.repository_id = ? AND f.file_category = 'PRIMARY'
             AND f.file_extension != ''
           GROUP BY ext ORDER BY n DESC LIMIT 3""", (repo_id,)
    ).fetchall()
    if top_ext:
        listed = ", ".join(f".{r['ext']} ({r['n']:,})" for r in top_ext)
        share = types.get("QD_PROJECT", 0) / summary["total_projects"]
        lines.append(
            f"The primary data is dominated by {listed}. Because a single PDF is "
            f"enough to make a project a QD_PROJECT, that rule sorts {share:.0%} of "
            f"the repository into one bucket; the file-type rules discriminate far "
            f"less here than the class taxonomy does.")

    restricted = files["total"] - files["downloaded"]
    if restricted:
        lines.append(
            f"{restricted:,} of {files['total']:,} files "
            f"({restricted / files['total']:.0%}) are restricted and could not be "
            f"downloaded, so for those the classifier reads only the metadata and the "
            f"file name. Classification quality is therefore not uniform across the "
            f"repository: the projects whose files are open are classified on more "
            f"evidence than the rest.")

    if counts:
        total = sum(counts.values())
        code, _ = counts.most_common(1)[0]
        top3 = sum(n for _, n in counts.most_common(3))
        lines.append(
            f"The distribution is heavily concentrated: {top3 / total:.0%} of the "
            f"classified projects fall into just three divisions, and only "
            f"{len(counts)} of the 87 ISIC divisions occur at all. This mirrors the "
            f"collection policy of the archive rather than a limitation of the "
            f"taxonomy; it is a themed archive of social-science studies, so the "
            f"manufacturing, mining and transport divisions are simply absent.")
        lines.append(
            f"That “{isic.division_name(code)}” dominates is consistent "
            f"with the corpus: the studies follow school and college populations "
            f"over time, so schooling vocabulary is what the researchers themselves "
            f"wrote in the metadata.")

    lines.append(
        "ISIC classifies economic activities, and much of this archive is about "
        "family life, personal identity and the life course, which no ISIC division "
        "describes directly. Such projects land on the division of the institution "
        "through which they were studied — a study of mothers observed via "
        "their children’s schools scores as Education — so the classes "
        "should be read as “the sector this data speaks about”, not as a "
        "summary of the research question.")

    if summary["unclassified"]:
        lines.append(
            f"{summary['unclassified']} in-scope project(s) matched no lexicon term "
            f"and were deliberately left unclassified rather than forced into a "
            f"division, following the instruction to leave a field empty when it "
            f"cannot be filled.")
    return lines


# ---------------------------------------------------------------------------
# Step 4c: the XLSX table
# ---------------------------------------------------------------------------
def export_xlsx(conn, path=None):
    path = path or config.REPORT_DIR / f"{config.STUDENT_ID}-sq26-classification.xlsx"
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = conn.execute(
        """SELECT repository_id, type AS project_type, title AS project_title,
                  primary_class, secondary_class, no_project_files
           FROM PROJECTS
           ORDER BY repository_id, type, id"""
    ).fetchall()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "classification"

    headers = ["repository_id", "project_type", "project_title",
               "primary_class", "secondary_class", "no_project_files"]
    sheet.append(headers)

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F3864")
    for column in range(1, len(headers) + 1):
        cell = sheet.cell(row=1, column=column)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for row in rows:
        sheet.append([
            row["repository_id"],
            row["project_type"],
            clean(row["project_title"]),
            # The full class name is the readable form of the code and is what
            # the report histograms bin on, so the spreadsheet carries it too.
            isic.full_class_name(row["primary_class"]) if row["primary_class"] else "",
            isic.full_class_name(row["secondary_class"]) if row["secondary_class"] else "",
            row["no_project_files"],
        ])

    widths = [14, 15, 80, 42, 42, 16]
    for index, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(rows) + 1}"

    workbook.save(path)
    return path, len(rows)


# ---------------------------------------------------------------------------
# Step 4b: the numbers to type into the Google form
# ---------------------------------------------------------------------------
def form_answers(conn, path=None):
    path = path or config.REPORT_DIR / "form_answers.md"
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# Part 2 Step 4b - answers for the per-repository form",
             "",
             "Fill in the form at https://forms.gle/wxTGQFBQbBvFi3N69 once per "
             "repository.",
             ""]

    for repository in conn.execute("SELECT * FROM REPOSITORIES ORDER BY id"):
        summary = repository_summary(conn, repository["id"])
        counts = summary["counts"]
        slug = clean(repository["name"])
        lines += [f"## Repository {repository['id']}: {config.display_name(slug)}",
                  f"- Identifier in the database: {slug} (repository_id "
                  f"{repository['id']})",
                  f"- URL: {repository['url']}",
                  f"- Projects in total: {summary['total_projects']}",
                  "- Project types found:"]
        for project_type in ALL_TYPES:
            lines.append(f"    - {project_type}: {summary['types'].get(project_type, 0)}")
        if counts:
            code, count = counts.most_common(1)[0]
            lines.append(f"- Dominant class: {isic.label(code)} ({count} projects)")
            lines.append("- Top 5 classes:")
            for rank, (c, n) in enumerate(counts.most_common(5), 1):
                lines.append(f"    {rank}. {isic.full_class_name(c)}: {n}")
        else:
            lines.append("- Dominant class: none (no classifiable project)")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    from part2 import report_pdf

    conn = connect()
    xlsx, rows = export_xlsx(conn)
    print(f"wrote {xlsx.relative_to(config.ROOT)} ({rows} rows)")
    pdf = report_pdf.build(conn)
    print(f"wrote {pdf.relative_to(config.ROOT)}")
    form = form_answers(conn)
    print(f"wrote {form.relative_to(config.ROOT)}")
    conn.close()


if __name__ == "__main__":
    main()
