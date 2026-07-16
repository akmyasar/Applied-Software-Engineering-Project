"""Part 2 Step 4d: the report.

Typesets reports/23025328-sq26-classification.pdf: a cover page, a table of
contents, the method, the per-repository distributions (histogram, ranked table
and comments), the technical challenges and a conclusion.

The body is portrait A4. Figure pages switch to landscape, because a histogram
whose bins are full ISIC class names needs the width to stay legible; the page
template switches back afterwards.
"""
from collections import Counter
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

from part2 import charts, config, isic, reports

NAVY = colors.HexColor("#1F3864")
ACCENT = colors.HexColor("#2F5496")
GREY = colors.HexColor("#595959")
LIGHT = colors.HexColor("#D9E2F3")
RULE = colors.HexColor("#BFBFBF")
ZEBRA = colors.HexColor("#F2F5FB")

MARGIN = 20 * mm
STUDENT_NAME = "A K M Yasar"
UNIVERSITY = "Friedrich-Alexander-Universität Erlangen-Nürnberg"
CHAIR = "Professorship for Open-Source Software"
SUPERVISOR = "Prof. Dr. Dirk Riehle"
DEGREE = "M.Sc. Data Science"
COURSE = "Applied Software Engineering Project"


# ---------------------------------------------------------------------------
# Document scaffolding
# ---------------------------------------------------------------------------
class ReportTemplate(BaseDocTemplate):
    """Adds the running header/footer and feeds the table of contents."""

    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.section_counter = 0

        portrait_frame = Frame(MARGIN, MARGIN + 8 * mm,
                               A4[0] - 2 * MARGIN, A4[1] - 2 * MARGIN - 12 * mm,
                               id="body")
        cover_frame = Frame(MARGIN, MARGIN, A4[0] - 2 * MARGIN, A4[1] - 2 * MARGIN,
                            id="cover")
        landscape_size = landscape(A4)
        landscape_frame = Frame(MARGIN, MARGIN + 8 * mm,
                                landscape_size[0] - 2 * MARGIN,
                                landscape_size[1] - 2 * MARGIN - 12 * mm,
                                id="figure")

        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover_frame], pagesize=A4),
            PageTemplate(id="body", frames=[portrait_frame],
                         onPage=self._decorate, pagesize=A4),
            PageTemplate(id="figure", frames=[landscape_frame],
                         onPage=self._decorate, pagesize=landscape_size),
        ])

    def _decorate(self, canvas, doc):
        canvas.saveState()
        width, _height = canvas._pagesize
        top = canvas._pagesize[1] - MARGIN + 6 * mm

        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(GREY)
        canvas.drawString(MARGIN, top, "Seeding QDArchive — Part 2: Data Classification")
        canvas.drawRightString(width - MARGIN, top,
                               f"{STUDENT_NAME} · {config.STUDENT_ID}")
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN, top - 2 * mm, width - MARGIN, top - 2 * mm)

        bottom = MARGIN - 2 * mm
        canvas.line(MARGIN, bottom + 5 * mm, width - MARGIN, bottom + 5 * mm)
        canvas.drawCentredString(width / 2, bottom, str(canvas.getPageNumber()))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        """Register headings with the table of contents."""
        if not isinstance(flowable, Paragraph):
            return
        style = flowable.style.name
        if style == "H1":
            self.notify("TOCEntry", (0, flowable.getPlainText(), self.page))
        elif style == "H2":
            self.notify("TOCEntry", (1, flowable.getPlainText(), self.page))


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "CoverTitle", fontName="Helvetica-Bold", fontSize=30, leading=35,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle(
        "CoverSubtitle", fontName="Helvetica", fontSize=17, leading=22,
        textColor=ACCENT, alignment=TA_CENTER, spaceAfter=2))
    styles.add(ParagraphStyle(
        "CoverMeta", fontName="Helvetica", fontSize=10.5, leading=16,
        textColor=GREY, alignment=TA_CENTER))
    styles.add(ParagraphStyle(
        "H1", fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=NAVY,
        spaceBefore=6, spaceAfter=8, keepWithNext=1))
    # Same look as H1, but afterFlowable ignores it, so the contents page does
    # not list itself.
    styles.add(ParagraphStyle(
        "H1Plain", parent=styles["H1"]))
    styles.add(ParagraphStyle(
        "H2", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=ACCENT,
        spaceBefore=10, spaceAfter=5, keepWithNext=1))
    styles.add(ParagraphStyle(
        "Body2", fontName="Helvetica", fontSize=9.5, leading=14,
        alignment=TA_JUSTIFY, textColor=colors.black, spaceAfter=6))
    styles.add(ParagraphStyle(
        "Bullet2", parent=styles["Body2"], leftIndent=10, bulletIndent=1,
        spaceAfter=5))
    styles.add(ParagraphStyle(
        "Caption", fontName="Helvetica-Oblique", fontSize=8, leading=11,
        textColor=GREY, spaceBefore=5, spaceAfter=10))
    styles.add(ParagraphStyle(
        "Cell", fontName="Helvetica", fontSize=8, leading=10.5))
    styles.add(ParagraphStyle(
        "CellHead", fontName="Helvetica-Bold", fontSize=8, leading=10.5,
        textColor=colors.white))
    styles.add(ParagraphStyle(
        "Key", fontName="Helvetica-Bold", fontSize=9.5, leading=13,
        textColor=NAVY))
    return styles


