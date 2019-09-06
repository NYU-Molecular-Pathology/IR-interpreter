import os
from django.test import TestCase
from .report import make_report_html


fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
IR_tsv = os.path.join(fixtures_dir, "SeraSeq.tsv")

class TestIR(TestCase):
    databases = '__all__'
    def setUp(self):
        self.IR_tsv = IR_tsv
        self.html = make_report_html(input = self.IR_tsv)

    def test_report_html_creation(self):
        self.assertTrue(len(self.html) > 0)
    def test_report_content_start(self):
        self.assertTrue(self.html.strip().startswith('<!DOCTYPE html>'))
    def test_report_content_end(self):
        self.assertTrue(self.html.strip().endswith('</html>'))
