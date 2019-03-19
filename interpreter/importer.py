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
import hashlib
from collections import defaultdict, OrderedDict

# import django app
# if __name__ == '__main__':
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
django.setup()
from interpreter.models import PMKBVariant, PMKBInterpretation, TumorType, TissueType, NYUTier, NYUInterpretation
from interpreter.util import sanitize_tumor_tissue, debugger
sys.path.pop(0)
import logging
logger = logging.getLogger()

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


def import_PMKB_bulk(entries):
    """
    """
    num_created_interpretations = 0
    num_skipped_interpretations = 0
    # import unique interpretations first
    # need to jump through some hoops to get all unique interpretations;
    # iterate over dataframe and concatenate the interpretation fields to make a unique key
    # use key in dict to store database entry instance to use later
    logger.debug("Importing unique interpretations")
    unique_interpretations = defaultdict(OrderedDict)
    for index, row in entries.iterrows():
        interpretation_data_str = "".join([
            str(row['Interpretation']),
            str(row['Citation']),
            str(row['Source'])
        ])
        if interpretation_data_str not in unique_interpretations:
            instance, created = PMKBInterpretation.objects.get_or_create(
                interpretation = row['Interpretation'],
                citations = row['Citation'],
                source_row =  row['Source'],
                )
            unique_interpretations[interpretation_data_str]['instance'] = instance
            unique_interpretations[interpretation_data_str]['created'] = created
            if created:
                num_created_interpretations += 1
            else:
                num_skipped_interpretations += 1
        else:
            num_skipped_interpretations += 1

    logger.debug("Getting bulk variant entries")
    num_created_variants = 0
    num_skipped_variants = 0
    # make list of bulk entries to import
    bulk_variants = []
    # list of skipped variants
    not_created = []
    # unique variants
    unique_variants = defaultdict(OrderedDict)
    for index, row in entries.iterrows():
        # get forgeign key instances needed for each
        interpretation_data_str = "".join([
            str(row['Interpretation']),
            str(row['Citation']),
            str(row['Source'])
        ])

        # set unique key for each variant
        variant_str = "".join([
            row['Gene'],
            row['TumorType'],
            row['TissueType'],
            row['Variant'],
            str(row['Tier']),
            row['Interpretation'],
            row['Citation'],
            str(row['Source'])
        ])
        variant_md5 = hashlib.md5(variant_str.encode('utf-8')).hexdigest()
        if variant_str not in unique_variants:
            unique_variants[variant_str]['row'] = row
            variant_instance = PMKBVariant(
            gene = row['Gene'],
            tumor_type = TumorType.objects.get(type = sanitize_tumor_tissue(row['TumorType'])),
            tissue_type = TissueType.objects.get(type = sanitize_tumor_tissue(row['TissueType'])),
            variant = row['Variant'],
            tier = row['Tier'],
            interpretation = unique_interpretations[interpretation_data_str]['instance'],
            source_row =  row['Source'],
            uid = variant_md5
            )
            bulk_variants.append(variant_instance)
            num_created_variants += 1
        else:
            not_created.append(row)
            num_skipped_variants += 1
    # add all variants to the database
    logger.debug("Importing bulk variant entries ({0} total)".format(len(bulk_variants)))
    PMKBVariant.objects.bulk_create(bulk_variants)

    total_db_variants = PMKBVariant.objects.count() # 22834
    total_db_interpretations = PMKBInterpretation.objects.count()# 408
    logger.debug("Added {num_created} variants to the database. {tot_var} total variants and {tot_interp} total interpretations in the database".format(
    num_created = num_created_variants,
    tot_var = total_db_variants,
    tot_interp = total_db_interpretations
    ))
    return(not_created)

def import_PMKB_get_or_create(entries):
    """
    """
    num_created_interpretations = 0
    num_skipped_interpretations = 0
    num_created_variants = 0
    num_skipped_variants = 0
    not_created = []
    for index, row in entries.iterrows():
        # set unique key for each variant
        variant_str = "".join([
            row['Gene'],
            row['TumorType'],
            row['TissueType'],
            row['Variant'],
            str(row['Tier']),
            row['Interpretation'],
            row['Citation'],
            str(row['Source'])
        ])
        variant_md5 = hashlib.md5(variant_str.encode('utf-8')).hexdigest()

        # get the tumor type from the database
        tumor_type_instance = TumorType.objects.get(type = sanitize_tumor_tissue(row['TumorType']))
        tissue_type_instance = TissueType.objects.get(type = sanitize_tumor_tissue(row['TissueType']))

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
            source_row =  row['Source'],
            uid = variant_md5
        )
        if created_variant:
            num_created_variants += 1
        else:
            num_skipped_variants += 1
            not_created.append(row)
    total_db_variants = PMKBVariant.objects.count() # 22834
    total_db_interpretations = PMKBInterpretation.objects.count()# 408
    logger.debug("Added {new_interp} new interpretations ({skip_interp} skipped) and {new_var} new variants ({skip_var} skipped) to the database. {tot_var} total variants and {tot_interp} total interpretations in the database".format(
    new_interp = num_created_interpretations,
    skip_interp = num_skipped_interpretations,
    new_var = num_created_variants,
    skip_var = num_skipped_variants,
    tot_var = total_db_variants,
    tot_interp = total_db_interpretations
    ))
    return(not_created)