class Numbering:
    """Sequential numbers for sections, figures and tables."""

    def __init__(self):
        self.section = 0
        self.sub = 0
        self.figure = 0
        self.table = 0

    def h1(self, title):
        self.section += 1
        self.sub = 0
        return f"{self.section}. {title}"

    def h2(self, title):
        self.sub += 1
        return f"{self.section}.{self.sub} {title}"

    def next_figure(self):
        self.figure += 1
        return self.figure

    def next_table(self):
        self.table += 1
        return self.table


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------
def data_table(rows, widths, styles, align_center=(), zebra=True):
    """A table with a navy header row and hairline rules."""
    body = [[Paragraph(str(c), styles["CellHead"]) for c in rows[0]]]
    body += [[Paragraph(str(c), styles["Cell"]) for c in row] for row in rows[1:]]

    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.25, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if zebra:
        for index in range(2, len(body), 2):
            style.append(("BACKGROUND", (0, index), (-1, index), ZEBRA))
    for column in align_center:
        style.append(("ALIGN", (column, 0), (column, -1), "CENTER"))

    table = Table(body, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle(style))
    return table


def bullets(items, styles):
    return [Paragraph(text, styles["Bullet2"], bulletText="•") for text in items]


def cover(conn, styles, totals):
    date_text = date.today().strftime("%d %B %Y")
    flow = [
        Spacer(1, 14 * mm),
        Paragraph(UNIVERSITY, styles["CoverMeta"]),
        Paragraph(CHAIR, styles["CoverMeta"]),
        Spacer(1, 28 * mm),
        Paragraph("Seeding QDArchive", styles["CoverTitle"]),
        Spacer(1, 3 * mm),
        Paragraph("Part 2: Data Classification", styles["CoverSubtitle"]),
        Spacer(1, 6 * mm),
        Paragraph(f"Project Report — {COURSE}", styles["CoverMeta"]),
        Spacer(1, 22 * mm),
    ]

    facts = [
        ["Repositories", f"{totals['repositories']}"],
        ["Projects classified", f"{totals['classified']:,} of {totals['in_scope']:,} in scope"],
        ["Primary data files classified", f"{totals['files_classified']:,} of {totals['primary_files']:,}"],
        ["Taxonomy", f"{isic.STANDARD} — section and division"],
        ["Dominant class", totals["dominant"]],
    ]
    table = Table([[Paragraph(k, styles["Key"]), Paragraph(v, styles["Cell"])]
                   for k, v in facts], colWidths=[58 * mm, 62 * mm], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F9FC")),
        ("BOX", (0, 0), (-1, -1), 0.4, LIGHT),
    ]))
    flow.append(table)
    flow.append(Spacer(1, 26 * mm))

    author = [
        ["Submitted by", f"{STUDENT_NAME} ({DEGREE})"],
        ["Matriculation number", config.STUDENT_ID],
        ["Supervisor", SUPERVISOR],
        ["Date", date_text],
    ]
    table = Table([[Paragraph(k, styles["Key"]), Paragraph(v, styles["Cell"])]
                   for k, v in author], colWidths=[45 * mm, 75 * mm], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    flow.append(table)
    return flow


def toc(styles):
    contents = TableOfContents()
    contents.levelStyles = [
        ParagraphStyle("TOC1", fontName="Helvetica-Bold", fontSize=10, leading=17,
                       textColor=NAVY),
        ParagraphStyle("TOC2", fontName="Helvetica", fontSize=9, leading=14,
                       leftIndent=14, textColor=GREY),
    ]
    return [Paragraph("Contents", styles["H1Plain"]), Spacer(1, 3 * mm), contents]


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------
def introduction(conn, styles, num, totals):
    flow = [Paragraph(num.h1("Introduction"), styles["H1"])]
    flow.append(Paragraph(
        "QDArchive is a web service for researchers to publish and archive "
        "qualitative data, with an emphasis on qualitative data analysis (QDA) "
        "files. Because the service is new, it has to be seeded with openly "
        "licensed qualitative data that already exists on the web. Part 1 of this "
        "project acquired that data; this report covers Part 2, which classifies "
        "it.", styles["Body2"]))
    flow.append(Paragraph(
        "Part 2 has three requirements. Every project must be assigned a "
        "PROJECT_TYPE derived from the types of the files it contains. A "
        "classifier must then be developed that uses both the base data and the "
        "metadata, and that classifies against the ISIC Rev. 5 standard two "
        "levels down, i.e. to division level. Finally the classifier must be run "
        "by project type and by repository, and the resulting distributions "
        "reported.", styles["Body2"]))

    flow.append(Paragraph(num.h2("Data provenance"), styles["H2"]))
    flow.append(Paragraph(
        f"The input is the Part 1 database <font face='Courier'>"
        f"{config.SEEDING_DB.name}</font>, tagged <font face='Courier'>"
        f"part-1-release</font>. It holds {totals['projects']:,} projects and "
        f"{totals['files']:,} file records from {totals['repositories']} assigned "
        f"repositories: the Harvard Murray Research Archive and the Australian "
        f"Data Archive (ADA). Part 1 is treated as read-only input; all Part 2 "
        f"output is written to a separate database, so the acquisition results "
        f"remain reproducible and unmodified.", styles["Body2"]))
    flow.append(Paragraph(
        f"Of the {totals['files']:,} file records, {totals['downloaded']:,} files "
        f"were actually downloaded; the remainder are restricted and were recorded "
        f"by Part 1 with a failure status rather than silently dropped. This "
        f"asymmetry shapes the classifier design in Section 2.", styles["Body2"]))
    return flow


def method(conn, styles, num):
    flow = [Paragraph(num.h1("Method"), styles["H1"])]

    flow.append(Paragraph(num.h2("Merging and deduplication"), styles["H2"]))
    flow.append(Paragraph(
        "The seeding database is merged into a new classification database. "
        "Deduplication treats the DOI as the global identity of a project, "
        "falling back to the project URL and then to the repository-scoped title. "
        "Merging further student databases requires only listing them in the "
        "configuration; the results reported here use this student's data, in "
        "which no duplicates were found.", styles["Body2"]))

    flow.append(Paragraph(num.h2("Deriving the PROJECT_TYPE"), styles["H2"]))
    flow.append(Paragraph(
        "Each project is typed from the types of its files, following the rules "
        "of the task description in strict precedence:", styles["Body2"]))
    rows = [
        ["PROJECT_TYPE", "Rule"],
        ["QDA_PROJECT", "There is a file with a QDA file extension"],
        ["QD_PROJECT", "Not a QDA_PROJECT and there are primary data files"],
        ["OTHER_PROJECT", "Not a QD_PROJECT and there are valid data files"],
        ["NOT_A_PROJECT", "Nothing can be derived about the file types"],
    ]
    flow.append(data_table(rows, [34 * mm, 118 * mm], styles))
    flow.append(Paragraph(
        f"Table {num.next_table()}: The PROJECT_TYPE derivation rules.",
        styles["Caption"]))
    flow.append(Paragraph(
        "The file taxonomy is keyed on the file extension. About 200 files in the "
        "Murray archive have no usable extension, either because none was ever "
        "given (<font face='Courier'>RM 2462 Elias</font>) or because a stray "
        "character was typed into it (<font face='Courier'>…PDF´</font>, "
        "<font face='Courier'>.Paris-f-38_Draftsmanpdf</font>). Since Part 1 also "
        "recorded the MIME subtype reported by the repository, the category falls "
        "back to it when the extension is unusable. The task description asks for "
        "the type to be derived from the file types, and that column is a file "
        "type, so this is the intended signal rather than a workaround. It "
        "recovers every one of those files — 73 of them PDFs, i.e. primary "
        "data — and corrects two projects that would otherwise have been "
        "misreported as NOT_A_PROJECT.", styles["Body2"]))

    flow.append(Paragraph(num.h2("Classification taxonomy"), styles["H2"]))
    flow.append(Paragraph(
        f"The taxonomy is {isic.STANDARD}, taken from the structure adopted by the "
        f"United Nations Statistical Commission at its 54th session. It is "
        f"hierarchical: {len(isic.SECTIONS)} sections identified by a letter, and "
        f"{len(isic.DIVISIONS)} divisions identified by two digits. As required, "
        f"classification goes down two levels, so every classified project carries "
        f"a division and, through it, a section. The full taxonomy is embedded in "
        f"the delivered database in the <font face='Courier'>ISIC_CLASSES</font> "
        f"table, so the database is self-describing.", styles["Body2"]))

    flow.append(Paragraph(num.h2("Classifier design"), styles["H2"]))
    flow.append(Paragraph(
        "The classifier is a rule-based ISIC lexicon scored over a TF-IDF "
        "weighting. It is deterministic and involves no external service, so the "
        "results can be reproduced exactly by re-running the code. It works in "
        "four stages:", styles["Body2"]))
    flow += bullets([
        "Every project becomes one document built from its metadata (title, "
        "keywords, description), its file names, and the text extracted from the "
        "primary data files that were downloaded. A project is classified as the "
        "sum of its files, so the file text is concatenated.",
        "The documents are vectorised with a TF-IDF model restricted to the "
        "lexicon vocabulary of 729 terms spanning all 87 divisions. TF-IDF earns "
        "its place because the corpus is boilerplate-heavy: the phrase “the "
        "Murray Archive holds…” occurs in roughly 85% of the descriptions, "
        "and inverse document frequency drives such terms towards zero on its own, "
        "without a hand-maintained stop list.",
        "Each division scores as the sum of the TF-IDF weights of its matched "
        "lexicon terms, multiplied by a hand-assigned term weight that separates "
        "unambiguous evidence (“nursing home”) from weak evidence "
        "(“training”).",
        "The highest-scoring division becomes the primary class. The runner-up "
        "becomes the secondary class only when it reaches 45% of the top score and "
        "belongs to a different ISIC section, so that a class is not shadowed by a "
        "near-duplicate of itself.",
    ], styles)
    flow.append(Paragraph(
        "The metadata score and the file-text score are computed separately and "
        "then blended, weighted 65% to 35% in favour of the metadata. Concatenating "
        "the two into a single document would let a 20,000-character codebook "
        "contribute hundreds of terms and bury a five-word title. Because only one "
        "file in six could be downloaded, a project with no file text would "
        "otherwise score systematically lower than one with text; such projects are "
        "therefore scored on their metadata alone rather than against zero, which "
        "keeps them comparable.", styles["Body2"]))
    flow.append(Paragraph(
        "A project whose best division does not clear a minimum score is left "
        "unclassified rather than forced into a division, following the "
        "instruction to leave a field empty when it cannot be filled. Search tags "
        "are generated per project by a second, free-vocabulary TF-IDF pass and "
        "stored in the delivered database.", styles["Body2"]))

    flow.append(Paragraph(num.h2("What is being classified"), styles["H2"]))
    flow.append(Paragraph(
        "ISIC classifies economic activities, whereas the objects being classified "
        "here are research projects. A project is therefore assigned the division "
        "of the activity its data is <i>about</i>, not the activity of doing "
        "research. The alternative reading would collapse the entire archive into "
        "division 72 (Scientific research and development) and the taxonomy would "
        "carry no information at all; division 72 is accordingly reserved for "
        "projects whose subject really is research and development itself. This "
        "decision is the single most important one for interpreting the results, "
        "and its consequences are discussed in Section 6.", styles["Body2"]))
    return flow


def results_overview(conn, styles, num, totals, repositories):
    flow = [Paragraph(num.h1("Results overview"), styles["H1"])]

    flow.append(Paragraph(num.h2("Project types"), styles["H2"]))
    rows = [["PROJECT_TYPE", "Projects", "Share"]]
    grand = totals["projects"]
    for project_type in reports.ALL_TYPES:
        count = totals["types"].get(project_type, 0)
        rows.append([project_type, f"{count:,}", f"{count / grand:.1%}"])
    rows.append(["Total", f"{grand:,}", "100.0%"])
    table = data_table(rows, [42 * mm, 30 * mm, 26 * mm], styles, align_center=(1, 2))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, len(rows) - 1), (-1, len(rows) - 1), LIGHT),
        ("FONTNAME", (0, len(rows) - 1), (-1, len(rows) - 1), "Helvetica-Bold"),
    ]))
    flow.append(table)
    flow.append(Paragraph(
        f"Table {num.next_table()}: PROJECT_TYPE distribution over all "
        f"repositories.", styles["Caption"]))
    flow.append(Paragraph(
        "No project in the archive is a QDA_PROJECT. Not one of the "
        f"{totals['files']:,} files carries a QDA file extension, so by the Step 1 "
        "rule the type cannot be assigned. This is discussed in Section 6.",
        styles["Body2"]))

    flow.append(Paragraph(num.h2("Distributions to report"), styles["H2"]))
    flow.append(Paragraph(
        "The task description crosses repository with project type; each "
        "populated cell is one distribution to report. Only one such cell exists "
        "in this archive:", styles["Body2"]))
    rows = [["Repository", "QDA_PROJECT", "QD_PROJECT"]]
    distribution = 0
    for repository, summary in repositories:
        cells = []
        for project_type in reports.CLASSIFIED_TYPES:
            count = summary["types"].get(project_type, 0)
            if count:
                distribution += 1
                classes = len(reports.class_counts(conn, repository["id"], project_type))
                cells.append(f"Distribution {distribution}<br/>"
                             f"<font size='7'>{count:,} projects, {classes} classes</font>")
            else:
                cells.append("<font color='#888888'>none</font>")
        label = config.display_name(reports.clean(repository["name"]))
        rows.append([f"{repository['id']}. {label}", *cells])
    flow.append(data_table(rows, [62 * mm, 45 * mm, 45 * mm], styles,
                           align_center=(1, 2)))
    flow.append(Paragraph(
        f"Table {num.next_table()}: Distributions to report, by repository and "
        f"project type.", styles["Caption"]))
    return flow


