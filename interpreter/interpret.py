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
    # parse the parameters passed
    tissue_type = params.pop('tissue_type', None)
    tumor_type = params.pop('tumor_type', None)
    variant = params.pop('variant', None)

    # build database query
    variant_query = PMKBVariant.objects.filter(gene__in = genes)
    if tissue_type:
        variant_query = variant_query.filter(tissue_type = tissue_type)
    if tumor_type:
        variant_query = variant_query.filter(tumor_type = tumor_type)
    if variant:
        variant_query = variant_query.filter(variant = variant)

    # store interpretations in dict; list of unique variants for each interpretation
    interpretations = defaultdict(set)
    for variant_result in variant_query:
        interpretations[variant_result.interpretation].add(variant_result)

    # convert to list of dicts
    results = []
    for key, value in interpretations.items():
        d = {'interpretation': key, 'variants': list(value)}
        results.append(d)
    return(results)

def interpret_pmkb(ir_table, **params):
    # parse the parameters passed
    tissue_type = params.pop('tissue_type', None)
    tumor_type = params.pop('tumor_type', None)
    variant = params.pop('variant', None)
    for record in ir_table.records:
        pmkb_results = query_pmkb(genes = record.genes,
            tissue_type = tissue_type,
            tumor_type = tumor_type,
            variant = variant)
        record.interpretations['pmkb'] = pmkb_results
    return(ir_table)

def demo():
    tumor_type = "Skin"
    tissue_type = "Melanoma"
    params = {'tissue_type': tissue_type, 'tumor_type': tumor_type}
    ir_tsv = sys.argv[1] # "example-data/SeraSeq.tsv"
    ir_table = IRTable(source = ir_tsv)
    ir_table = interpret_pmkb(ir_table = ir_table, **params)
    print(ir_table.records[3].interpretations['pmkb'])

if __name__ == '__main__':
    demo()
