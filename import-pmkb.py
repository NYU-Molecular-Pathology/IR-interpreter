#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Import entries from PMKB Excel .xlsx sheet into database
"""
import os
import sys
import django
import pandas as pd

# import django app
parentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
django.setup()
from interpreter.models import PMKBVariant, PMKBInterpretation
sys.path.pop(0)

def my_debugger(vars):
    """
    starts interactive Python terminal at location in script
    very handy for debugging
    call this function with
    my_debugger(globals().copy())
    anywhere in the body of the script, or
    my_debugger(locals().copy())
    within a script function
    """
    import readline # optional, will allow Up/Down/History in the console
    import code
    # vars = globals().copy() # in python "global" variables are actually module-level
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()

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

def make_entries(df):
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


if __name__ == '__main__':
    pmkb_xlsx = "db/pmkb.xlsx"
    pmkb_df = xlsx2df(pmkb_xlsx)
    print("Read {0} entries from xlsx file".format(len(pmkb_df.index)))
    pmkb_df = clean_pmkb_df(pmkb_df)
    entries = make_entries(pmkb_df)
    print("Generated {0} variant entries".format(len(entries.index)))

    num_created_interpretations = 0
    num_created_variants = 0
    for index, row in entries.iterrows():
        # add the interpretations first
        interpretaion_instance, created_interpretation = PMKBInterpretation.objects.get_or_create(
            interpretation = row['Interpretation'],
            citations = row['Citation'],
            source_row =  row['Source'],
            )
        if created_interpretation:
            num_created_interpretations += 1
        # add the variant in each row
        instance, created_variant = PMKBVariant.objects.get_or_create(
            gene = row['Gene'],
            tumor_type = row['TumorType'],
            tissue_type = row['TissueType'],
            variant = row['Variant'],
            tier = row['Tier'],
            interpretation = interpretaion_instance,
            source_row =  row['Source']
        )
        if created_variant:
            num_created_variants += 1
    print("Added {0} new interpretations and {1} new variants to the database".format(num_created_interpretations, num_created_variants))
    # my_debugger(locals().copy())
