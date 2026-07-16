# Seeding QDArchive — Part 1: Data Acquisition

## Student Information
- **Student Name:** A K M Yasar
- **Matriculation ID:** 23025328
- **Course / Project:** Applied Software Engineering Project — Seeding QDArchive
- **Supervisor / Course Lead:** Prof. Dirk Riehle
- **University:** FAU Erlangen-Nürnberg
- **Department:** M.Sc in Data Science

---

## Project Overview

This repository contains the implementation for **Part 1: Data Acquisition** of the **Seeding QDArchive** project.

The goal of this part is to:

- identify qualitative research projects from the assigned repositories,
- download as many accessible project files as possible,
- preserve the original files without modification,
- store project metadata in a structured SQLite database,
- record both successful and failed download attempts,
- and export the collected metadata to CSV files.

The project is part of a broader effort to seed **QDArchive**, a repository intended for qualitative research data, especially projects containing:

- QDA project files,
- interview transcripts,
- codebooks,
- related documentation,
- and other files associated with qualitative research projects.

---

## Assigned Repositories

This implementation covers the following assigned repositories:

1. **ADA — Australian Data Archive**  
   Repository URL: `https://dataverse.ada.edu.au`

2. **Harvard Murray Research Archive**  
   Repository URL: `https://www.murray.harvard.edu`

---

## Part 1 Objectives

Part 1 focuses on **data acquisition**, not data cleaning or classification.

The required tasks are:

- repository-specific scraping / API access,
- downloading accessible project files,
- recording metadata in SQLite,
- storing project and file-level information,
- exporting metadata to CSV,
- and documenting **technical challenges related to the data**.

A key instruction for this part is:

> **Do not change the data during download.**  
> Data quality issues are preserved and can be handled later.

---

## Final Output

The required SQLite database file is:

- **`23025328-seeding.db`**

This file is stored in the **root of the repository**, as required.

---

## Project Structure

