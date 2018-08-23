#!/usr/bin/env python
"""
Prints a single column from a file
Use this when terminal 'cut' doesnt work due to formatting issues
NOTE: Python 3+ required for utf-16 input !!
"""
import sys
import csv
import argparse

def main(**kwargs):
    """
    Main control function for the script
    """
    input_file = kwargs.pop('input_file')[0]
    delimiter = kwargs.pop('delimiter', '\t')
    field_num = int(kwargs.pop('field_num', 1)) - 1 # field numbers are 1-based but Python list index is 0-based
    encoding = kwargs.pop('encoding', 'utf-8')

    with open(input_file, encoding = encoding) as fin:
        reader = csv.DictReader(fin, delimiter = delimiter)
        fieldnames = reader.fieldnames
        for row in reader:
            print(row[fieldnames[field_num]])

def parse():
    """
    Parses script args
    """
    parser = argparse.ArgumentParser(description='Prints a column from a file')
    parser.add_argument('input_file', nargs=1, help="Input file")
    parser.add_argument("-d", default = '\t', dest = 'delimiter', help="Delimiter")
    parser.add_argument("-f", default = 1, dest = 'field_num', help="Column in the file to output")
    parser.add_argument("-e", default = 'utf-8', dest = 'encoding', help="Text encoding. NOTE: Python 3+ required for utf-16") # "utf-16"
    args = parser.parse_args()

    main(**vars(args))

if __name__ == '__main__':
    parse()
