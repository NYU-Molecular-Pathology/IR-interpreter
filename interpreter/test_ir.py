import os
from django.test import TestCase
from .models import PMKBVariant
from .ir import IRTable
import numpy as np

fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
IR_tsv = os.path.join(fixtures_dir, "SeraSeq.tsv")

class TestIR(TestCase):
    def setUp(self):
        self.demo_table = IRTable(source = IR_tsv)

    def tearDown(self):
        del self.demo_table

    def test_true(self):
        self.assertTrue(True, 'Demo True assertion')

    def test_exampleData_exits(self):
            self.assertTrue(os.path.exists(IR_tsv), 'Example data file does not exist')

    def test_records_genes1(self):
        expected_genes = ['TMPRSS2', 'ERG']
        table_genes = self.demo_table.records[34].genes
        self.assertTrue(table_genes == expected_genes, 'Did not return expected genes: {0}, instead got: {1}'.format(expected_genes, table_genes))

    def test_records_genes2(self):
        expected_genes = ['EGFR', 'EGFR-AS1']
        table_genes = self.demo_table.records[19].genes
        self.assertTrue(table_genes == expected_genes, 'Did not return expected genes: {0}, instead got: {1}'.format(expected_genes, table_genes))

    def test_records_genes3(self):
        expected_genes = ['NRAS']
        table_genes = self.demo_table.records[0].genes
        self.assertTrue(table_genes == expected_genes, 'Did not return expected genes: {0}, instead got: {1}'.format(expected_genes, table_genes))

    def test_parse_af1(self):
        afs = self.demo_table.records[0].parse_af(af = 'AA=0.00, AG=0.00, CG=11.27, CT=0.00, GG=0.00')
        expected_afs = ['CG=11.27']
        self.assertTrue(afs == expected_afs, 'Did not return expected afs: {0}, instead got: {1}'.format(expected_afs, afs))

    def test_parse_af2(self):
        afs = self.demo_table.records[0].parse_af(af = '9.09')
        expected_afs = ['9.09']
        self.assertTrue(afs == expected_afs, 'Did not return expected afs: {0}, instead got: {1}'.format(expected_afs, afs))

    def test_parse_af3(self):
        afs = self.demo_table.records[0].parse_af(af = np.nan)
        expected_afs = ['nan']
        self.assertTrue(afs == expected_afs, 'Did not return expected afs: {0}, instead got: {1}'.format(expected_afs, afs))

    def test_parse_af4(self):
        """
        Make sure string coercion works to parse AF entries that were not read in as strings
        float input = string output
        """
        afs = self.demo_table.records[0].parse_af(af = 38.44)
        expected_afs = ['38.44']
        self.assertTrue(afs == expected_afs, 'Did not return expected afs: {0}, instead got: {1}'.format(expected_afs, afs))
