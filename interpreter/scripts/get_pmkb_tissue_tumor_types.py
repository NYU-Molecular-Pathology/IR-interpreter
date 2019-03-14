#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Write out the list of tissue and tumor types from the PMKB .xlsx file
Uses the interpreter.importer module
"""
import os
import sys
import json
import csv
import re

# import the importer app from parent dir
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
import importer
from util import capitalize
sys.path.pop(0)

# get the configs
output_tumor_types_json = "tumor_types.json"
output_tumor_types_csv = "tumor_types.csv"
output_tissue_types_json = "tissue_types.json"
output_tissue_types_csv = "tissue_types.csv"
pmkb_xlsx = importer.config['pmkb_xlsx']
nyu_tiers_csv = importer.config['nyu_tiers_csv']
nyu_interpretations_tsv = importer.config['nyu_interpretations_tsv']

# Load PMKB data
pmkb_df = importer.xlsx2df(pmkb_xlsx)
pmkb_df = importer.clean_pmkb_df(pmkb_df)
entries = importer.make_PMKB_entries(pmkb_df)
pmkb_tumor_types = entries['TumorType'].tolist()
pmkb_tissue_types = entries['TissueType'].tolist()

# Load NYU tiers data
nyu_tier_tumor_types = []
nyu_tier_tissue_types = []
with open(nyu_tiers_csv) as f:
    reader = csv.DictReader(f)
    for row in reader:
        nyu_tier_tumor_types.append(row['tumor_type'])
        pmkb_tissue_types.append(row['tissue_type'])

# Load NYU Interpretations data
nyu_interpretations_tissue_types = []
nyu_interpretations_tumor_types = []
with open(nyu_interpretations_tsv) as f:
    reader = csv.DictReader(f, delimiter = '\t')
    for row in reader:
        nyu_interpretations_tumor_types.append(row['TumorType'])
        nyu_interpretations_tissue_types.append(row['TissueType'])

# clean up the entries; remove trailing spaces, capitalize, unique, sort
tumor_types = nyu_interpretations_tumor_types + nyu_tier_tumor_types + pmkb_tumor_types
tumor_types = [ i.strip() for i in tumor_types ]
tumor_types = [ capitalize(i) for i in tumor_types ]
# need to include empty string
tumor_types = tumor_types + ['']
tumor_types = sorted(set(tumor_types))
# tumor_types = [ i for i in tumor_types if i != '' ]

tissue_types = nyu_interpretations_tissue_types + nyu_tier_tissue_types + pmkb_tissue_types
tissue_types = [ i.strip() for i in tissue_types ]
tissue_types = [ capitalize(i) for i in tissue_types ]
# need to include empty string
tissue_types = tissue_types + ['']
tissue_types = sorted(set(tissue_types))
# tissue_types = [ i for i in tissue_types if i != '' ]

# write output
with open(output_tumor_types_json, "w") as f:
    json.dump(tumor_types, f, indent = 4)
with open(output_tissue_types_json, "w") as f:
    json.dump(tissue_types, f, indent = 4)

# its actually a .txt but call it .csv so it opens in Excel
with open(output_tumor_types_csv, "w") as f:
    for item in tumor_types:
        f.write("{0}\n".format(item))

with open(output_tissue_types_csv, "w") as f:
    for item in tissue_types:
        f.write("{0}\n".format(item))
