"""Part 2 Step 2: the ISIC Rev. 5 classifier.

Design
------
The classifier is a rule-based lexicon scorer on top of a TF-IDF weighting.

1. Every project becomes one document built from its metadata (title, keywords,
   description), its file names, and the text extracted from the primary data
   files that were actually downloaded. Fields are weighted by repetition: a
   term in the title counts more than the same term in a codebook.

2. The documents are vectorised with a TF-IDF model restricted to the lexicon
   vocabulary (part2/lexicon.py). TF-IDF matters here because the corpus is
   boilerplate-heavy: "the Murray Archive holds..." occurs in ~85% of the
   descriptions, and IDF drives such terms towards zero on its own, without a
   hand-maintained stop list.

3. Each division scores as the sum of the TF-IDF weights of its lexicon terms,
   multiplied by the hand-assigned term weight. This is one sparse matrix
   product: SCORES = TFIDF x WEIGHTS.

4. The highest-scoring division becomes primary_class. The runner-up becomes
   secondary_class when it is close enough to be a genuine second reading of
   the project (>= SECONDARY_RATIO of the top score) and belongs to a different
   ISIC section, so that "85 Education" is not shadowed by a near-duplicate.

The model is deterministic: the same database always produces the same
classification, and no external service is involved.
"""
import re

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from part2 import isic
from part2.lexicon import LEXICON

# A project is left unclassified rather than forced into a division when even
# its best division barely registers. "If you can't fill a particular field,
# leave it empty."
MIN_SCORE = 0.02
# Runner-up must reach this share of the top score to be reported.
SECONDARY_RATIO = 0.45

# Relative influence of the metadata and of the text extracted from the files.
W_METADATA = 0.65
W_BASEDATA = 0.35

TOKEN_PATTERN = r"(?u)\b\w+\b"
MAX_NGRAM = 4


def normalize(text):
    """Lower-case, strip punctuation, collapse whitespace.

    Applied identically to documents and to lexicon terms so that phrases like
    "women's liberation movement" survive on both sides.

    Apostrophes are deleted rather than turned into a space, so that possessives
    stay a single token: splitting them would push "women's liberation movement"
    to four tokens and any four-word phrase containing one past MAX_NGRAM, where
    it could never be matched again.
    """
    text = (text or "").lower()
    text = re.sub(r"['‘’ʼ`]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_vocabulary():
    """{normalized term: column index} plus the (terms x divisions) weights."""
    normalized = {}
    for division, terms in LEXICON.items():
        for term, weight in terms.items():
            key = normalize(term)
            if key:
                normalized.setdefault(key, []).append((division, float(weight)))

    vocabulary = {term: i for i, term in enumerate(sorted(normalized))}
    divisions = sorted(LEXICON)
    division_index = {d: i for i, d in enumerate(divisions)}

    rows, cols, values = [], [], []
    for term, pairs in normalized.items():
        for division, weight in pairs:
            rows.append(vocabulary[term])
            cols.append(division_index[division])
            values.append(weight)

    weights = csr_matrix(
        (values, (rows, cols)), shape=(len(vocabulary), len(divisions))
    )
    return vocabulary, divisions, weights


class IsicClassifier:
    def __init__(self):
        self.vocabulary, self.divisions, self.weights = build_vocabulary()
        self.vectorizer = TfidfVectorizer(
            vocabulary=self.vocabulary,
            ngram_range=(1, MAX_NGRAM),
            token_pattern=TOKEN_PATTERN,
            lowercase=True,
            sublinear_tf=True,   # a term occurring 50x is not 50x as indicative
            norm="l2",
        )
        self._fitted = False

    def fit(self, documents):
        """Learn the IDF weights from the whole corpus."""
        self.vectorizer.fit([normalize(d) for d in documents])
        self._fitted = True
        return self

    def score(self, documents):
        """(n_documents x n_divisions) dense score matrix."""
        if not self._fitted:
            raise RuntimeError("fit() must be called before score()")
        tfidf = self.vectorizer.transform([normalize(d) for d in documents])
        return np.asarray((tfidf @ self.weights).todense())

    def score_combined(self, metadata_docs, basedata_docs):
        """Blend the metadata score with the base-data (file text) score.

        The two are scored separately instead of being concatenated into one
        string: a 20 000-character codebook would otherwise contribute hundreds
        of terms and bury a five-word title. The metadata carries more weight
        because the researcher wrote it to describe the project, while the base
        data is corroborating evidence.

        Only ~1 file in 6 could be downloaded, so a project without any file
        text would otherwise score systematically lower than one with text and
        risk falling under MIN_SCORE. The divisor therefore drops the base-data
        term for those projects instead of scoring them against zero.
        """
        meta_scores = self.score(metadata_docs)
        text_scores = self.score(basedata_docs)
        has_text = np.array(
            [1.0 if (d or "").strip() else 0.0 for d in basedata_docs]
        ).reshape(-1, 1)

        numerator = W_METADATA * meta_scores + W_BASEDATA * text_scores * has_text
        denominator = W_METADATA + W_BASEDATA * has_text
        return numerator / denominator

    def classify(self, documents):
        """One classification dict per document."""
        return self.interpret(self.score(documents))

    def interpret(self, scores):
        """Turn a score matrix into one classification dict per row."""
        return [self._interpret(row) for row in scores]

    def _interpret(self, row):
        order = np.argsort(row)[::-1]
        best = order[0]
        best_score = float(row[best])

        if best_score < MIN_SCORE:
            return {
                "primary_class": None, "secondary_class": None,
                "score": best_score, "confidence": "NONE",
            }

        primary = self.divisions[best]
        secondary = None
        for index in order[1:]:
            candidate_score = float(row[index])
            if candidate_score <= 0 or candidate_score < SECONDARY_RATIO * best_score:
                break
            candidate = self.divisions[index]
            if isic.section_of(candidate) != isic.section_of(primary):
                secondary = candidate
                break

        runner_up = float(row[order[1]]) if len(order) > 1 else 0.0
        margin = (best_score - runner_up) / best_score if best_score else 0.0
        if best_score >= 0.25 and margin >= 0.4:
            confidence = "HIGH"
        elif best_score >= 0.08:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return {
            "primary_class": primary,
            "secondary_class": secondary,
            "score": best_score,
            "confidence": confidence,
        }


class TagExtractor:
    """Free-vocabulary TF-IDF over the corpus, for search tags.

    Part 2 Step 2: "Also consider creating tags for searching." Unlike the
    classifier this uses no fixed vocabulary, so it surfaces whatever actually
    distinguishes a project from the rest of the archive.
    """

    def __init__(self, max_tags=12):
        self.max_tags = max_tags
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            token_pattern=TOKEN_PATTERN,
            stop_words="english",
            min_df=2,
            max_df=0.4,      # drops the archive-wide boilerplate
            sublinear_tf=True,
            max_features=60_000,
        )
        self.terms = None

    def fit(self, documents):
        self.vectorizer.fit([normalize(d) for d in documents])
        self.terms = np.array(self.vectorizer.get_feature_names_out())
        return self

    def tags_for(self, documents):
        matrix = self.vectorizer.transform([normalize(d) for d in documents])
        result = []
        for i in range(matrix.shape[0]):
            row = matrix.getrow(i)
            if row.nnz == 0:
                result.append([])
                continue
            order = np.argsort(row.data)[::-1][: self.max_tags]
            result.append([
                (self.terms[row.indices[j]], round(float(row.data[j]), 4))
                for j in order
            ])
        return result
