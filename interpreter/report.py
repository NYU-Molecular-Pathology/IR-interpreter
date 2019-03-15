#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for generating a report based on IonReporter table and database matches
"""
import os
import sys
import django
from django.template.loader import get_template
import time
import logging

logger = logging.getLogger()

# import app from top level directory
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
django.setup()
from interpreter.ir import IRTable, IRRecord
import interpreter.interpret as interpret
sys.path.pop(0)

def make_report_html(input, template = 'report.html', **params):
    """
    Generates an HTML report based on a supplied Ion Reporter .tsv file

    Parameters
    ----------
    input: str
        the path to an Ion Reporter .tsv file, or a file-like object that can be read
    template: str
        path to HTML template to use for reporting
    **params: str
        an optional set of string keyword arguments to filter interpretation query results by, for the following keys: 'tissue_type', 'tumor_type'

    Returns
    -------
    str
        the formatted HTML string output is returned
    """
    # calculate time used in generating report
    start = time.time()
    tissue_type = params.pop('tissue_type', None)
    tumor_type = params.pop('tumor_type', None)
    report_template = get_template(template)
    logger.info("generating IRTable from input file")
    table = IRTable(input)
    logger.info("generating PMKB interpretations")
    table = interpret.interpret_pmkb(
        ir_table = table,
        tissue_type = tissue_type,
        tumor_type = tumor_type
        )
    # print(table.records[3].interpretations['pmkb'][0]['variants'][0].gene)
    # print(type(table.records[3].interpretations['pmkb'][0]['variants'][0].gene))
    logger.debug("getting interpretation metrics")
    tumor_type_label = tumor_type
    if tumor_type_label == None:
        tumor_type_label = 'Any'
    tissue_type_label = tissue_type
    if tissue_type_label == None:
        tissue_type_label = 'Any'
    num_IR_entries = len(table.records)
    num_PMKB_interpretations = 0
    num_PMKB_variants = 0
    for record in table.records:
        for interpretation in record.interpretations['pmkb']:
            num_PMKB_interpretations += 1
            for variant in interpretation['variants']:
                num_PMKB_variants += 1

    end = time.time()
    elapsed = end - start
    elapsed_str = "{0:.2f}".format(elapsed)

    context = {
    'IRtable': table,
    'tumor_type': tumor_type_label,
    'tissue_type': tissue_type_label,
    'num_IR_entries': num_IR_entries,
    'num_PMKB_interpretations': num_PMKB_interpretations,
    'num_PMKB_variants': num_PMKB_variants,
    'elapsed': elapsed_str
    }

    logger.debug("rendering HTML from IRTable")
    report_html = report_template.render(context)
    logger.debug("returning HTML output")
    return(report_html)

def demo():
    ir_tsv = sys.argv[1] # "example-data/SeraSeq.tsv"
    report_html = make_report_html(input = ir_tsv)
    print(report_html)

if __name__ == '__main__':
    demo()