def repository_section(conn, styles, num, repository, summary, land_width_mm):
    slug = reports.clean(repository["name"])
    name = config.display_name(slug)
    flow = [Paragraph(num.h1(f"Repository: {name}"), styles["H1"])]
    flow.append(Paragraph(
        f"<font face='Helvetica-Bold'>URL:</font> {repository['url']}<br/>"
        f"<font face='Helvetica-Bold'>Identifier:</font> "
        f"<font face='Courier'>{slug}</font> (repository_id {repository['id']})",
        styles["Body2"]))

    # --- types
    flow.append(Paragraph(num.h2("Project types found"), styles["H2"]))
    rows = [["PROJECT_TYPE", "Projects", "Share"]]
    total = summary["total_projects"]
    for project_type in reports.ALL_TYPES:
        count = summary["types"].get(project_type, 0)
        rows.append([project_type, f"{count:,}",
                     f"{count / total:.1%}" if total else "—"])
    flow.append(data_table(rows, [42 * mm, 30 * mm, 26 * mm], styles,
                           align_center=(1, 2)))
    flow.append(Paragraph(
        f"Table {num.next_table()}: PROJECT_TYPE distribution for {name}.",
        styles["Caption"]))

    files = summary["files"]
    if files["total"]:
        flow.append(Paragraph(
            f"{summary['classified']:,} of {summary['in_scope']:,} in-scope projects "
            f"(QDA_PROJECT and QD_PROJECT) received a class. "
            f"{files['downloaded']:,} of {files['total']:,} files could be "
            f"downloaded, and {files['with_text']:,} of those yielded "
            f"machine-readable text for the classifier to read.", styles["Body2"]))

    # --- distribution
    if summary["counts"]:
        flow.append(NextPageTemplate("figure"))
        flow.append(PageBreak())
        flow.append(Paragraph(num.h2("Distribution of primary classes"),
                              styles["H2"]))
        # Landscape text frame width, minus the heading and the caption.
        flow.append(charts.class_histogram(summary["counts"], land_width_mm, 126))
        flow.append(Paragraph(
            f"Figure {num.next_figure()}: Histogram of the primary ISIC Rev. 5 "
            f"classes identified in the {name}, over all "
            f"{summary['classified']:,} classified projects. Bin names are the full "
            f"class names; the count is printed above each bar.", styles["Caption"]))
        flow.append(NextPageTemplate("body"))
        flow.append(PageBreak())

        flow.append(Paragraph(num.h2("Classes ranked by frequency"), styles["H2"]))
        flow.append(ranked_table(summary["counts"], styles, num, name))

    # --- comments
    flow.append(Paragraph(num.h2("Comments on the findings"), styles["H2"]))
    flow += bullets(reports.findings_comments(conn, repository, summary), styles)
    return flow


