#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
unit tests for the PMKB module
"""
import unittest
from pmkb import PMKB
import os

pmkb_db = os.path.join("db", "pmkb.db")

class TestPMKB(unittest.TestCase):
    def setUp(self):
        self.pmkb = PMKB(source = pmkb_db)

    def tearDown(self):
        del self.pmkb

    def test_true(self):
        self.assertTrue(True, 'Demo True assertion')

    def test_exampleDb_exists(self):
        self.assertTrue(os.path.exists(self.pmkb.source), 'Example PMKB database does not exist')

    def test_returns_results_EGFR1(self):
        genes = ['EGFR']
        params = {'genes': genes}
        res = self.pmkb.query(params = params)
        self.assertTrue(len(res) > 1, 'PMKB database query does not return results for {0}'.format(genes))

    def test_returns_results_EGFR1_filters1(self):
        genes = ['EGFR']
        tumorType = 'Urothelial Carcinoma'
        tissueType = 'Kidney'
        params1 = {'genes': genes}
        params2 = {'genes': genes, 'tumorType': tumorType, 'tissueType': tissueType}
        res1 = self.pmkb.query(params = params1)
        res2 = self.pmkb.query(params = params2)
        self.assertTrue(len(res1) > len(res2), 'PMKB database does not return fewer results when extra params are applied')

    def test_noResults_invalidTumorTissue1(self):
        genes = ['EGFR']
        tumorType = 'foooo'
        tissueType = 'bar'
        params = {'genes': genes, 'tumorType': tumorType, 'tissueType': tissueType}
        res = self.pmkb.query(params = params)
        self.assertTrue(len(res) == 0, 'PMKB database returns results for invalid params: {0}'.format(params))
