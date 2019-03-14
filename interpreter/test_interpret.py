import os
from django.test import TestCase
from .models import PMKBVariant, PMKBInterpretation, TissueType, TumorType
from .ir import IRTable
from .interpret import interpret_pmkb

fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
IR_tsv = os.path.join(fixtures_dir, "SeraSeq.tsv")

class TestInterpret(TestCase):
    @classmethod # causes setup to only run once per instance of this class, instead of before every test
    def setUpTestData(self):
        # make demo fake db entries
        self.tumor_type_instance = TumorType.objects.create(type = "Adenocarcinoma")
        self.tissue_type_instance = TissueType.objects.create(type = "Lung")
        self.interpretation_instance = PMKBInterpretation.objects.create(
            interpretation = "Foo",
            citations = "Bar",
            source_row =  1 # must be unique across all tests in app
            )
        self.variant_instance = PMKBVariant.objects.create(
            gene = 'NRAS',
            tumor_type = self.tumor_type_instance,
            tissue_type = self.tissue_type_instance,
            variant = '',
            tier = 1,
            interpretation = self.interpretation_instance,
            source_row =  1
        )
        self.ir_table = IRTable(source = IR_tsv)
        self.tissue_type = "Lung"
        self.tissue_type_instance = TissueType.objects.get(type = self.tissue_type)
        self.tumor_type = "Adenocarcinoma"
        self.tumor_type_instance = TumorType.objects.get(type = self.tumor_type)
        self.params = {'tissue_type': self.tissue_type_instance, 'tumor_type': self.tumor_type_instance}
        self.ir_table = interpret_pmkb(ir_table = self.ir_table, **self.params)

    def test_interpret_genes_match_expected1(self):
        all_genes = set()
        for record in self.ir_table.records:
            for interpretation in record.interpretations['pmkb']:
                for variant in interpretation['variants']:
                    all_genes.add(variant.gene)
        self.assertTrue((all([ gene == 'NRAS' for gene in all_genes ])))

    def test_interpret_tissue_types_match_expected1(self):
        all_tissue_types = set()
        for record in self.ir_table.records:
            for interpretation in record.interpretations['pmkb']:
                for variant in interpretation['variants']:
                    all_tissue_types.add(variant.tissue_type.type)
        self.assertTrue((all([ tissue == 'Lung' for tissue in all_tissue_types ])))

    def test_interpret_tumor_types_match_expected1(self):
        all_tumor_types = set()
        for record in self.ir_table.records:
            for interpretation in record.interpretations['pmkb']:
                for variant in interpretation['variants']:
                    all_tumor_types.add(variant.tumor_type.type)
        self.assertTrue((all([ tumor == 'Adenocarcinoma' for tumor in all_tumor_types ])))