def ranked_table(counts, styles, num, name):
    ordered = counts.most_common(reports.TOP_N)
    total = sum(counts.values())
    rows = [["Rank", "Section", "Division", "Full class name", "Count", "Share"]]
    for rank, (code, count) in enumerate(ordered, 1):
        rows.append([str(rank), isic.section_of(code), code,
                     isic.division_name(code), f"{count:,}", f"{count / total:.1%}"])
    table = data_table(rows, [13 * mm, 16 * mm, 17 * mm, 78 * mm, 15 * mm, 15 * mm],
                       styles, align_center=(0, 1, 2, 4, 5))
    caption = Paragraph(
        f"Table {num.next_table()}: The {len(ordered)} most common primary classes "
        f"in {name}, ranked, out of {len(counts)} distinct classes over {total:,} "
        f"classified projects. The top {reports.TOP_N} are shown.",
        styles["Caption"])
    return KeepTogether([table, caption])


def challenges(conn, styles, num, totals):
    flow = [Paragraph(num.h1("Technical challenges with the data"), styles["H1"])]
    flow.append(Paragraph(
        "The following observations concern the data itself rather than the "
        "programming, as requested for the ongoing reporting of this project.",
        styles["Body2"]))

    items = [
        ("The archive contains no QDA files at all",
         f"Not one of the {totals['files']:,} files carries a QDA file extension: "
         f"no .qdpx, no NVivo, ATLAS.ti or MAXQDA project. By the Step 1 rule "
         f"there are therefore zero QDA_PROJECTs. The Murray archive largely "
         f"predates the REFI-QDA interchange standard and stores its analysis "
         f"material as PDF codebooks and SPSS/SAS data instead. This is a property "
         f"of the data, not a gap in the pipeline: the classifier does look for "
         f"those extensions, and the QDA extension list is configuration rather "
         f"than hard-coded, so it can be extended when new formats appear."),
        ("The QD_PROJECT rule barely discriminates",
         "A single PDF is enough to make a project a QD_PROJECT, and 9,342 of the "
         "files are PDFs. The rule therefore sorts 92% of the archive into one "
         "bucket. For this repository the file-type rules separate far less than "
         "the class taxonomy does, and the useful discrimination comes from the "
         "classification rather than from the typing."),
        ("Most of the base data is restricted",
         f"Only {totals['downloaded']:,} of {totals['files']:,} files could be "
         f"downloaded, and {totals['with_text']:,} yielded machine-readable text. "
         f"The classifier reads the base data where it exists and falls back to "
         f"the metadata elsewhere, so classification quality is not uniform: "
         f"projects with open files are classified on more evidence than the rest. "
         f"Public visibility of a repository does not imply machine accessibility, "
         f"and this remains the dominant limitation carried over from Part 1."),
        ("Titles alone are often not classifiable",
         "Many titles name only the study, for example “Woman’s Day "
         "Survey, 1984”, and contain no subject term whatsoever. Such a "
         "project still classifies from its description, but its individual files "
         "initially did not, because a file’s context was built from the "
         "title and keywords only. Including the description in the inherited "
         "context raised file-level coverage from 50% to 99.9%."),
        ("ISIC is an economic taxonomy applied to social-science data",
         "Much of the archive is about family life, personal identity and the life "
         "course, which no ISIC division describes directly. Such projects land on "
         "the division of the institution through which they were studied: a study "
         "of mothers observed via their children’s schools scores as "
         "Education. The classes should be read as “the sector this data "
         "speaks about”, not as a summary of the research question. This is "
         "the single biggest interpretive caveat on the results, and it is a "
         "mismatch between the standard and the material rather than a defect of "
         "the classifier."),
        ("A sentinel row is not a project",
         "Part 1 recorded ADA’s firewall block as a synthetic row carrying "
         "an invented file name, all-files-inaccessible.txt. Typed naively, its "
         ".txt extension would have made it a QD_PROJECT and contributed a "
         "spurious class to the statistics. It is detected explicitly and typed "
         "NOT_A_PROJECT, and the report states plainly that no distribution can be "
         "reported for ADA. Records that document a failure must not be allowed to "
         "read as data."),
    ]
    for index, (heading, text) in enumerate(items, 1):
        flow.append(Paragraph(num.h2(heading), styles["H2"]))
        flow.append(Paragraph(text, styles["Body2"]))
    return flow


