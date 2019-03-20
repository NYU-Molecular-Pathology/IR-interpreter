from django.test import TestCase
from .util import capitalize, sanitize_tumor_tissue, sanitize_genes

class TestUtil(TestCase):
    def test_capitalize1(self):
        bad_label = "adamantinomatous craniopharyngioma"
        good_label = "Adamantinomatous Craniopharyngioma"
        self.assertTrue(capitalize(bad_label) == good_label)

    def test_capitalize2(self):
        bad_label = "ABC"
        good_label = "ABC"
        self.assertTrue(capitalize(bad_label) == good_label)

    def test_sanitize_tumor_tissue1(self):
        bad_label = ""
        good_label = "Any"
        self.assertTrue(sanitize_tumor_tissue(bad_label) == good_label)

    def test_sanitize_tumor_tissue2(self):
        bad_label = "All"
        good_label = "Any"
        self.assertTrue(sanitize_tumor_tissue(bad_label) == good_label)

    def test_sanitize_tumor_tissue3(self):
        bad_label = "All Tumor Types"
        good_label = "Any"
        self.assertTrue(sanitize_tumor_tissue(bad_label) == good_label)

    def test_sanitize_genes(self):
        bad_genes = ["EGFR", "-", "NRAS"]
        good_genes = ["EGFR", "NRAS"]
        self.assertTrue(sanitize_genes(bad_genes) == good_genes)

    def test_sanitize_genes(self):
        bad_genes = ["EGFR", "NRAS"]
        good_genes = ["EGFR", "NRAS"]
        self.assertTrue(sanitize_genes(bad_genes) == good_genes)