```text
.
├── 23025328-seeding.db
├── main.py
├── check_db.py
├── requirements.txt
├── README.md
├── data/
│   ├── ada/
│   └── harvard-murray-archive/
├── db/
│   ├── __init__.py
│   ├── database.py
│   └── schema.sql
├── export/
│   ├── repositories.csv
│   ├── projects.csv
│   ├── files.csv
│   ├── keywords.csv
│   ├── person_role.csv
│   └── licenses.csv
├── pipeline/
│   └── downloader.py
├── scrapers/
│   ├── __init__.py
│   ├── ada_scraper.py
│   └── murray_scraper.py
└── scripts/

Repository-Specific Implementation
1. Harvard Murray Research Archive

The Murray implementation is the main successful acquisition pipeline in this project.

It works by:

searching datasets through the Dataverse API,
retrieving dataset metadata,
collecting title, DOI, description, version, upload date, and related information,
extracting keywords, license values, and person-role metadata,
checking file availability,
downloading accessible files,
and recording download failures where files are restricted.

For publicly available files, the status is recorded as:

SUCCEEDED

For restricted or protected files, the status is recorded as:

FAILED_LOGIN_REQUIRED

This ensures that file-level accessibility is documented accurately rather than treating the entire project as either fully open or fully inaccessible.

2. ADA — Australian Data Archive

The ADA scraper was implemented with support for automated access, but in practice the repository blocked the requests with a web application firewall (WAF).

Instead of returning the expected JSON response, ADA returned HTML / blocked content, which made automated harvesting impossible in the same way as Murray.

To handle this properly, the implementation:

detects the WAF-blocked response,
records the repository-level acquisition failure,
and stores this situation transparently in the database.

The failure is documented using:

FAILED_SERVER_UNRESPONSIVE

This is important because the repository is visible to humans in a browser, but not reliably accessible to the scraper. From a technical perspective, this is a data-access problem, not simply a programming bug.

Technical Analysis
1. Repository Heterogeneity

A major challenge in this project is that the assigned repositories do not behave the same way, even though both are conceptually repositories for research data.

The Murray archive is accessible through a structured Dataverse interface and provides metadata and file access patterns that can be processed programmatically.

ADA, however, presents a different operational reality. Although it looks like a Dataverse-based repository, automated requests are blocked by WAF / anti-bot protection. This means that the same general logic cannot simply be reused for both repositories.

Technical implication:
A generic scraper is not sufficient. Repository-specific handling is required.

2. Public Visibility Does Not Mean Machine Accessibility

One of the most important observations in this project is that a repository can be publicly visible to a human user but still not be machine-accessible.

ADA demonstrates this clearly:

the website exists,
search pages can be opened manually,
but the scraper does not receive stable machine-readable JSON,
and the automated request is blocked before useful acquisition can happen.

Technical implication:
The acquisition pipeline must distinguish between:

repository availability to users,
and repository availability to automated systems.

This is why the ADA pipeline records FAILED_SERVER_UNRESPONSIVE rather than silently failing.

3. Fine-Grained File Accessibility

Within Murray, project-level metadata is often accessible even when some files are not.

This creates an important acquisition pattern:

the project itself is real and discoverable,
some files are downloadable,
some files are restricted,
and the system must record that mixed state correctly.

Instead of labeling the whole project as success or failure, the design records per-file download status.

Technical implication:
The FILES table is essential because accessibility varies at file level, not just project level.

This improves both transparency and later reproducibility.

4. Metadata Quality and Preservation

Metadata in real repositories is often incomplete, inconsistent, or ambiguous. Common examples include:

missing language values,
inconsistent person roles,
multiple license formats,
noisy keyword formatting,
and HTML inside descriptions.

For Part 1, the correct approach is not to over-clean the metadata during download.

Instead, the pipeline preserves the metadata as closely as possible to the source.

Technical implication:
Part 1 emphasizes acquisition fidelity and traceability rather than normalization.

This also aligns with the project rule that data quality issues should be handled later rather than during the initial download phase.

5. Schema Alignment and Phase Separation

Another technical issue in the project is that the schema and project requirements evolve across phases.

Part 1 is focused on acquisition. Later parts introduce richer interpretation and classification. During implementation, it was necessary to keep the database aligned with the required Part 1 schema and avoid mixing later-phase concepts into the base acquisition schema.

Technical implication:
Strict schema discipline is important.
Acquisition, classification, and data cleaning should remain logically separate.

This prevents mismatches between the code and the required database structure.

6. Folder-Based Archival Logic

The local storage design mirrors the structure of repository → project → version.

This is useful for several reasons:

it keeps downloads organized,
it makes manual inspection easier,
it preserves provenance,
and it allows the database fields such as download_repository_folder, download_project_folder, and download_version_folder to map directly to real locations on disk.

Technical implication:
The file system is not just a storage location; it is part of the acquisition trace.

This supports debugging, validation, and later downstream processing.

7. Why SQLite and CSV Are Both Useful

SQLite is the primary structured storage format for this project because it supports:

multiple related tables,
reproducible queries,
compact local storage,
and easy validation.

CSV export is also important because it allows:

quick manual inspection,
easy comparison across runs,
and simpler sharing / checking without requiring a database client.

Technical implication:
SQLite is the authoritative structured metadata store, while CSV acts as a lightweight inspection and reporting layer.

Technical Challenges (Data)

This section is required by the project and focuses on data challenges, not only coding issues.

ADA anti-bot / WAF protection

The ADA repository blocked automated requests and returned unusable content for the scraper. This prevented normal programmatic harvesting.

Restricted files in Murray

Some Murray projects contain both open and restricted files. As a result, not every listed file can be downloaded even when the project metadata is accessible.

Inconsistent metadata

Metadata fields such as keywords, licenses, language, and people are not fully standardized across repositories.

Mixed content types

Projects may contain a mixture of:

structured data files,
text documents,
codebooks,
scanned PDFs,
and other supplementary materials.

This makes broad but careful file handling necessary.

Phase-specific schema evolution

The project requirements evolve across phases, which creates a need for careful separation between acquisition logic and later enrichment logic.

Validation

The project includes check_db.py for quick validation.

This script is used to:

inspect the columns of PROJECTS and FILES,
view sample rows,
and confirm that the database has been populated correctly.

This is useful after each test run and before final submission.

---

# Seeding QDArchive — Part 2: Data Classification

Part 2 takes the database produced by Part 1, derives a `PROJECT_TYPE` for every
project, classifies the projects and their primary data files against the
**ISIC Rev. 5** taxonomy, and produces the required deliverables.

All Part 2 code lives in the `part2/` package and does not modify the Part 1
database: `23025328-seeding.db` is read-only input, and everything is written to
a new database.

## Running Part 2

```bash
pip install -r requirements.txt
python -m part2                      # runs all steps end to end
python -m unittest discover -s part2/tests -t .   # the test suite
```

Individual steps:

```bash
python -m part2.build_db             # Step 1: merge, dedup, PROJECT_TYPE
python -m part2.run_classification   # Steps 2 + 3: classify
python -m part2.reports              # Step 4: xlsx, pdf, form answers
```

## Step 1 — Merge, deduplicate, derive PROJECT_TYPE

`part2/build_db.py` merges the seeding database(s) into
`23025328-sq26-classification.db` and adds a `type` column of type
`PROJECT_TYPE` to `PROJECTS`.

Deduplication uses the DOI as the identity of a project, falling back to the
project URL and then the repository-scoped title. Additional student databases
can be merged by listing them in `config.EXTRA_SEEDING_DBS`; the current results
use this student's data only, where no duplicates were found.

The type is derived exactly as specified:

| Type | Rule |
|---|---|
| `QDA_PROJECT` | a file has a QDA file extension |
| `QD_PROJECT` | not a QDA_PROJECT and there are primary data files |
| `OTHER_PROJECT` | not a QD_PROJECT and there are valid data files |
| `NOT_A_PROJECT` | nothing can be derived about file types |

**Result:**

| Type | Count |
|---|---|
| QDA_PROJECT | 0 |
| QD_PROJECT | 355 |
| OTHER_PROJECT | 31 |
| NOT_A_PROJECT | 1 |

### File type fallback via MIME subtype

The file taxonomy lives in `part2/config.py` and is keyed on the file extension.
About 200 files in the Murray archive have no usable extension (`RM 2462 Elias`)
or a damaged one (`....PDF´`, `.Paris-f-38_Draftsmanpdf`).

Because Part 1 also recorded the MIME subtype reported by the repository, the
category falls back to it when the extension is unusable. The task description
says to derive the type from *the file types*, and `FILES.file_type` is that
column, so this is the intended signal rather than a workaround. It recovers all
~200 files (73 of them PDFs, i.e. primary data) and changes two projects from
`NOT_A_PROJECT` to their true type. Only the ADA sentinel row now remains
`UNKNOWN`.

## Step 2 — The classifier

`part2/classifier.py` implements a deterministic, rule-based classifier over a
TF-IDF weighting. No external service or API key is involved, so the professor
can reproduce the results by re-running the code.

1. Each project becomes a document built from its metadata (title, keywords,
   description), its file names, and the text extracted from the primary data
   files that were downloaded (`part2/textextract.py`).
2. Documents are vectorised with TF-IDF restricted to the lexicon vocabulary in
   `part2/lexicon.py` (729 terms across all 87 divisions). TF-IDF earns its
   place here because the corpus is boilerplate-heavy — *"The Murray Archive
   holds…"* appears in ~85% of the descriptions — and IDF suppresses such terms
   automatically instead of via a hand-maintained stop list.
3. Every ISIC division scores as the sum of the TF-IDF weights of its matched
   lexicon terms times a hand-assigned term weight.
4. The metadata score and the file-text score are computed **separately** and
   blended 65/35. Concatenating them would let a 20 000-character codebook bury
   a five-word title. Projects whose files could not be downloaded are scored on
   metadata alone rather than against zero, so they stay comparable.
5. The runner-up division is reported as `secondary_class` only when it reaches
   45% of the top score *and* belongs to a different ISIC section.

Projects that match no lexicon term are left unclassified rather than forced
into a division, following the instruction to leave a field empty when it cannot
be filled.

### What is being classified

ISIC classifies **economic activities**. A project is therefore assigned the
division of the activity its data is *about*, not the activity of doing
research. Otherwise every project in the archive would collapse into division 72
(Scientific research and development) and the taxonomy would carry no
information. Division 72 is reserved for projects whose subject really is
research and development itself.

## Step 3 — Running the classifier

`part2/run_classification.py` runs the classifier by project type
(`QDA_PROJECT` and `QD_PROJECT`) and by repository. For each project it
classifies the project itself, as the sum of its files, and every individual
primary data file. Search tags are generated per project by a second,
free-vocabulary TF-IDF pass and stored in the `TAGS` table.

**Result:** 352 of 355 in-scope projects and 9 939 of 9 946 primary data files
classified; 246 projects at `HIGH` confidence, 106 at `MEDIUM`.

| Division | Class | Projects |
|---|---|---|
| 85 | Education | 189 |
| 86 | Human health activities | 78 |
| 84 | Public administration and defence; compulsory social security | 40 |
| 88 | Social work activities without accommodation | 10 |
| 94 | Activities of membership organizations | 7 |

## Step 4 — Deliverables

| Deliverable | File | Step |
|---|---|---|
| Classification database | `23025328-sq26-classification.db` (tag `classification-results`) | 4a |
| Form answers per repository | `reports/form_answers.md` | 4b |
| Spreadsheet | `reports/23025328-sq26-classification.xlsx` | 4c |
| Report | `reports/23025328-sq26-classification.pdf` | 4d |

The PDF (`part2/report_pdf.py`, figures in `part2/charts.py`) is typeset with
ReportLab as a project report: cover page, generated table of contents, numbered
sections, running headers and page numbers, and numbered figures and tables. Its
structure is

1. Introduction — task and data provenance
2. Method — merging, typing, taxonomy, classifier design, scope
3. Results overview — project types and the repository × type distributions
4. / 5. One section per repository — types, histogram, ranked table, comments
6. Technical challenges with the data
7. Conclusion
8. Appendix — reproducing the results

Per repository it contains a histogram of the primary classes with the full
class name as the bin name and the count printed on top of each bar, a
rank-ordered top-20 table, and comments on the findings. Figures are drawn with
matplotlib, converted to SVG and embedded as **vector** (verified: zero raster
image objects in the PDF), so they stay sharp when zoomed. Histograms sit on
landscape pages because a bin labelled with a full ISIC class name needs the
width to stay legible.

## Technical challenges with the data (Part 2)

### 1. The archive contains no QDA files at all

Not one of the 11 979 files carries a QDA file extension — no `.qdpx`, `.nvp`,
`.atlproj` or MAXQDA project. By the Step 1 rule there are therefore **zero
QDA_PROJECTs**. The Murray archive largely predates the REFI-QDA standard and
stores its analysis material as PDF codebooks and SPSS/SAS data instead of as
QDA software projects. This is a property of the data, not a gap in the
pipeline: the classifier does look for those extensions.

### 2. The QD_PROJECT rule barely discriminates

A single PDF is enough to make a project a `QD_PROJECT`, and 9 342 of the files
are PDFs. The rule therefore sorts 92% of the repository into one bucket. The
file-type rules separate this archive far less than the class taxonomy does.

### 3. 81% of the files are restricted

Only 2 258 of 11 979 files could be downloaded, and 1 631 yielded
machine-readable text. The classifier reads the base data where it exists and
falls back to metadata elsewhere, so classification quality is **not uniform**:
projects with open files are classified on more evidence than the rest.

### 4. Titles alone are often not classifiable

Many titles name only the study (*"Woman's Day Survey, 1984"*) and contain no
subject term. Such a project still classifies from its description, but its
individual files initially did not, because a file's context was built from the
title and keywords only. Including the description in the file context raised
file coverage from 50% to 99.9%.

### 5. ISIC is an economic taxonomy applied to social-science data

Much of the archive is about family life, personal identity and the life course,
which no ISIC division describes directly. Such projects land on the division of
the institution through which they were studied — a study of mothers observed
via their children's schools scores as *Education*. The classes should be read
as *"the sector this data speaks about"*, not as a summary of the research
question. This is the single biggest interpretive caveat on the results.

### 6. The ADA sentinel row is not a project

Part 1 recorded ADA's WAF block as a synthetic row carrying an invented file
name, `all-files-inaccessible.txt`. Typed naively, its `.txt` extension would
have made it a `QD_PROJECT` and contributed a spurious class to the statistics.
It is detected via `config.PLACEHOLDER_DOIS` and typed `NOT_A_PROJECT`, and the
report says plainly that no distribution can be reported for ADA.

---

Conclusion

This project delivers a working Part 1 acquisition pipeline for QDArchive seeding.

The implementation successfully:

collects structured project metadata,
downloads accessible files from the Murray archive,
records restricted files accurately,
documents acquisition failure for ADA transparently,
exports metadata to CSV,
and stores all required outputs in a reproducible SQLite database.

Overall, the project demonstrates that real-world data acquisition is not only a scraping problem, but also a problem of repository heterogeneity, machine accessibility, metadata preservation, and traceable archival design.