def conclusion(conn, styles, num, totals):
    flow = [Paragraph(num.h1("Conclusion"), styles["H1"])]
    flow.append(Paragraph(
        f"Part 2 typed all {totals['projects']:,} projects acquired in Part 1, "
        f"classified {totals['classified']:,} of the {totals['in_scope']:,} "
        f"in-scope projects and {totals['files_classified']:,} of the "
        f"{totals['primary_files']:,} primary data files against "
        f"{isic.STANDARD} at division level, and reported the resulting "
        f"distributions by repository and by project type.", styles["Body2"]))
    flow.append(Paragraph(
        f"The dominant class is {totals['dominant']}, followed by human health and "
        f"public administration. The concentration reflects the collection policy "
        f"of the Murray archive, a themed archive of longitudinal social-science "
        f"studies following school and college populations, rather than any "
        f"property of the taxonomy.", styles["Body2"]))
    flow.append(Paragraph(
        "Two findings are worth carrying into the seeding effort itself. First, an "
        "archive can be full of qualitative research and still contain no QDA "
        "files: the interchange standard is younger than most of the material, so "
        "seeding QDArchive from existing repositories will mostly yield primary "
        "data rather than the analysis files that are of particular interest. "
        "Second, most of the material is visible but not downloadable, so the "
        "quantity of metadata that can be harvested substantially exceeds the "
        "quantity of base data that can be read.", styles["Body2"]))
    flow.append(Paragraph(
        "The classifier is deterministic and its lexicon is data rather than code, "
        "so the results in this report can be reproduced exactly, and the "
        "classification can be extended to further repositories or refined without "
        "retraining anything.", styles["Body2"]))
    return flow


