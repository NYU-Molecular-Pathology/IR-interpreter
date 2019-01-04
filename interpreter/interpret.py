#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for handling the interpretation of IonReporter .tsv results against databases
"""
import os
import sys
import django
from collections import defaultdict

# import app from top level directory
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
django.setup()
from interpreter.models import PMKBVariant, PMKBInterpretation
from interpreter.ir import IRTable
sys.path.pop(0)

def query_variant(model, **params):
    variants = model.objects.filter(**params)
    return(variants)

def query_pmkb(genes, **params):
    tissue_type = params.pop('tissue_type', None)
    tumor_type = params.pop('tumor_type', None)
    variant = params.pop('variant', None)
    variant_query = PMKBVariant.objects.filter(gene__in = genes)
    if tissue_type:
        variant_query = variant_query.filter(tissue_type = tissue_type)
    if tumor_type:
        variant_query = variant_query.filter(tumor_type = tumor_type)
    if variant:
        variant_query = variant_query.filter(variant = variant)

    interpretations = defaultdict(set)
    for variant_result in variant_query:
        interpretations[variant_result.interpretation].add(variant_result)
    results = []
    for key, value in interpretations.items():
        d = {'interpretation': key, 'variants': list(value)}
        results.append(d)
    return(results)

def demo():
    tumor_type = "Skin"
    tissue_type = "Melanoma"
    ir_tsv = sys.argv[1] # "example-data/SeraSeq.tsv"
    ir_table = IRTable(source = ir_tsv)
    for record in ir_table.records:
        results = query_pmkb(genes = record.genes, params = {'tissue_type': tissue_type, 'tumor_type': tumor_type})
        print(results)

if __name__ == '__main__':
    demo()
