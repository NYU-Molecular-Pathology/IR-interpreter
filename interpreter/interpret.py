#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for handling the interpretation of IonReporter .tsv results against databases
"""
import os
import sys
import django

# import app from top level directory
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
django.setup()
from interpreter.models import PMKBVariant, PMKBInterpretation
from interpreter.ir import IRTable
sys.path.pop(0)

class PMKBResults(object):
    """
    Object for aggregating database query results for PMKB variants and their interpretations
    """
    def __init__(self):
        self.variants = []
        self.interpretations = []

def query_variant(model, **params):
    # print(params)
    variants = model.objects.filter(**params)
    return(variants)

def query_pmkb(genes, **params):
    tissue_type = params.pop('tissue_type', None)
    tumor_type = params.pop('tumor_type', None)
    variant = params.pop('variant', None)
    results = PMKBResults()
    for gene in genes:
        PMKB_params = {'gene': gene}
        if tissue_type:
            PMKB_params['tissue_type'] = tissue_type
        if tumor_type:
            PMKB_params['tumor_type'] = tumor_type
        if variant:
            PMKB_params['variant'] = variant
        for variant in query_variant(model = PMKBVariant, **PMKB_params):
            results.variants.append(variant)
    return(results)

def demo():
    tissueType = "Skin"
    tumorType = "Melanoma"
    ir_tsv = sys.argv[1] # "example-data/SeraSeq.tsv"
    ir_table = IRTable(source = ir_tsv)
    # print(ir_table.records)
    for record in ir_table.records:
        print(record.genes)
        for gene in record.genes:
            PMKB_params = {
            'gene': gene,
            'tumor_type': tumorType,
            'tissue_type': tissueType
            }
            PMKB_variants = query_variant(model = PMKBVariant, **PMKB_params)
            # record.interpretations
            for variant in PMKB_variants:
                # interpretation = PMKBInterpretation.objects.get(interpretation = variant.interpretation)
                print(variant.interpretation.interpretation)
        # break

if __name__ == '__main__':
    demo()
