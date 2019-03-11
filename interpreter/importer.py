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

# import django app
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
django.setup()
from interpreter.models import PMKBVariant, PMKBInterpretation
sys.path.pop(0)

# global default configs for the module
config = {}
config['fixtures_dir'] = os.path.join(os.path.realpath(os.path.dirname(__file__)), "fixtures")
config['pmkb_xlsx'] = os.path.join(config['fixtures_dir'], "pmkb.xlsx")
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
    fixtures_dir = kwargs.pop('fixtures_dir', config['fixtures_dir'])
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
        if import_limit and num_created_variants >= int(import_limit):
            break
        else:
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
                tumor_type = row['TumorType'],
                tissue_type = row['TissueType'],
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

def main(**kwargs):
    """
    Main control function for the module.
    """
    fixtures_dir = kwargs.pop('fixtures_dir', config['fixtures_dir'])
    pmkb_xlsx = kwargs.pop('pmkb_xlsx', config['pmkb_xlsx'])
    import_limit = kwargs.pop('import_limit', config['import_limit'])
    import_type = kwargs.pop('import_type', config['import_type'])

    if import_type == "PMKB":
        import_PMKB(
            fixtures_dir = fixtures_dir,
            pmkb_xlsx = pmkb_xlsx,
            import_limit = import_limit
            )

def parse():
    """
    Parses script args.
    """
    parser = argparse.ArgumentParser(description='Import data from files into the app database')
    parser.add_argument("--fixtures-dir", default = config['fixtures_dir'], dest = 'fixtures_dir', help="Parent directory to search for static files")
    parser.add_argument("--pmkb-xlsx", default = config['pmkb_xlsx'], dest = 'pmkb_xlsx', help="Path to PMKB .xlsx file to import from")
    parser.add_argument("--import-limit", default = config['import_limit'], dest = 'import_limit', help="Number of entries to import into database. Value of -1 means no limit")
    parser.add_argument("--type", default = config['import_type'], dest = 'import_type', help="Type of data to import")
    args = parser.parse_args()
    main(**vars(args))


if __name__ == '__main__':
    parse()
