"""ISIC Rev. 5 taxonomy (sections and divisions).

The project classifies down two levels, i.e. section (letter) and division
(two digits), as required by Part 2 Step 2.
"""
import json
from pathlib import Path

ISIC_PATH = Path(__file__).resolve().parent / "isic_rev5.json"

_data = json.loads(ISIC_PATH.read_text(encoding="utf-8"))

STANDARD = _data["standard"]
SOURCE = _data["source"]

# {"A": "Agriculture, forestry and fishing", ...}
SECTIONS = _data["sections"]

# {"01": {"section": "A", "name": "Crop and animal production, ..."}, ...}
DIVISIONS = {
    d["division"]: {"section": d["section"], "name": d["name"]}
    for d in _data["divisions"]
}

DIVISION_CODES = sorted(DIVISIONS)


def division_name(code):
    """Full division name, e.g. '85' -> 'Education'."""
    entry = DIVISIONS.get(code)
    return entry["name"] if entry else ""


def section_of(code):
    """Section letter owning a division, e.g. '85' -> 'Q'."""
    entry = DIVISIONS.get(code)
    return entry["section"] if entry else ""


def section_name(letter):
    return SECTIONS.get(letter, "")


def full_class_name(code):
    """Bin name used in the report histograms, e.g. '85 Education'."""
    if not code:
        return "UNCLASSIFIED"
    return f"{code} {division_name(code)}"


def label(code):
    """Fully qualified label, e.g. 'Q.85 Education'."""
    if not code:
        return "UNCLASSIFIED"
    return f"{section_of(code)}.{code} {division_name(code)}"
