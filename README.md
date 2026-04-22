@'
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