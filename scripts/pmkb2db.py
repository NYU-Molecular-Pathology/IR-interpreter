#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script for loading and parsing the PMKB Excel sheet
Outputs tables in .tsv, .csv format, along with SQLite database
requires Python 3+
"""
import pandas as pd
import csv
import sqlite3
import argparse
import os

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

def make_interpretations(df):
    """
    Make a new dataframe just for the interpretations
    """
    # pull off just the interpretations & citations
    df = df[['Source', 'Interpretation', 'Citation']]
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
    return(df2)

def save_interpretations(df, output):
    """
    Save the interpretations to file
    """
    df.to_csv(output, sep ='\t', index = False, encoding = "utf-16")

def save_entries(df, output):
    """
    Save the variant information
    """
    df.to_csv(output, sep =',', index = False, quoting = csv.QUOTE_ALL)

def save_db(interpretations, entries, output):
    """
    Save the PMKB data to SQLite database
    """
    conn = sqlite3.connect(output)
    interpretations.to_sql("interpretations", conn, if_exists = "replace", index = False)
    entries.to_sql("entries", conn, if_exists = "replace", index = False)
    # test that it worked
    # my_debugger(locals().copy())
    # pd.read_sql_query("select * from entries;", conn)
    # pd.read_sql_query("select TumorType from entries;", conn)

def save_db_tissues(db, output):
    """
    """
    conn = sqlite3.connect(db)
    tissues = list(pd.read_sql_query("select TumorType from entries;", conn).TumorType.unique())
    with open(output, "w") as f:
        for tissue in tissues:
            f.write("{0}\n".format(tissue))

def save_db_tumor(db, output):
    """
    """
    conn = sqlite3.connect(db)
    tumors = list(pd.read_sql_query("select TissueType from entries;", conn).TissueType.unique())
    with open(output, "w") as f:
        for tumor in tumors:
            f.write("{0}\n".format(tumor))

def my_debugger(vars):
    '''
    starts interactive Python terminal at location in script
    very handy for debugging
    call this function with
    my_debugger(globals().copy())
    anywhere in the body of the script, or
    my_debugger(locals().copy())
    within a script function
    '''
    import readline # optional, will allow Up/Down/History in the console
    import code
    # vars = globals().copy() # in python "global" variables are actually module-level
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()


def main(**kwargs):
    """
    Main control function
    """
    pmkb_db = kwargs.pop('pmkb_db', None)
    pmkb_xlsx = kwargs.pop('pmkb_xlsx')
    interpretations_file = kwargs.pop('interpretations_file', None)
    entries_file = kwargs.pop('entries_file', None)
    tumors_file = kwargs.pop('tumors_file', None)
    tissues_file = kwargs.pop('tissues_file', None)

    pmkb_df = xlsx2df(pmkb_xlsx)
    pmkb_df = clean_pmkb_df(pmkb_df)
    interpretations = make_interpretations(pmkb_df)
    entries = make_entries(pmkb_df)

    if interpretations_file:
        save_interpretations(interpretations, output = interpretations_file)
    if entries_file:
        save_entries(entries, output = entries_file)
    if pmkb_db:
        save_db(interpretations, entries, output = pmkb_db)
    if tumors_file and pmkb_db:
        save_db_tumor(db = pmkb_db, output = tumors_file)
    if tissues_file and pmkb_db:
        save_db_tissues(db = pmkb_db, output = tissues_file)

def parse():
    """
    Parses script args
    """
    parser = argparse.ArgumentParser(description='Prints a column from a file')
    parser.add_argument("--pmkb-xlsx", default = "pmkb.xlsx", dest = 'pmkb_xlsx', help="PMKB Excel spreadsheet input")
    parser.add_argument("--db", default = "pmkb.db", dest = 'pmkb_db', help="SQLite output file")
    parser.add_argument("--interpretations", default = "pmkb.interpretations.tsv", dest = 'interpretations_file', help="Output file for clinical interpretations")
    parser.add_argument("--entries", default = "pmkb.entries.csv", dest = 'entries_file', help="Output file for variant entries")
    parser.add_argument("--tumors", default = "pmkb.tumor-terms.txt", dest = 'tumors_file', help="Output file for tumor type terms")
    parser.add_argument("--tissues", default = "pmkb.tissue-terms.txt", dest = 'tissues_file', help="Output file for tissue type terms")

    args = parser.parse_args()

    main(**vars(args))

if __name__ == '__main__':
    parse()
