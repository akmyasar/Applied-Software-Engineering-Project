# Seeding QDArchive – Part 1: Data Acquisition

**Course:** Applied Software Engineering Project (10 ECTS)  
** FAU Erlangen-Nürnberg ** 
**Student:**  Akm Yasar  

---

# Project Overview

This project contributes to the **QDArchive initiative**, a web service designed to archive and publish qualitative research data.

The goal of **Part 1 (Data Acquisition)** is to collect qualitative research datasets from publicly available repositories and store them in a structured archive.

The system builds an automated **data acquisition pipeline** that:

- searches online repositories for qualitative datasets
- downloads research project files
- stores metadata in a structured SQLite database
- exports metadata to CSV format

The collected data can later be used for:

- qualitative data research
- retrieval-augmented generation (RAG)
- large language model (LLM) training datasets

---


# Pipeline Architecture

The acquisition pipeline follows this workflow:


Web Repositories
↓
Dataset Search
↓
Metadata Extraction
↓
File Download
↓
Local Storage
↓
SQLite Metadata Database
↓
CSV Export


---

# Data Sources

The pipeline collects qualitative research datasets from open repositories such as:

- Zenodo
- Qualitative Data Repositories
- Public research archives

Typical files include:

### Primary Data
- `.txt`
- `.pdf`
- `.docx`
- `.rtf`

Example: interview transcripts or research notes.

### QDA Files (Qualitative Data Analysis)

These are structured analysis files created by researchers.

Examples:

- `.qdpx` (REFI standard)
- NVivo files
- Atlas.ti files

---

# Metadata Database

All collected metadata is stored in a **SQLite database**.

Database location:

```
data/metadata/qdarchive.db
```

Metadata fields include:

| Field | Description |
|-----|-----|
| url | Source download link |
| timestamp | Download timestamp |
| local_dir | Local storage directory |
| filename | Downloaded file name |
| source | Repository source |
| license | Dataset license |
| uploader_name | Dataset uploader |
| uploader_email | Uploader contact |

---

# Output Files

After running the pipeline, the following outputs are generated:

### Downloaded datasets

```
data/raw_downloads/
```

### Metadata database

```
data/metadata/qdarchive.db
```

### CSV metadata export

```
data/metadata/metadata.csv
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/akmyasar/Applied-Software-Engineering-Project.git
cd Applied-Software-Engineering-Project

Create virtual environment:

python -m venv venv

Activate environment:

Windows
.\venv\Scripts\Activate.ps1
Linux / Mac
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt
