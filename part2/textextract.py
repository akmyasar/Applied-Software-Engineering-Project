"""Extraction of text from the downloaded files (the "base data").

Part 2 Step 2 requires the classifier to use both the base data and the
metadata. Only the files the Part 1 pipeline could actually download are
available here; for everything else the classifier falls back to metadata and
file names alone.

Extracted text is cached under data/.textcache so that re-running the
classification does not re-parse several gigabytes of PDF. The cache lives
inside data/, which is git-ignored.
"""
import hashlib
import re
import zipfile
from pathlib import Path

from part2 import config

CACHE_DIR = config.DATA_DIR / ".textcache"

# Enough text to characterise a document; parsing whole 500-page codebooks
# would cost minutes per file and add little signal.
MAX_PAGES = 12
MAX_CHARS = 20_000

TEXT_EXTENSIONS = {"txt", "md", "csv", "tab", "tsv", "dat", "sps", "sas", "do",
                   "r", "dct", "codebook", "dic", "log", "out", "lst"}
HTML_EXTENSIONS = {"html", "htm", "shtml", "xml"}


def _cache_path(path):
    digest = hashlib.sha1(str(path).encode("utf-8", "replace")).hexdigest()
    return CACHE_DIR / digest[:2] / f"{digest}.txt"


def _clean(text):
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()[:MAX_CHARS]


def _from_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        reader = PdfReader(str(path))
        chunks = []
        for page in reader.pages[:MAX_PAGES]:
            try:
                chunks.append(page.extract_text() or "")
            except Exception:
                continue
            if sum(len(c) for c in chunks) >= MAX_CHARS:
                break
        return "".join(chunks)
    except Exception:
        return ""


def _from_docx(path):
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", "replace")
        xml = re.sub(r"</w:p>", "\n", xml)
        return re.sub(r"<[^>]+>", " ", xml)
    except Exception:
        return ""


def _from_html(path):
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"<[^>]+>", " ", raw)


def _from_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")[: MAX_CHARS * 2]
    except Exception:
        return ""


def _from_doc(path):
    """Legacy binary .doc / .wpd: recover the readable ASCII runs.

    There is no pure-python reader for these formats, but the word list is all
    the classifier needs, so printable runs are good enough. Only runs of four
    or more characters are kept to drop the binary noise.
    """
    try:
        blob = path.read_bytes()[:2_000_000]
    except Exception:
        return ""
    words = re.findall(rb"[\x20-\x7e]{4,}", blob)
    text = b" ".join(words).decode("ascii", "replace")
    # These formats interleave metadata; keep it only if it looks like prose.
    return text if len(text) > 200 else ""


def extract(path, extension=None):
    """Best-effort text of one file; '' when the type is not extractable."""
    path = Path(path)
    if not path.is_file():
        return ""

    ext = (extension or config.normalize_extension(path.name)).lower()

    cache = _cache_path(path)
    if cache.is_file():
        try:
            return cache.read_text(encoding="utf-8")
        except Exception:
            pass

    if ext == "pdf":
        text = _from_pdf(path)
    elif ext in {"docx", "odt", "epub"}:
        text = _from_docx(path)
    elif ext in HTML_EXTENSIONS:
        text = _from_html(path)
    elif ext in TEXT_EXTENSIONS:
        text = _from_text(path)
    elif ext in {"doc", "wpd", "wps", "rtf"}:
        text = _from_doc(path)
    else:
        text = ""

    text = _clean(text)

    cache.parent.mkdir(parents=True, exist_ok=True)
    try:
        cache.write_text(text, encoding="utf-8")
    except Exception:
        pass
    return text


def extract_all(conn, verbose=True):
    """Extract text for every downloaded file and record its length.

    Returns {file_id: text} for the files that yielded any text.
    """
    rows = conn.execute(
        "SELECT id, file_name, file_extension, local_path FROM FILES "
        "WHERE local_path IS NOT NULL"
    ).fetchall()

    texts = {}
    updates = []
    for index, row in enumerate(rows, 1):
        text = extract(config.ROOT / row["local_path"], row["file_extension"])
        if text:
            texts[row["id"]] = text
        updates.append((len(text), row["id"]))
        if verbose and index % 250 == 0:
            print(f"    extracted {index}/{len(rows)} files "
                  f"({len(texts)} with text)")

    conn.executemany("UPDATE FILES SET text_chars = ? WHERE id = ?", updates)
    conn.commit()

    if verbose:
        print(f"    extracted {len(rows)}/{len(rows)} files "
              f"({len(texts)} with text)")
    return texts
