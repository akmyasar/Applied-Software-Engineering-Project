"""File-type taxonomy and paths used by Part 2.

The extension sets below drive the PROJECT_TYPE derivation of Part 2 Step 1.
They extend the sets already used in Part 1 (db/database.py) and are kept here
so they can be edited in one place when new file types are discovered.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STUDENT_ID = "23025328"
SEEDING_DB = ROOT / f"{STUDENT_ID}-seeding.db"
CLASSIFICATION_DB = ROOT / f"{STUDENT_ID}-sq26-classification.db"
DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"

# Extra seeding databases to merge in (Part 2 Step 1). Empty = own data only.
EXTRA_SEEDING_DBS = []

# Presentation names for the repositories. REPOSITORIES.name holds the folder
# slug the Part 1 pipeline harvested into, which is the identifier everywhere in
# the data; these are only for the prose of the report, and anything not listed
# falls back to the slug itself.
REPOSITORY_DISPLAY_NAMES = {
    "harvard-murray-archive": "Harvard Murray Research Archive",
    "ada": "Australian Data Archive (ADA)",
}


def display_name(name):
    return REPOSITORY_DISPLAY_NAMES.get((name or "").strip(), name)


# Sentinel records written by the Part 1 scrapers to document a repository that
# could not be harvested at all. They carry an invented file name and therefore
# must not be typed from their file extensions: they are NOT_A_PROJECT.
PLACEHOLDER_DOIS = {"ADA-WAF-BLOCKED"}

# ---------------------------------------------------------------------------
# Analysis data files (QDA files)
#
# Structured data a researcher creates when interpreting primary data.
# qdpx is the REFI-QDA interchange format (https://www.qdasoftware.org/).
# ---------------------------------------------------------------------------
QDA_EXTENSIONS = {
    # REFI-QDA exchange standard
    "qdpx", "qdc", "qde",
    # NVivo
    "nvp", "nvpx", "nvivo", "nvp10", "nvpx12",
    # ATLAS.ti
    "atlproj", "hpr5", "hpr6", "hpr7", "hpr8", "atlas22", "atlproj23",
    # MAXQDA
    "mx3", "mx4", "mx5", "mx11", "mx12", "mx16", "mx18", "mx20", "mx22", "mx24",
    "mx2018", "mx2020", "mx2022", "maxqda", "maxqdaproject", "mex",
    # QDA Miner / Provalis
    "ppj", "wpj",
    # Dedoose / Transana / Quirkos / f4analyse / Taguette / Transcriva
    "dedoose", "tra", "transana", "qrk", "qrkc", "f4a", "taguette",
    # Other legacy / niche QDA tools
    "qda", "qdp", "nva", "cat", "hyperresearch", "hs2", "qsr",
}

# ---------------------------------------------------------------------------
# Primary data files
#
# Any form of qualitative data: interview transcripts, research articles, ...
# ---------------------------------------------------------------------------
PRIMARY_DATA_EXTENSIONS = {
    # documents / transcripts / articles
    "txt", "pdf", "rtf", "doc", "docx", "odt", "md", "wpd", "wps", "tex",
    "html", "htm", "xml", "epub", "pages",
    # audio / video interviews
    "mp3", "wav", "m4a", "aac", "flac", "wma", "aiff", "ogg",
    "mp4", "mov", "avi", "mkv", "wmv", "mpeg", "mpg", "m4v",
    # images of primary material (field notes, scans)
    "jpg", "jpeg", "png", "tif", "tiff", "gif", "bmp",
}

# ---------------------------------------------------------------------------
# Other valid data files
#
# Not analysis and not primary data, but still something the researcher
# considers part of the project (Part 1 "Additional Data Files").
# ---------------------------------------------------------------------------
OTHER_DATA_EXTENSIONS = {
    # tabular / statistical data
    "csv", "tab", "tsv", "xls", "xlsx", "xlsm", "ods", "dat", "json", "wk1",
    "sav", "por", "zsav", "dta", "sas7bdat", "sd2", "sd7", "xpt", "rdata",
    "rds", "mdb", "accdb", "db", "sqlite", "parquet", "codebook", "dic",
    # syntax / code
    "sps", "sas", "do", "r", "py", "dct", "prg", "m",
    # archives / containers
    "zip", "tar", "gz", "tgz", "7z", "rar", "bz2", "warc",
    # misc project material
    "log", "out", "lst", "ini", "mxd", "shp", "ppt", "pptx", "test",
}


# ---------------------------------------------------------------------------
# MIME subtype fallback
#
# Part 1 stored the MIME subtype reported by the repository in FILES.file_type
# (e.g. 'pdf', 'x-spss-por', 'plain; charset=US-ASCII'). Roughly 200 files in
# the Murray archive carry no usable extension at all ('RM 2462 Elias') or a
# corrupted one ('...PDF�'), but their MIME subtype is intact. Deriving the
# category from it recovers those files instead of discarding them as UNKNOWN.
# ---------------------------------------------------------------------------
MIME_PRIMARY = {
    "pdf", "plain", "txt", "text", "rtf", "msword", "html", "xhtml+xml", "xml",
    "vnd.openxmlformats-officedocument.wordprocessingml.document",
    "vnd.oasis.opendocument.text", "epub+zip",
    "mpeg", "mp3", "mp4", "wav", "x-wav", "aac", "ogg", "quicktime",
    "x-msvideo", "jpeg", "jpg", "png", "tiff", "gif",
}

MIME_OTHER = {
    "tab-separated-values", "csv", "comma-separated-values",
    "vnd.ms-excel", "vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "vnd.oasis.opendocument.spreadsheet",
    "x-spss-por", "x-spss-sav", "x-spss-syntax", "x-sas-system", "x-sas-syntax",
    "x-stata-syntax", "x-stata-data", "x-rlang-transport", "x-r-syntax",
    "msaccess", "x-msaccess", "json", "warc",
    "zip", "x-zip-compressed", "x-tar", "x-gzip", "gzip", "x-7z-compressed",
    "x-rar-compressed", "x-bzip2",
    # Generic binary: the repository does not say what it is, but it is still a
    # real file the researcher published, i.e. a valid data file.
    "octet-stream",
}


def normalize_mime(file_type):
    """'plain; charset=US-ASCII' -> 'plain'; also drops any 'application/' prefix."""
    value = (file_type or "").strip().lower()
    if not value:
        return ""
    value = value.split(";", 1)[0].strip()
    if "/" in value:
        value = value.split("/", 1)[-1].strip()
    return value


def mime_category(file_type):
    """One of PRIMARY, OTHER, UNKNOWN, derived from the MIME subtype."""
    mime = normalize_mime(file_type)
    if not mime:
        return "UNKNOWN"
    if mime in MIME_PRIMARY:
        return "PRIMARY"
    if mime in MIME_OTHER:
        return "OTHER"
    return "UNKNOWN"


def normalize_extension(file_name):
    """Lower-case extension without the dot; '' when there is none.

    Part 1 stored some names with trailing spaces ('report.pdf '), so the name
    is stripped before the extension is taken.
    """
    name = (file_name or "").strip()
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[-1].strip().lower()


def extension_category(ext):
    """One of QDA, PRIMARY, OTHER, UNKNOWN, derived from the extension alone."""
    if not ext:
        return "UNKNOWN"
    if ext in QDA_EXTENSIONS:
        return "QDA"
    if ext in PRIMARY_DATA_EXTENSIONS:
        return "PRIMARY"
    if ext in OTHER_DATA_EXTENSIONS:
        return "OTHER"
    return "UNKNOWN"


def file_category(file_name, file_type=None):
    """Category of a file from its extension, falling back to its MIME subtype.

    The extension wins because it is what the QDA/primary/other taxonomy is
    defined on, and no MIME subtype identifies a QDA file (repositories serve
    .qdpx as application/octet-stream or application/zip).
    """
    category = extension_category(normalize_extension(file_name))
    if category != "UNKNOWN":
        return category
    return mime_category(file_type)
