#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Import data from files into the databases.

PMKB: Import entries from PMKB Excel .xlsx sheet into database
https://pmkb.weill.cornell.edu/therapies/download.xlsx

"""
import os
import sys
import django
import pandas as pd
import argparse
import json
import csv


# import django app
# if __name__ == '__main__':
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
django.setup()
from interpreter.models import PMKBVariant, PMKBInterpretation, TumorType, TissueType, NYUTier
from interpreter.util import capitalize, debugger
sys.path.pop(0)

# load relative paths from JSON file
config_json = os.path.join(os.path.realpath(os.path.dirname(__file__)), "importer.json")
with open(config_json) as f:
    config_json_data = json.load(f)

# global default configs for the module
config = {}
config['fixtures_dir'] = os.path.join(os.path.realpath(os.path.dirname(__file__)), config_json_data['fixtures_dir'])
config['pmkb_xlsx'] = os.path.join(config['fixtures_dir'], config_json_data['pmkb_xlsx'])
config['tumor_types_json'] = os.path.join(config['fixtures_dir'], config_json_data['tumor_types_json'])
config['tissue_types_json'] = os.path.join(config['fixtures_dir'], config_json_data['tissue_types_json'])
config['nyu_interpretations_tsv'] = os.path.join(config['fixtures_dir'], config_json_data['nyu_interpretations_tsv'])
config['nyu_tiers_csv'] = os.path.join(config['fixtures_dir'], config_json_data['nyu_tiers_csv'])
config['import_limit'] = -1
config['import_type'] = "PMKB"

def xlsx2df(xlsx_file, return_sheet = None):
    """
    Loads PMKB Excel file into Pandas dataframe
    """
    if return_sheet is None:
        return_sheet = 'Interpretations'
    # read excel file
    xls_file = pd.ExcelFile(xlsx_file)
    # load each excel sheet into a dict entry
    xls_dict = {sheet_name: xls_file.parse(sheet_name) for sheet_name in xls_file.sheet_names}
    # pull off interpretations df
    df = xls_dict[return_sheet]
    return(df)

def clean_pmkb_df(df):
    """
    Cleans up some aspects of the raw data loaded from PMKB Excel file
    """
    # fix column names
    df = df.rename({
    'Tumor Type(s)': 'TumorType',
    'Tissue Type(s)': 'TissueType',
    'Variant(s)': 'Variant',
    'Interpretations': 'Interpretation',
    'Citations': 'Citation'
    }, axis='columns')

    # collapse citations to a single column
    df['Citation'] = df.loc[:, 'Citation': ].fillna('').astype(str).apply(lambda x: '\n'.join(x).strip(), axis=1)
    df.drop(list(df.filter(regex = 'Unnamed')), axis = 1, inplace = True)

    # add row numbers as a column called 'Source'; the original source entry
    df.index.names = ['Source']
    df = df.reset_index()

    # convert Tiers to int
    df.Tier = df.Tier.fillna(0).astype(int)
    return(df)

def make_PMKB_entries(df):
    """
    Make a new dataframe just for the variant entries
    """
    # pull off tier
    tier = df[['Source', 'Tier']]

    # pull off genes
    gene = df[['Source', 'Gene']]

    # split rows with multiple entries apart
    tumor = df['TumorType'].str.split(',').apply(pd.Series, 1).stack().map(lambda x: x.strip())
    tissue = df['TissueType'].str.split(',').apply(pd.Series, 1).stack().map(lambda x: x.strip())
    # split on comma's that are preceeded by a capital letter
    variant = df['Variant'].str.split(r'\s*,\s*(?=[A-Z])').apply(pd.Series, 1).stack().map(lambda x: x.strip())

    # convert them to dataframe with new columns
    tumor = tumor.reset_index()
    tumor.columns = ['Source', 'Entry', 'TumorType']
    tissue = tissue.reset_index()
    tissue.columns = ['Source', 'Entry', 'TissueType']
    variant = variant.reset_index()
    variant.columns = ['Source', 'Entry', 'Variant']

    # merge them back together
    df2 = pd.merge(left = tumor[['Source', 'TumorType']],
        right = tissue[['Source', 'TissueType']],
        on = 'Source')
    df2 = pd.merge(left = df2, right = variant[['Source', 'Variant']])
    df2 = pd.merge(left = df2, right = tier)
    df2 = pd.merge(left = df2, right = gene)

    # combine the original interpretations back onto the dataframe
    df3 = pd.merge(df2, df[['Source', 'Interpretation', 'Citation']], on = 'Source')
    return(df3)


def import_PMKB(**kwargs):
    """
    Imports entries from PMKB .xlsx file into the database
    """
    pmkb_xlsx = kwargs.pop('pmkb_xlsx', config['pmkb_xlsx'])
    import_limit = kwargs.pop('import_limit', config['import_limit'])

    # convert the xlsx to a Pandas dataframe
    pmkb_df = xlsx2df(pmkb_xlsx)
    print("Read {0} entries from xlsx file".format(len(pmkb_df.index)))

    # need to clean and reformat some attributes of the dataframe
    pmkb_df = clean_pmkb_df(pmkb_df)

    # create the entries for the database
    entries = make_PMKB_entries(pmkb_df)
    print("Generated {0} variant entries".format(len(entries.index)))

    if int(import_limit) < 0:
        import_limit = None

    print("Importing variant entries; import limit is: {0}".format(import_limit))
    num_created_interpretations = 0
    num_created_variants = 0
    num_skipped_interpretations = 0
    num_skipped_variants = 0
    for index, row in entries.iterrows():
        # NOTE: limit on number imported for dev; full import takes ~3min
        # TODO: figure out how to speed this up
        if import_limit and num_created_variants >= int(import_limit):
            break
        else:
            # get the tumor type from the database
            tumor_type_instance = TumorType.objects.get(type = capitalize(row['TumorType']))
            tissue_type_instance = TissueType.objects.get(type = capitalize(row['TissueType']))

            # add the interpretations first
            interpretation_instance, created_interpretation = PMKBInterpretation.objects.get_or_create(
                interpretation = row['Interpretation'],
                citations = row['Citation'],
                source_row =  row['Source'],
                )
            if created_interpretation:
                num_created_interpretations += 1
            else:
                num_skipped_interpretations += 1

            # add the variant in each row
            instance, created_variant = PMKBVariant.objects.get_or_create(
                gene = row['Gene'],
                tumor_type = tumor_type_instance,
                tissue_type = tissue_type_instance,
                variant = row['Variant'],
                tier = row['Tier'],
                interpretation = interpretation_instance,
                source_row =  row['Source']
            )
            if created_variant:
                num_created_variants += 1
            else:
                num_skipped_variants += 1
    print("Added {new_interp} new interpretations ({skip_interp} skipped) and {new_var} new variants ({skip_var} skipped) to the database".format(
    new_interp = num_created_interpretations,
    skip_interp = num_skipped_interpretations,
    new_var = num_created_variants,
    skip_var = num_skipped_variants
    ))

def import_tumor_types(**kwargs):
    """
    Imports tumor types from JSON file to the database
    """
    tumor_types_json = kwargs.pop('tumor_types_json', config['tumor_types_json'])

    with open(tumor_types_json) as f:
        tumor_types = json.load(f)

    num_created = 0
    num_skipped = 0
    for tumor_type in tumor_types:
        instance, created = TumorType.objects.get_or_create(type = capitalize(tumor_type))
        if created:
            num_created += 1
        else:
            num_skipped += 1
    print("Added {new} new tumor types ({skipped} skipped) to the databse".format(
    new = num_created,
    skipped = num_skipped
    ))

def import_tissue_types(**kwargs):
    """
    Imports tumor types from JSON file to the database
    """
    tissue_types_json = kwargs.pop('tissue_types_json', config['tissue_types_json'])

    with open(tissue_types_json) as f:
        tissue_types = json.load(f)

    num_created = 0
    num_skipped = 0
    for tissue_type in tissue_types:
        instance, created = TissueType.objects.get_or_create(type = capitalize(tissue_type))
        if created:
            num_created += 1
        else:
            num_skipped += 1
    print("Added {new} new tissue types ({skipped} skipped) to the databse".format(
    new = num_created,
    skipped = num_skipped
    ))

def import_nyu_tiers(**kwargs):
    """
    Imports values from the NYU tiers list to the database
    """
    nyu_tiers_csv = kwargs.pop('nyu_tiers_csv', config['nyu_tiers_csv'])
    num_created = 0
    num_skipped = 0
    with open(nyu_tiers_csv) as f:
        reader = csv.DictReader(f)
        # debugger(locals().copy())
        for row in reader:
            tumor_type_instance = TumorType.objects.get(type = capitalize(row['tumor_type']).strip())
            tissue_type_instance = TissueType.objects.get(type = capitalize(row['tissue_type']).strip())
            instance, created = NYUTier.objects.get_or_create(
            gene = row['gene'],
            variant_type = row['type'],
            tumor_type = tumor_type_instance,
            tissue_type = tissue_type_instance,
            coding = row['coding'],
            protein = row['protein'],
            tier = int(row['tier']),
            comment = row['comment']
            )
            if created:
                num_created += 1
            else:
                num_skipped += 1
        print("Added {new} new tissue types ({skipped} skipped) to the databse".format(
        new = num_created,
        skipped = num_skipped
        ))

def main(**kwargs):
    """
    Main control function for the module.
    """
    pmkb_xlsx = kwargs.pop('pmkb_xlsx', config['pmkb_xlsx'])
    tumor_types_json = kwargs.pop('tumor_types_json', config['tumor_types_json'])
    tissue_types_json = kwargs.pop('tissue_types_json', config['tissue_types_json'])
    nyu_tiers_csv = kwargs.pop('nyu_tiers_csv', config['nyu_tiers_csv'])
    import_limit = kwargs.pop('import_limit', config['import_limit'])
    import_type = kwargs.pop('import_type', config['import_type'])


    if import_type == "tumor_type":
        import_tumor_types(tumor_types_json = tumor_types_json)

    if import_type == "tissue_type":
        import_tissue_types(tissue_types_json = tissue_types_json)

    if import_type == "PMKB":
        import_PMKB(pmkb_xlsx = pmkb_xlsx, import_limit = import_limit)

    if import_type == "nyu_tier":
        import_nyu_tiers(nyu_tiers_csv = nyu_tiers_csv)

def parse():
    """
    Parses script args.
    """
    parser = argparse.ArgumentParser(description='Import data from files into the app database')
    parser.add_argument("--fixtures-dir", default = config['fixtures_dir'], dest = 'fixtures_dir', help="Parent directory to search for static files")
    parser.add_argument("--import-limit", default = config['import_limit'], dest = 'import_limit', help="Number of entries to import into database from PMKB. Value of -1 means no limit")
    parser.add_argument("--type", default = config['import_type'], dest = 'import_type', help="Type of data to import")
    args = parser.parse_args()
    main(**vars(args))


if __name__ == '__main__':
    parse()
