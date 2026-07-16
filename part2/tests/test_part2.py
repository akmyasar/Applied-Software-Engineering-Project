"""Tests for the Part 2 classification logic.

    python -m unittest discover -s part2/tests -v
"""
import unittest

from part2 import config, isic
from part2.build_db import derive_project_type
from part2.classifier import MAX_NGRAM, IsicClassifier, normalize
from part2.lexicon import LEXICON
from part2.run_classification import tokenize_filename


class TestIsicTaxonomy(unittest.TestCase):
    def test_has_full_rev5_structure(self):
        self.assertEqual(len(isic.SECTIONS), 22)
        self.assertEqual(len(isic.DIVISIONS), 87)

    def test_two_levels_are_linked(self):
        for code, entry in isic.DIVISIONS.items():
            self.assertIn(entry["section"], isic.SECTIONS,
                          f"division {code} points at an unknown section")

    def test_known_divisions(self):
        self.assertEqual(isic.division_name("85"), "Education")
        self.assertEqual(isic.section_of("85"), "Q")
        self.assertEqual(isic.full_class_name("85"), "85 Education")
        self.assertEqual(isic.label("85"), "Q.85 Education")

    def test_unknown_division_is_empty_not_an_error(self):
        self.assertEqual(isic.division_name("00"), "")
        self.assertEqual(isic.full_class_name(None), "UNCLASSIFIED")


class TestFileCategories(unittest.TestCase):
    def test_extension_is_normalized(self):
        self.assertEqual(config.normalize_extension("Report.PDF"), "pdf")
        # Part 1 preserved names verbatim, including trailing blanks.
        self.assertEqual(config.normalize_extension("Report.pdf "), "pdf")
        self.assertEqual(config.normalize_extension("no_extension"), "")

    def test_categories(self):
        self.assertEqual(config.extension_category("qdpx"), "QDA")
        self.assertEqual(config.extension_category("pdf"), "PRIMARY")
        self.assertEqual(config.extension_category("sav"), "OTHER")
        self.assertEqual(config.extension_category("wat"), "UNKNOWN")

    def test_mime_is_normalized(self):
        self.assertEqual(config.normalize_mime("plain; charset=US-ASCII"), "plain")
        self.assertEqual(config.normalize_mime("application/pdf"), "pdf")

    def test_mime_recovers_unusable_extensions(self):
        # Real rows from the Murray archive: no extension at all, an extension
        # with a stray acute accent, and a word glued to the extension.
        self.assertEqual(config.file_category("RM 2462 Elias", "pdf"), "PRIMARY")
        self.assertEqual(config.file_category("Subjects_1355-1369.PDF´", "pdf"),
                         "PRIMARY")
        self.assertEqual(config.file_category(".Paris-f-38_Draftsmanpdf", "pdf"),
                         "PRIMARY")
        self.assertEqual(
            config.file_category("Holtzman-Austin-1990", "x-spss-por"), "OTHER")

    def test_unusable_extension_and_unusable_mime_stays_unknown(self):
        self.assertEqual(config.file_category("mystery.xyz", "unheard-of"), "UNKNOWN")

    def test_extension_wins_over_mime(self):
        # A .qdpx served as a generic zip must still be recognised as QDA.
        self.assertEqual(config.file_category("project.qdpx", "zip"), "QDA")


class TestProjectType(unittest.TestCase):
    """The rules given in Part 2 Step 1 Continued."""

    def test_qda_project(self):
        self.assertEqual(derive_project_type({"QDA", "PRIMARY", "OTHER"}), "QDA_PROJECT")

    def test_qd_project_when_no_qda_file(self):
        self.assertEqual(derive_project_type({"PRIMARY", "OTHER"}), "QD_PROJECT")

    def test_other_project_when_no_primary_data(self):
        self.assertEqual(derive_project_type({"OTHER"}), "OTHER_PROJECT")

    def test_not_a_project_when_nothing_derivable(self):
        self.assertEqual(derive_project_type({"UNKNOWN"}), "NOT_A_PROJECT")
        self.assertEqual(derive_project_type(set()), "NOT_A_PROJECT")

    def test_precedence_is_strict(self):
        self.assertEqual(derive_project_type({"QDA"}), "QDA_PROJECT")
        self.assertEqual(derive_project_type({"PRIMARY"}), "QD_PROJECT")

    def test_placeholder_is_never_a_project(self):
        # The ADA sentinel row carries an invented 'all-files-inaccessible.txt'.
        self.assertEqual(
            derive_project_type({"PRIMARY"}, is_placeholder=True), "NOT_A_PROJECT")