def import_PMKB(**kwargs):
    """
    Imports entries from PMKB .xlsx file into the database
    """
    pmkb_xlsx = kwargs.pop('pmkb_xlsx', config['pmkb_xlsx'])
    import_limit = kwargs.pop('import_limit', config['import_limit'])

    # convert the xlsx to a Pandas dataframe
    pmkb_df = xlsx2df(pmkb_xlsx)
    logger.debug("Read {0} entries from xlsx file".format(len(pmkb_df.index)))

    # need to clean and reformat some attributes of the dataframe
    pmkb_df = clean_pmkb_df(pmkb_df)

    # create the entries for the database
    entries = make_PMKB_entries(pmkb_df)
    logger.debug("Generated {0} variant entries".format(len(entries.index)))

    entries.to_csv("all_entries.tsv", sep = "\t")

    # remove duplicates caused by duplicate PMKB entries in Excel sheet
    num_entries_start = entries.shape[0]
    entries = entries.drop_duplicates()
    num_entries_end = entries.shape[0]
    logger.debug("Removed {0} duplicates; {1} unique entries remain to be imported to database".format(
    num_entries_start - num_entries_end,
    num_entries_end
    ))
    if PMKBVariant.objects.count() == 0:
        logger.debug("Importing interpretation entries in bulk")
        not_created = import_PMKB_bulk(entries)
    else:
        logger.debug("Database already has variants entries; Importing interpretation entries individually. This might take a while...")
        not_created = import_PMKB_get_or_create(entries)
    # # debugger(locals().copy())

    # save the skipped entries, if any
    if len(not_created) > 0:
        with open("pmkb.import.skipped.tsv", "w") as f:
            writer = csv.DictWriter(f, delimiter = '\t', fieldnames = not_created[0].keys())
            writer.writeheader()
            for row in not_created:
                writer.writerow({ k:str(v) for k,v in row.items() })

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
        instance, created = TumorType.objects.get_or_create(type = sanitize_tumor_tissue(tumor_type))
        if created:
            num_created += 1
        else:
            num_skipped += 1
    logger.debug("Added {new} new tumor types ({skipped} skipped) to the databse".format(
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
        instance, created = TissueType.objects.get_or_create(type = sanitize_tumor_tissue(tissue_type))
        if created:
            num_created += 1
        else:
            num_skipped += 1
    logger.debug("Added {new} new tissue types ({skipped} skipped) to the database".format(
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
        for row in reader:
            tumor_type_instance = TumorType.objects.get(type = sanitize_tumor_tissue(row['tumor_type']))
            tissue_type_instance = TissueType.objects.get(type = sanitize_tumor_tissue(row['tissue_type']))
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
        logger.debug("Added {new} new tissue types ({skipped} skipped) to the databse".format(
        new = num_created,
        skipped = num_skipped
        ))

def import_nyu_interpretations(**kwargs):
    """
    """
    nyu_interpretations_tsv = kwargs.pop('nyu_interpretations_tsv', config['nyu_interpretations_tsv'])
    num_created = 0
    num_skipped = 0
    with open(nyu_interpretations_tsv) as f:
        reader = csv.DictReader(f, delimiter = '\t')
        for row in reader:
            tumor_type_instance = TumorType.objects.get(type = sanitize_tumor_tissue(row['TumorType']))
            tissue_type_instance = TissueType.objects.get(type = sanitize_tumor_tissue(row['TissueType']))

            instance, created = NYUInterpretation.objects.get_or_create(
            genes = row['Gene'],
            variant_type = row['VariantType'],
            tumor_type = tumor_type_instance,
            tissue_type = tissue_type_instance,
            variant = row['Variant'],
            interpretation = row['Interpretation'],
            citations = row['Citation']
            )
            if created:
                num_created += 1
            else:
                num_skipped += 1
    logger.debug("Added {new} new NYU interpretations ({skipped} skipped) to the databse".format(
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
    nyu_interpretations_tsv = kwargs.pop('nyu_interpretations_tsv', config['nyu_interpretations_tsv'])
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

    if import_type == "nyu_interpretation":
        import_nyu_interpretations(nyu_interpretations_tsv = nyu_interpretations_tsv)


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
