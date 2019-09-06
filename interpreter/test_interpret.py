import os
import hashlib
from django.test import TestCase
from .models import PMKBVariant, PMKBInterpretation, TissueType, TumorType
from .ir import IRTable
from .interpret import interpret_pmkb
"""
Tests for the interpret module, to make sure that the correct interpretations are being returned under various conditions
"""
fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
IR_tsv = os.path.join(fixtures_dir, "SeraSeq.tsv")
NRAS_IDH1_tsv = os.path.join(fixtures_dir, "NRAS_IDH1.tsv")

class TestInterpret(TestCase):
    databases = '__all__'
    @classmethod # causes setup to only run once per instance of this class, instead of before every test
    def setUpTestData(self):
        # make demo fake db entries
        # need to test: inclusion filter, exclusion filter, 'Any' handling

        # create some tumor and tissue entries
        Adenocarcinoma = TumorType.objects.create(type = "Adenocarcinoma")
        Any_tumor = TumorType.objects.create(type = "Any")
        Carcinoma = TumorType.objects.create(type = "Carcinoma")

        Lung = TissueType.objects.create(type = "Lung")
        Any_tissue = TissueType.objects.create(type = "Any")
        Skin = TissueType.objects.create(type = "Skin")

        # create some interpretations
        interpretation1 = PMKBInterpretation.objects.create(
            interpretation = "Bar",
            citations = "Foo",
            source_row =  1
            )
        interpretation2 = PMKBInterpretation.objects.create(
            interpretation = "Baz",
            citations = "Foo",
            source_row =  2
            )

        interpretation3 = PMKBInterpretation.objects.create(
            interpretation = "Buzz",
            citations = "Foo",
            source_row =  3
            )

        # create variants for NRAS for all combinations of tumor and tissue
        for tumor in [ Adenocarcinoma, Any_tumor, Carcinoma ]:
            for tissue in [ Lung, Any_tissue, Skin ]:
                for gene in [ 'NRAS', 'EGFR' ]:
                    for interpretation in [ interpretation1, interpretation2 ]:
                        variant_str = "".join([
                            gene,
                            tumor.type,
                            tissue.type,
                            '',
                            str(1),
                            interpretation.interpretation,
                            str(1)
                        ])
                        variant_md5 = hashlib.md5(variant_str.encode('utf-8')).hexdigest()
                        PMKBVariant.objects.create(
                            gene = gene,
                            tumor_type = tumor,
                            tissue_type = tissue,
                            variant = '',
                            tier = 1,
                            interpretation = interpretation,
                            source_row =  1,
                            uid = variant_md5
                        )

        # add extraneous entries that should not match anything in any tests
        variant_str = "".join([
            'EGFR',
            Adenocarcinoma.type,
            Lung.type,
            '',
            str(1),
            interpretation3.interpretation,
            str(1)
        ])
        variant_md5 = hashlib.md5(variant_str.encode('utf-8')).hexdigest()
        PMKBVariant.objects.create(
            gene = 'EGFR',
            tumor_type = Adenocarcinoma,
            tissue_type = Lung,
            variant = '',
            tier = 1,
            interpretation = interpretation3,
            source_row =  1,
            uid = variant_md5
        )

        variant_str = "".join([
            'SOX9',
            Carcinoma.type,
            Skin.type,
            '',
            str(1),
            interpretation3.interpretation,
            str(1)
        ])
        variant_md5 = hashlib.md5(variant_str.encode('utf-8')).hexdigest()
        PMKBVariant.objects.create(
            gene = 'SOX9',
            tumor_type = Carcinoma,
            tissue_type = Skin,
            variant = '',
            tier = 1,
            interpretation = interpretation3,
            source_row =  1,
            uid = variant_md5
        )

    def test_total_num_test_db_entries(self):
        """
        Test that the number of entries in the test database matches the expected number
        """
        self.assertTrue(len(PMKBVariant.objects.values_list('id', flat=True)) == 38)

    def test_pmkb_tissue_none_tumor_none_NRAS_IDH1_1(self):
        """
        If tissue_type = None and tumor_type = None, then all entries matching the given gene should be returned regardless of tumor or tissue type

        NRAS_IDH1.tsv contains 1 NRAS and 1 IDH1 variant
        database contains 18 variant entries for NRAS, 18 for EGFR
        should return 2 interpretations with 9 variants each
        """
        tissue_type = None
        tumor_type = None
        params = {'tissue_type': tissue_type, 'tumor_type': tumor_type}
        ir_table = IRTable(source = NRAS_IDH1_tsv)
        ir_table = interpret_pmkb(ir_table = ir_table, **params)
        # test that NRAS returned 2 interpretations, 'Bar' and 'Baz', with 9 total variants, including all tumor and tissue types
        self.assertTrue( ir_table.records[0].genes == ['NRAS'] )
        self.assertTrue( len(ir_table.records[0].interpretations['pmkb']) == 2 )
        self.assertTrue( ir_table.records[0].interpretations['pmkb'][0]['interpretation'].interpretation == "Bar" )
        self.assertTrue( len(ir_table.records[0].interpretations['pmkb'][0]['variants']) == 9 )
        self.assertTrue(all([ v.gene == 'NRAS' for v in ir_table.records[0].interpretations['pmkb'][0]['variants'] ]))
        self.assertTrue(sorted(set(
            [ v.tumor_type.type for v in ir_table.records[0].interpretations['pmkb'][0]['variants'] ]
            )) == ['Adenocarcinoma', 'Any', 'Carcinoma'])
        self.assertTrue(sorted(set(
            [ v.tissue_type.type for v in ir_table.records[0].interpretations['pmkb'][0]['variants'] ]
            )) == ['Any', 'Lung', 'Skin'])

        # repeat for the second NRAS interpretation
        self.assertTrue(ir_table.records[0].interpretations['pmkb'][1]['interpretation'].interpretation == 'Baz')
        self.assertTrue( len(ir_table.records[0].interpretations['pmkb'][1]['variants']) == 9 )
        self.assertTrue(all([ v.gene == 'NRAS' for v in ir_table.records[0].interpretations['pmkb'][1]['variants'] ]))
        self.assertTrue(sorted(set(
            [ v.tumor_type.type for v in ir_table.records[0].interpretations['pmkb'][1]['variants'] ]
            )) == ['Adenocarcinoma', 'Any', 'Carcinoma'])
        self.assertTrue(sorted(set(
            [ v.tissue_type.type for v in ir_table.records[0].interpretations['pmkb'][1]['variants'] ]
            )) == ['Any', 'Lung', 'Skin'])

        # test that the IDH1 entry did not get any matches
        self.assertTrue(ir_table.records[1].genes == ['IDH1'])
        self.assertTrue(ir_table.records[1].interpretations['pmkb'] == [] )
        self.assertTrue(len(ir_table.records[1].interpretations['pmkb']) == 0 )

    def test_pmkb_tissue_Any_tumor_Any_NRAS_IDH1_1(self):
        """
        Same as above but testing that functions of 'Any' are the same as they were for None
        """
        tissue_type = 'Any'
        tumor_type = 'Any'
        params = {'tissue_type': tissue_type, 'tumor_type': tumor_type}
        ir_table = IRTable(source = NRAS_IDH1_tsv)
        ir_table = interpret_pmkb(ir_table = ir_table, **params)
        # test that NRAS returned 2 interpretations, 'Bar' and 'Baz', with 9 total variants, including all tumor and tissue types
        self.assertTrue( ir_table.records[0].genes == ['NRAS'] )
        self.assertTrue( len(ir_table.records[0].interpretations['pmkb']) == 2 )
        self.assertTrue( ir_table.records[0].interpretations['pmkb'][0]['interpretation'].interpretation == "Bar" )
        self.assertTrue( len(ir_table.records[0].interpretations['pmkb'][0]['variants']) == 9 )
        self.assertTrue(all([ v.gene == 'NRAS' for v in ir_table.records[0].interpretations['pmkb'][0]['variants'] ]))
        self.assertTrue(sorted(set(
            [ v.tumor_type.type for v in ir_table.records[0].interpretations['pmkb'][0]['variants'] ]
            )) == ['Adenocarcinoma', 'Any', 'Carcinoma'])
        self.assertTrue(sorted(set(
            [ v.tissue_type.type for v in ir_table.records[0].interpretations['pmkb'][0]['variants'] ]
            )) == ['Any', 'Lung', 'Skin'])

        # repeat for the second NRAS interpretation
        self.assertTrue(ir_table.records[0].interpretations['pmkb'][1]['interpretation'].interpretation == 'Baz')
        self.assertTrue( len(ir_table.records[0].interpretations['pmkb'][1]['variants']) == 9 )
        self.assertTrue(all([ v.gene == 'NRAS' for v in ir_table.records[0].interpretations['pmkb'][1]['variants'] ]))
        self.assertTrue(sorted(set(
            [ v.tumor_type.type for v in ir_table.records[0].interpretations['pmkb'][1]['variants'] ]
            )) == ['Adenocarcinoma', 'Any', 'Carcinoma'])
        self.assertTrue(sorted(set(
            [ v.tissue_type.type for v in ir_table.records[0].interpretations['pmkb'][1]['variants'] ]
            )) == ['Any', 'Lung', 'Skin'])

        # test that the IDH1 entry did not get any matches
        self.assertTrue(ir_table.records[1].genes == ['IDH1'])
        self.assertTrue(ir_table.records[1].interpretations['pmkb'] == [] )
        self.assertTrue(len(ir_table.records[1].interpretations['pmkb']) == 0 )

    def test_pmkb_tissue_Any_tumor_Adenocarcinoma_NRAS_IDH1_1(self):
        """
        Test the correct results for tumor_type=Adenocarcinoma

        Should return 2 interpretations for NRAS, with 3 variants each, all tumor_type should be Adenocarcinoma and all three tissue_type should be returned, IDH1 should return no interpretations
        """
        tissue_type = None
        tumor_type = "Adenocarcinoma"
        params = {'tissue_type': tissue_type, 'tumor_type': tumor_type}
        ir_table = IRTable(source = NRAS_IDH1_tsv)
        ir_table = interpret_pmkb(ir_table = ir_table, **params)
        self.assertTrue( len(ir_table.records[0].interpretations['pmkb']) == 2 )
        self.assertTrue( ir_table.records[0].interpretations['pmkb'][0]['interpretation'].interpretation == "Bar" )
        self.assertTrue(all([ v.gene == 'NRAS' for v in ir_table.records[0].interpretations['pmkb'][0]['variants'] ]))
        self.assertTrue(sorted(set(
            [ v.tumor_type.type for v in ir_table.records[0].interpretations['pmkb'][1]['variants'] ]
            )) == ['Adenocarcinoma'])
        self.assertTrue(sorted(set(
            [ v.tissue_type.type for v in ir_table.records[0].interpretations['pmkb'][1]['variants'] ]
            )) == ['Any', 'Lung', 'Skin'])

        # test that the IDH1 entry did not get any matches
        self.assertTrue(ir_table.records[1].genes == ['IDH1'])
        self.assertTrue(ir_table.records[1].interpretations['pmkb'] == [] )
        self.assertTrue(len(ir_table.records[1].interpretations['pmkb']) == 0 )

    def test_pmkb_tissue_Lung_tumor_Adenocarcinoma_NRAS_IDH1_1(self):
        """
        Test the correct results for tumor_type=Adenocarcinoma tissue_type=Lung

        Should return 2 interpretations for NRAS, each should be only for Lung Adenocarcinoma
        """
        tissue_type = 'Lung'
        tumor_type = "Adenocarcinoma"
        params = {'tissue_type': tissue_type, 'tumor_type': tumor_type}
        ir_table = IRTable(source = NRAS_IDH1_tsv)
        ir_table = interpret_pmkb(ir_table = ir_table, **params)

        self.assertTrue( len(ir_table.records[0].interpretations['pmkb']) == 2 )
        self.assertTrue( ir_table.records[0].interpretations['pmkb'][0]['interpretation'].interpretation == "Bar" )
        self.assertTrue( len(ir_table.records[0].interpretations['pmkb'][0]['variants']) == 1 )
        self.assertTrue( ir_table.records[0].interpretations['pmkb'][0]['variants'][0].gene == 'NRAS' )
        self.assertTrue( ir_table.records[0].interpretations['pmkb'][0]['variants'][0].tissue_type.type == 'Lung' )
        self.assertTrue( ir_table.records[0].interpretations['pmkb'][0]['variants'][0].tumor_type.type == 'Adenocarcinoma' )

        self.assertTrue( ir_table.records[0].interpretations['pmkb'][1]['interpretation'].interpretation == "Baz" )
        self.assertTrue( len(ir_table.records[0].interpretations['pmkb'][1]['variants']) == 1 )
        self.assertTrue( ir_table.records[0].interpretations['pmkb'][1]['variants'][0].gene == 'NRAS' )
        self.assertTrue( ir_table.records[0].interpretations['pmkb'][1]['variants'][0].tissue_type.type == 'Lung' )
        self.assertTrue( ir_table.records[0].interpretations['pmkb'][1]['variants'][0].tumor_type.type == 'Adenocarcinoma' )

        # test that the IDH1 entry did not get any matches
        self.assertTrue(ir_table.records[1].genes == ['IDH1'])
        self.assertTrue(ir_table.records[1].interpretations['pmkb'] == [] )
        self.assertTrue(len(ir_table.records[1].interpretations['pmkb']) == 0 )
