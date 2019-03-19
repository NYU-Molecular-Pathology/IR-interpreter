#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for handling the interpretation of IonReporter .tsv results against databases
"""
import os
import sys
import django
from collections import defaultdict
import logging
import json

logger = logging.getLogger()

# import app from top level directory
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
django.setup()
from interpreter.models import PMKBVariant, TissueType, TumorType, NYUTier, NYUInterpretation
from interpreter.ir import IRTable
from interpreter.util import debugger
sys.path.pop(0)

def query_variant(model, **params):
    """
    NOTE: what is this for? I do not remember
    Perhaps some future method of potentially querying a variant directly
    Consider deleting this
    """
    variants = model.objects.filter(**params)
    return(variants)

def query_pmkb(genes, **params):
    """
    Get PMKB interpretations for a list of genes.

    Parameters
    ----------
    genes: list
        a list of gene identifiers
    **params: str
        an optional set of string keyword arguments to filter PMKB results by, for the following keys: 'tissue_type', 'tumor_type', 'variant'

    Returns
    -------
    list
        a list of dict's containing the interpretations for all variants matching the given genes, filtering by other criteria passed in `**params`
    """
    # parse the parameters passed
    tissue_type = params.pop('tissue_type', None)
    tumor_type = params.pop('tumor_type', None)
    variant = params.pop('variant', None)

    # build database query
    logger.debug("building database query")
    variant_query = PMKBVariant.objects.filter(gene__in = genes)
    if tissue_type and tissue_type != 'Any':
        logger.debug("adding tissue_type to query")
        variant_query = variant_query.filter(tissue_type = TissueType.objects.get(type = tissue_type))
    if tumor_type and tumor_type != 'Any':
        logger.debug("adding tumor_type to query")
        variant_query = variant_query.filter(tumor_type = TumorType.objects.get(type = tumor_type))
    if variant:
        logger.debug("adding variant to query")
        variant_query = variant_query.filter(variant = variant)

    # store interpretations in dict; list of unique variants for each interpretation
    logger.debug("getting unique interpretations from query")
    interpretations = defaultdict(set)
    for variant_result in variant_query:
        interpretations[variant_result.interpretation].add(variant_result)

    # convert to list of dicts
    logger.debug("reformatting query results")
    results = []
    for key, value in interpretations.items():
        d = {'interpretation': key, 'variants': list(value)}
        results.append(d)
    return(results)

def interpret_pmkb(ir_table, **params):
    """
    Adds PMKB interpretations to an Ion Reporter table

    Parameters
    ----------
    ir_table: IRTable
        an `IRTable` object created from a valid Ion Reporter export .tsv file

    Returns
    -------
    IRTable
        the original `ir_table` object is returned, with interpretations added for each record in the table.
    """
    # parse the parameters passed
    tissue_type = params.pop('tissue_type', None)
    tumor_type = params.pop('tumor_type', None)
    variant = params.pop('variant', None)
    logger.debug("querying PMKB database for records in the IRTable")
    for record in ir_table.records:
        pmkb_results = query_pmkb(genes = record.genes,
            tissue_type = tissue_type,
            tumor_type = tumor_type,
            variant = variant)
        record.interpretations['pmkb'] = pmkb_results
    logger.debug("returning database query results")
    return(ir_table)

def query_nyu_tier(genes, **params):
    """
    """
    tissue_type = params.pop('tissue_type', None)
    tumor_type = params.pop('tumor_type', None)
    variant = params.pop('variant', None)
    # build database query
    logger.debug("building NYU tier database query")
    variant_query = NYUTier.objects.filter(gene__in = genes)
    if tissue_type and tissue_type != 'Any':
        logger.debug("adding tissue_type to query")
        variant_query = variant_query.filter(tissue_type = TissueType.objects.get(type = tissue_type))
    if tumor_type and tumor_type != 'Any':
        logger.debug("adding tumor_type to query")
        variant_query = variant_query.filter(tumor_type = TumorType.objects.get(type = tumor_type))
    if variant:
        logger.debug("adding variant to query")
        variant_query = variant_query.filter(variant = variant)

    # store proteins in dict; list of unique tiers for each protein
    logger.debug("getting unique protein codings from query")
    proteins = defaultdict(set)
    for variant_result in variant_query:
        proteins[variant_result.protein].add(variant_result)
    # convert to list of dicts
    logger.debug("reformatting query results")
    results = []
    for key, value in proteins.items():
        d = {'protein': key, 'tiers': list(value)}
        results.append(d)
    return(results)

def interpret_nyu_tier(ir_table, **params):
    """
    Adds NYU Tier interpretations to an Ion Reporter table

    Parameters
    ----------
    ir_table: IRTable
        an `IRTable` object created from a valid Ion Reporter export .tsv file

    Returns
    -------
    IRTable
        the original `ir_table` object is returned, with interpretations added for each record in the table.
    """
    tissue_type = params.pop('tissue_type', None)
    tumor_type = params.pop('tumor_type', None)
    variant = params.pop('variant', None)
    logger.info("querying NYU tier database for records in the IRTable")
    for record in ir_table.records:
        nyu_tier_results = query_nyu_tier(genes = record.genes,
            tissue_type = tissue_type,
            tumor_type = tumor_type,
            variant = variant)
        record.interpretations['nyu_tier'] = nyu_tier_results
    # debugger(locals().copy())
    return(ir_table)

def query_nyu_interpretation(genes, **params):
    """
    """
    tissue_type = params.pop('tissue_type', None)
    tumor_type = params.pop('tumor_type', None)
    variant = params.pop('variant', None)
    # build database query
    logger.debug("building NYU interpretation database query")

    variant_query =  NYUInterpretation.objects.all()
    if tissue_type and tissue_type != 'Any':
        logger.debug("adding tissue_type to query")
        variant_query = variant_query.filter(tissue_type = TissueType.objects.get(type = tissue_type))
    if tumor_type and tumor_type != 'Any':
        logger.debug("adding tumor_type to query")
        variant_query = variant_query.filter(tumor_type = TumorType.objects.get(type = tumor_type))
    if variant:
        logger.debug("adding variant to query")
        variant_query = variant_query.filter(variant = variant)

    results = []
    for interpretation in variant_query:
        interpretation_genes = json.loads(interpretation.genes_json)
        if any(x in interpretation_genes for x in genes):
            results.append(interpretation)
    return(results)

def interpret_nyu_interpretation(ir_table, **params):
    """
    """
    tissue_type = params.pop('tissue_type', None)
    tumor_type = params.pop('tumor_type', None)
    variant = params.pop('variant', None)
    logger.info("querying NYU interpretation database for records in the IRTable")
    for record in ir_table.records:
        nyu_interpretation_results = query_nyu_interpretation(genes = record.genes,
            tissue_type = tissue_type,
            tumor_type = tumor_type,
            variant = variant)
        record.interpretations['nyu_interpretation'] = nyu_interpretation_results
    # debugger(locals().copy())
    return(ir_table)

def demo():
    tumor_type = "Any"
    tissue_type = "Any" # Adrenal Gland
    params = {'tissue_type': tissue_type, 'tumor_type': tumor_type}
    ir_tsv = sys.argv[1] # "example-data/SeraSeq.tsv"
    ir_table = IRTable(source = ir_tsv)
    ir_table = interpret_pmkb(ir_table = ir_table, **params)
    ir_table = interpret_nyu_tier(ir_table = ir_table, **params)
    ir_table = interpret_nyu_interpretation(ir_table = ir_table, **params)
    debugger(locals().copy())
    # print(ir_table.records[3].interpretations['pmkb'])
    # print(ir_table.records[3].interpretations['nyu_tier'])
    # print(ir_table.records[3].interpretations['nyu_tier'][0]['tiers'][0].tier)
    # print(ir_table.records[3].interpretations['nyu_tier'][0]['tiers'][0].protein)
    # ir_table.records[11].interpretations['nyu_interpretation']

if __name__ == '__main__':
    demo()
