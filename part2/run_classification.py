"""Part 2 Step 3: run the classifier over the archive.

    python -m part2.run_classification

The classifier is run by project type (QDA_PROJECT and QD_PROJECT), and for
each of those projects it classifies both the project itself, as the sum of its
files, and every individual primary data file. Results are written back into
config.CLASSIFICATION_DB.
"""
import re
import sqlite3

from part2 import config, isic, textextract
from part2.classifier import IsicClassifier, TagExtractor

# Project types the classifier is run for (Part 2 Step 3).
CLASSIFIED_TYPES = ("QDA_PROJECT", "QD_PROJECT")

# Caps keep one enormous project from dominating the corpus statistics.
MAX_PROJECT_TEXT = 60_000
MAX_FILE_TEXT = 20_000

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def tokenize_filename(name):
    """'01951Earls-PHDCN-CommunitySurvey-Codebook.pdf' -> readable words.

    File names in this archive pack several words together in CamelCase and
    around separators, so they carry real signal once split apart.
    """
    stem = (name or "").rsplit(".", 1)[0]
    stem = _CAMEL.sub(" ", stem)
    stem = re.sub(r"[^A-Za-z]+", " ", stem)
    words = [w for w in stem.split() if len(w) > 2]
    return " ".join(words)


def metadata_document(project, keywords, file_names):
    """Project metadata as one weighted string.

    Repetition is the weighting: the title and the researcher's own keywords
    describe the project directly, the description elaborates, and file names
    are the weakest of the metadata signals.
    """
    title = project["title"] or ""
    parts = [title] * 3
    parts += [" ".join(keywords)] * 3
    parts.append(project["description"] or "")
    parts.append(" ".join(tokenize_filename(n) for n in file_names))
    return " ".join(parts)


def load_projects(conn):
    projects = conn.execute(
        "SELECT * FROM PROJECTS WHERE type IN ({}) ORDER BY id".format(
            ", ".join("?" * len(CLASSIFIED_TYPES))
        ),
        CLASSIFIED_TYPES,
    ).fetchall()
    return projects


