import os
from django.test import TestCase
from .models import PMKBVariant, PMKBInterpretation, TissueType, TumorType
from .ir import IRTable

# https://docs.djangoproject.com/en/2.1/topics/testing/overview/
# https://docs.djangoproject.com/en/2.1/intro/tutorial05/

fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
IR_tsv = os.path.join(fixtures_dir, "SeraSeq.tsv")

# accesses the production database
# print(PMKBVariant.objects.all().count()) # 22834

class InterpreterTestCase(TestCase):
    def setUp(self):
        # make demo fake db entries
        self.tumor_type_instance = TumorType.objects.create(type = "Acute Myeloid Leukemia")
        self.tissue_type_instance = TissueType.objects.create(type = "Blood")
        self.interpretation_instance = PMKBInterpretation.objects.create(
            interpretation = "Foo",
            citations = "Bar",
            source_row =  5
            )
        self.variant_instance = PMKBVariant.objects.get_or_create(
            gene = 'NRAS',
            tumor_type = self.tumor_type_instance,
            tissue_type = self.tissue_type_instance,
            variant = '',
            tier = 1,
            interpretation = self.interpretation_instance,
            source_row =  5
        )

    def test_pmkb_db(self):
        # check that there is only 1 entry in the test db now
        self.assertTrue(PMKBVariant.objects.all().count() == 1)
        self.assertTrue(PMKBInterpretation.objects.all().count() == 1)
