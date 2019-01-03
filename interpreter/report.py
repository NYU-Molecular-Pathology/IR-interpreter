#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for generating a report based on IonReporter table and database matches
"""
import os
import sys
import django
from django.template.loader import get_template

# import app from top level directory
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
django.setup()
from interpreter.ir import IRTable, IRRecord
sys.path.pop(0)

def make_report_html(input, template = 'report.html'):
    """
    """
    report_template = get_template(template)
    table = IRTable(input)
    report_html = report_template.render({'IRtable': table})
    return(report_html)

if __name__ == '__main__':
    ir_tsv = sys.argv[1] # "example-data/SeraSeq.tsv"
    report_html = make_report_html(input = ir_tsv)
    print(report_html)