class TestNormalization(unittest.TestCase):
    def test_punctuation_is_folded(self):
        self.assertEqual(normalize("Women's Liberation Movement!"),
                         "womens liberation movement")

    def test_filename_is_split_into_words(self):
        self.assertEqual(
            tokenize_filename("01951Earls-PHDCN-CommunitySurvey-Codebook.pdf"),
            "Earls PHDCN Community Survey Codebook",
        )

    def test_filename_without_extension(self):
        self.assertEqual(tokenize_filename("StudyDocumentation"), "Study Documentation")


class TestLexiconIsReachable(unittest.TestCase):
    """Every lexicon term must be matchable by the vectoriser.

    A term longer than MAX_NGRAM tokens once normalized can never appear in the
    document n-grams, so it would sit in the vocabulary scoring nothing.
    """

    def test_no_term_exceeds_the_ngram_window(self):
        for division, terms in LEXICON.items():
            for term in terms:
                length = len(normalize(term).split())
                self.assertLessEqual(
                    length, MAX_NGRAM,
                    f"division {division}: {term!r} normalizes to {length} tokens, "
                    f"above MAX_NGRAM={MAX_NGRAM}, so it can never match",
                )

    def test_no_term_normalizes_to_nothing(self):
        for division, terms in LEXICON.items():
            for term in terms:
                self.assertTrue(normalize(term),
                                f"division {division}: {term!r} normalizes to nothing")

    def test_divisions_are_valid_isic_codes(self):
        for division in LEXICON:
            self.assertIn(division, isic.DIVISIONS,
                          f"{division} is not an ISIC Rev. 5 division")


class TestClassifier(unittest.TestCase):
    """The classifier is trained per corpus, so these use a small fixture."""

    @classmethod
    def setUpClass(cls):
        cls.corpus = [
            "A longitudinal study of school teachers and classroom curriculum in "
            "high school education, measuring academic achievement of students.",
            "Interviews with patients in a psychiatric hospital about mental health "
            "treatment, clinical depression and medical care.",
            "Survey of trade union members and collective bargaining in a labor union.",
            "A study of farming households, crops, livestock and agricultural harvest.",
            "Records of presidential elections, voting, parliament and public "
            "administration policy.",
        ]
        cls.classifier = IsicClassifier().fit(cls.corpus)

    def test_assigns_the_expected_divisions(self):
        expected = ["85", "86", "94", "01", "84"]
        results = self.classifier.classify(self.corpus)
        for document, want, got in zip(self.corpus, expected, results):
            self.assertEqual(got["primary_class"], want,
                             f"{document[:45]!r} -> {got['primary_class']}")

    def test_unrelated_text_is_left_unclassified(self):
        result = self.classifier.classify(["zzz qqq"])[0]
        self.assertIsNone(result["primary_class"])
        self.assertEqual(result["confidence"], "NONE")

    def test_secondary_class_differs_in_section(self):
        for result in self.classifier.classify(self.corpus):
            if result["secondary_class"]:
                self.assertNotEqual(
                    isic.section_of(result["primary_class"]),
                    isic.section_of(result["secondary_class"]),
                )

    def test_is_deterministic(self):
        first = self.classifier.classify(self.corpus)
        second = self.classifier.classify(self.corpus)
        self.assertEqual(first, second)

    def test_metadata_outweighs_base_data(self):
        """A short title must not be buried by a long, off-topic file text."""
        scores = self.classifier.score_combined(
            ["school teachers classroom curriculum education"],
            ["farming crops livestock " * 200],
        )
        result = self.classifier.interpret(scores)[0]
        self.assertEqual(result["primary_class"], "85")

    def test_missing_base_data_does_not_lower_the_score(self):
        """Projects whose files could not be downloaded must stay comparable."""
        metadata = ["school teachers classroom curriculum education"]
        without = self.classifier.score_combined(metadata, [""])
        with_same = self.classifier.score_combined(metadata, metadata)
        self.assertAlmostEqual(without.max(), with_same.max(), places=6)


if __name__ == "__main__":
    unittest.main()