def run(verbose=True):
    conn = sqlite3.connect(config.CLASSIFICATION_DB)
    conn.row_factory = sqlite3.Row

    if verbose:
        print("Part 2 Step 3: classification")
        print("  extracting text from downloaded files ...")
    file_texts = textextract.extract_all(conn, verbose=verbose)

    projects = load_projects(conn)
    if verbose:
        print(f"  building documents for {len(projects)} projects "
              f"of type {'/'.join(CLASSIFIED_TYPES)} ...")

    metadata_docs, basedata_docs = [], []
    file_rows_by_project = {}

    for project in projects:
        files = conn.execute(
            "SELECT * FROM FILES WHERE project_id = ? ORDER BY id",
            (project["id"],),
        ).fetchall()
        file_rows_by_project[project["id"]] = files

        keywords = [
            r["keyword"] for r in conn.execute(
                "SELECT keyword FROM KEYWORDS WHERE project_id = ?",
                (project["id"],),
            )
        ]
        metadata_docs.append(
            metadata_document(project, keywords, [f["file_name"] for f in files])
        )

        # The project is classified as the sum of its files, so the base-data
        # document is the concatenated text of every file that was downloaded.
        chunks, total = [], 0
        for f in files:
            text = file_texts.get(f["id"])
            if not text:
                continue
            chunks.append(text)
            total += len(text)
            if total >= MAX_PROJECT_TEXT:
                break
        basedata_docs.append(" ".join(chunks)[:MAX_PROJECT_TEXT])

    # ---- fit on the whole corpus, then classify ---------------------------
    corpus = metadata_docs + [d for d in basedata_docs if d.strip()]
    if verbose:
        with_text = sum(1 for d in basedata_docs if d.strip())
        print(f"  fitting TF-IDF on {len(corpus)} documents "
              f"({with_text} projects have file text) ...")

    classifier = IsicClassifier().fit(corpus)
    scores = classifier.score_combined(metadata_docs, basedata_docs)
    results = classifier.interpret(scores)

    tagger = TagExtractor().fit(corpus)
    tags = tagger.tags_for(
        [f"{m} {b}" for m, b in zip(metadata_docs, basedata_docs)]
    )

    if verbose:
        print("  writing project classifications ...")

    conn.execute("DELETE FROM TAGS")
    for project, result, project_tags in zip(projects, results, tags):
        primary, secondary = result["primary_class"], result["secondary_class"]
        conn.execute(
            """UPDATE PROJECTS SET
                   primary_class = ?, primary_class_name = ?, primary_section = ?,
                   secondary_class = ?, secondary_class_name = ?, secondary_section = ?,
                   classification_score = ?, classification_confidence = ?
               WHERE id = ?""",
            (
                primary, isic.division_name(primary) if primary else None,
                isic.section_of(primary) if primary else None,
                secondary, isic.division_name(secondary) if secondary else None,
                isic.section_of(secondary) if secondary else None,
                round(result["score"], 6), result["confidence"], project["id"],
            ),
        )
        conn.executemany(
            "INSERT INTO TAGS (project_id, tag, weight) VALUES (?, ?, ?)",
            [(project["id"], tag, weight) for tag, weight in project_tags],
        )

    # ---- classify every primary data file ---------------------------------
    if verbose:
        print("  classifying primary data files ...")

    file_ids, file_meta_docs, file_text_docs = [], [], []
    for project in projects:
        keywords = [
            r["keyword"] for r in conn.execute(
                "SELECT keyword FROM KEYWORDS WHERE project_id = ?",
                (project["id"],),
            )
        ]
        # Context inherited from the owning project. The description has to be
        # part of it: many titles in this archive name only the study ("Woman's
        # Day Survey, 1984") and carry no subject term at all, so a file of such
        # a project would otherwise have nothing to be classified on even though
        # the project itself classifies fine from its description.
        title = project["title"] or ""
        context = " ".join([title, title, " ".join(keywords), " ".join(keywords),
                            project["description"] or ""])
        for f in file_rows_by_project[project["id"]]:
            if f["file_category"] != "PRIMARY":
                continue
            file_ids.append(f["id"])
            # A file's own name is the strongest evidence about it, so it
            # outweighs the inherited context. Five files in six could not be
            # downloaded, so for those the class is effectively inherited from
            # the project - the same fallback a human would use when the file
            # name is all there is.
            name_tokens = tokenize_filename(f["file_name"])
            file_meta_docs.append(" ".join([name_tokens] * 3 + [context]))
            file_text_docs.append((file_texts.get(f["id"]) or "")[:MAX_FILE_TEXT])

    if file_ids:
        file_scores = classifier.score_combined(file_meta_docs, file_text_docs)
        file_results = classifier.interpret(file_scores)
        conn.executemany(
            """UPDATE FILES SET
                   primary_class = ?, primary_class_name = ?,
                   secondary_class = ?, secondary_class_name = ?,
                   classification_score = ?
               WHERE id = ?""",
            [
                (
                    r["primary_class"],
                    isic.division_name(r["primary_class"]) if r["primary_class"] else None,
                    r["secondary_class"],
                    isic.division_name(r["secondary_class"]) if r["secondary_class"] else None,
                    round(r["score"], 6),
                    file_id,
                )
                for file_id, r in zip(file_ids, file_results)
            ],
        )

    conn.commit()

    if verbose:
        summarize(conn)
    conn.close()


def summarize(conn):
    print()
    print("  projects classified per type:")
    for row in conn.execute(
        """SELECT type,
                  COUNT(*) AS total,
                  SUM(primary_class IS NOT NULL) AS classified
           FROM PROJECTS GROUP BY type ORDER BY total DESC"""
    ):
        print(f"    {row['type']:<15}: {row['classified']}/{row['total']} classified")

    print("  primary data files classified:")
    row = conn.execute(
        """SELECT COUNT(*) AS total, SUM(primary_class IS NOT NULL) AS classified
           FROM FILES WHERE file_category = 'PRIMARY'"""
    ).fetchone()
    print(f"    {row['classified']}/{row['total']} classified")

    print("  confidence distribution (projects):")
    for row in conn.execute(
        """SELECT classification_confidence AS c, COUNT(*) AS n FROM PROJECTS
           WHERE type IN ('QDA_PROJECT', 'QD_PROJECT')
           GROUP BY c ORDER BY n DESC"""
    ):
        print(f"    {str(row['c']):<8}: {row['n']}")

    print("  top project classes:")
    for row in conn.execute(
        """SELECT primary_class AS c, COUNT(*) AS n FROM PROJECTS
           WHERE primary_class IS NOT NULL
           GROUP BY c ORDER BY n DESC LIMIT 12"""
    ):
        print(f"    {isic.full_class_name(row['c']):<55}: {row['n']}")


if __name__ == "__main__":
    run()
