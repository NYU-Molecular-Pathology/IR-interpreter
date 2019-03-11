import os
from django.test import TestCase
from .models import PMKBVariant
from .ir import IRTable

# https://docs.djangoproject.com/en/2.1/topics/testing/overview/
# https://docs.djangoproject.com/en/2.1/intro/tutorial05/

fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
IR_tsv = os.path.join(fixtures_dir, "SeraSeq.tsv")

# print(PMKBVariant.objects.all().count())

class InterpreterTestCase(TestCase):
    def setUp(self):
        self.fixtures_dir = fixtures_dir
        self.IR_tsv = IR_tsv