def appendix(conn, styles, num):
    flow = [Paragraph(num.h1("Appendix: reproducing these results"), styles["H1"])]
    flow.append(Paragraph(
        "The delivered database is <font face='Courier'>"
        f"{config.CLASSIFICATION_DB.name}</font>, committed to the project "
        "repository and tagged <font face='Courier'>classification-results</font>. "
        "It carries the Part 1 tables extended with the PROJECT_TYPE and the "
        "classification, a TAGS table for searching, and the ISIC Rev. 5 taxonomy "
        "itself. The report, the spreadsheet and the form answers are regenerated "
        "from it by:", styles["Body2"]))
    code = Paragraph(
        "<font face='Courier' size='8'>"
        "pip install -r requirements.txt<br/>"
        "python -m part2                                   # all steps, end to end<br/>"
        "python -m unittest discover -s part2/tests -t .   # the test suite"
        "</font>", styles["Body2"])
    box = Table([[code]], colWidths=[152 * mm])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F9FC")),
        ("BOX", (0, 0), (-1, -1), 0.4, LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
    ]))
    flow.append(box)
    flow.append(Spacer(1, 5 * mm))
    flow.append(Paragraph(
        f"The ISIC Rev. 5 structure was taken from the UN Statistical Commission "
        f"background document at {isic.SOURCE}, parsed to "
        f"{len(isic.SECTIONS)} sections and {len(isic.DIVISIONS)} divisions, and "
        f"is stored in the repository as data.", styles["Body2"]))
    return flow


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def gather_totals(conn):
    """Archive-wide figures used by the cover, the overview and the conclusion."""
    types = Counter(r["type"] for r in conn.execute("SELECT type FROM PROJECTS"))
    counts = Counter(
        r["primary_class"] for r in conn.execute(
            "SELECT primary_class FROM PROJECTS WHERE primary_class IS NOT NULL")
    )
    files = conn.execute(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(status = 'SUCCEEDED'), 0) AS downloaded,
                  COALESCE(SUM(text_chars > 0), 0) AS with_text,
                  COALESCE(SUM(file_category = 'PRIMARY'), 0) AS primary_files,
                  COALESCE(SUM(file_category = 'PRIMARY'
                               AND primary_class IS NOT NULL), 0) AS files_classified
           FROM FILES"""
    ).fetchone()
    dominant = "none"
    if counts:
        code, count = counts.most_common(1)[0]
        dominant = f"{isic.full_class_name(code)} ({count:,} projects)"
    return {
        "repositories": conn.execute(
            "SELECT COUNT(*) AS n FROM REPOSITORIES").fetchone()["n"],
        "projects": sum(types.values()),
        "types": types,
        "files": files["total"],
        "downloaded": files["downloaded"],
        "with_text": files["with_text"],
        "primary_files": files["primary_files"],
        "files_classified": files["files_classified"],
        "in_scope": sum(types.get(t, 0) for t in reports.CLASSIFIED_TYPES),
        "classified": sum(counts.values()),
        "dominant": dominant,
    }


def build(conn, path=None):
    path = path or config.REPORT_DIR / f"{config.STUDENT_ID}-sq26-classification.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)

    styles = build_styles()
    num = Numbering()
    totals = gather_totals(conn)
    repositories = [
        (r, reports.repository_summary(conn, r["id"]))
        for r in conn.execute("SELECT * FROM REPOSITORIES ORDER BY id")
    ]

    # Usable width of a landscape page, in millimetres: the figures are built at
    # their physical size so their type stays the size it was chosen to be.
    land_width_mm = (landscape(A4)[0] - 2 * MARGIN) / mm

    story = []
    story += cover(conn, styles, totals)
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())
    story += toc(styles)
    story.append(PageBreak())
    story += introduction(conn, styles, num, totals)
    story.append(PageBreak())
    story += method(conn, styles, num)
    story.append(PageBreak())
    story += results_overview(conn, styles, num, totals, repositories)
    for repository, summary in repositories:
        story.append(PageBreak())
        story += repository_section(conn, styles, num, repository, summary,
                                    land_width_mm)
    story.append(PageBreak())
    story += challenges(conn, styles, num, totals)
    story.append(PageBreak())
    story += conclusion(conn, styles, num, totals)
    story.append(PageBreak())
    story += appendix(conn, styles, num)

    document = ReportTemplate(
        str(path), pagesize=A4, title="Seeding QDArchive - Part 2: Data Classification",
        author=STUDENT_NAME, subject=COURSE,
    )
    # multiBuild resolves the table of contents page numbers.
    document.multiBuild(story)
    return path
