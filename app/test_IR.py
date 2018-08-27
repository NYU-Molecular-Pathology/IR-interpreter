#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
unit tests for the IR module
"""
import os
import unittest
from IR import IRTable

# run from parent repo dir
test_tsv = os.path.join("example-data", "Seraseq-DNA_RNA-07252018_v1_79026a9c-e0ff-4a32-9686-ead82c35f793-2018-08-21-15-00-11200.tsv")

class TestIR(unittest.TestCase):
    def setUp(self):
        self.demo_table = IRTable(source = test_tsv)

    def tearDown(self):
        del self.demo_table

    def test_true(self):
        self.assertTrue(True, 'Demo True assertion')

    def test_exampleData_exits(self):
        self.assertTrue(os.path.exists(test_tsv), 'Example data file does not exist')

    def test_records_genes1(self):
        expected_genes = ['ERG', 'TMPRSS2']
        self.assertTrue(self.demo_table.records[34].genes == expected_genes, 'Did not return expected genes: {0}'.format(expected_genes))

    def test_records_genes2(self):
        expected_genes = ['EGFR', 'EGFR-AS1']
        self.assertTrue(self.demo_table.records[19].genes == expected_genes, 'Did not return expected genes: {0}'.format(expected_genes))
