#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Write out the list of tissue and tumor types from the PMKB .xlsx file
Uses the interpreter.importer module
"""
import os
import sys
import json
# import the importer app from parent dir
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
import importer
sys.path.pop(0)

output_tumor_types_json = "tumor_types.json"
output_tissue_types_json = "tissue_types.json"
pmkb_xlsx = importer.config['pmkb_xlsx']

pmkb_df = importer.xlsx2df(pmkb_xlsx)
pmkb_df = importer.clean_pmkb_df(pmkb_df)
entries = importer.make_PMKB_entries(pmkb_df)

tumor_types = sorted(set(entries['TumorType'].tolist()))
tissue_types = sorted(set(entries['TissueType'].tolist()))

with open(output_tumor_types_json, "w") as f:
    json.dump(tumor_types, f, indent = 4)
with open(output_tissue_types_json, "w") as f:
    json.dump(tissue_types, f, indent = 4)
