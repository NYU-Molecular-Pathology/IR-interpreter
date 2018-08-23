#!/usr/bin/env python
"""
USAGE: ./dump-xlsx.py /path/to/my_file.xlsx

OUTPUT: /path/to/my_file.sheet_1.tsv

This script will dump every sheet in an XLSX Excel file to a TSV
Each worksheet in the Excel file will be saved to a separate TSV file
"""
import pandas as pd
import sys
import os
import argparse

def main(**kwargs):
    """
    Main control function for the script
    """
    input_file = kwargs.pop('input_file')[0]
    encoding = kwargs.pop('encoding', 'utf-16')

    file_base = os.path.splitext(os.path.basename(input_file))[0]
    file_dir = os.path.dirname(input_file)

    # read excel file
    xls_file = pd.ExcelFile(input_file)

    # load each excel sheet into a dict entry
    xls_dict = {sheet_name: xls_file.parse(sheet_name) for sheet_name in xls_file.sheet_names}

    # read each sheet into a Pandas dataframe then export as TSV
    for sheet_name, sheet_data, in xls_dict.items():
        sheet_df = xls_dict[sheet_name]
        out_file_name = '.'.join([file_base, sheet_name, "tsv"]).replace(" ", "_")
        out_file_path = os.path.join(file_dir, out_file_name)
        sheet_df.to_csv(out_file_path,sep ='\t', index = False, encoding = encoding) # encoding = 'utf-8'
        # utf-8 has better file compatibility but messes up strange text characters, utf-16 default for Windows Excel I think

def parse():
    """
    Parses script args
    """
    parser = argparse.ArgumentParser(description='Prints a column from a file')
    parser.add_argument('input_file', nargs=1, help="Input file")
    parser.add_argument("-e", default = "utf-16", dest = 'encoding', help="Output text encoding.") # 'utf-8'
    args = parser.parse_args()

    main(**vars(args))

if __name__ == '__main__':
    parse()
