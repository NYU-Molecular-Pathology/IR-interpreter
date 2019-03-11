import os
from django.test import TestCase
# https://docs.djangoproject.com/en/2.1/topics/testing/overview/
# https://docs.djangoproject.com/en/2.1/intro/tutorial05/

fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
test_IR_tsv = os.path.join(fixtures_dir, "SeraSeq.tsv")

class InterpreterTestCase(TestCase):
    def test_fixtures_exist(self):
        self.assertEqual(os.path.exists(fixtures_dir), True)
    def test_fixtures_sheet_exists(self):
        self.assertEqual(os.path.exists(test_IR_tsv), True)
