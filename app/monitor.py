#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for monitoring a local directory and running the program based on discovered inputs
"""
import os
import template
import argparse
import rsync

def find_input_IR_tsvs(inputDir):
    """
    Searches for .tsv files in the provided input directory

    Parameters
    ----------
    inputDir: str
        path to directory to search for input files

    Returns
    -------
    str
        yields a character string representing the path to an input file

    Examples
    --------
    Example usage::

        for input_file in find_input_IR_tsvs(inputDir = "inputs"):
            do_thing(input_file)

    """
    for root, dirs, files in os.walk(inputDir):
        for item in files:
            if item.endswith('.tsv'):
                yield(os.path.join(root, item))

def make_reports(inputDir):
    """
    Makes HTML reports for all valid input files found in the supplied directory.

    Notes
    ------
    A valid input file:

    - ends with ``.tsv``
    - does not have an accompanying file with the same path that ends in ``.html``

    Parameters
    ----------
    inputDir: str
        path to directory to search for input files
    """
    for input in find_input_IR_tsvs(inputDir):
        output = os.path.splitext(input)[0] + ".html"
        if not os.path.exists(output):
            print(">>> Making output: {0}".format(output))
            template.make_report(input = input, output = output)

def main(**kwargs):
    """
    Main control function for the script
    """
    inputDirs = kwargs.pop('inputDirs')
    useRsync = kwargs.pop('useRsync', False)
    rsyncConfig = kwargs.pop('rsyncConfig', None)

    for inputDir in inputDirs:
        print(">>> Processing {0} dir".format(inputDir))
        if useRsync:
            # add trailing slash for rsync path
            inputDir = os.path.join(inputDir, '')
            # set the rsync config if passed
            if rsyncConfig:
                rsync.load_config(input_json = rsyncConfig)
            # first copy all remote files to local input dir
            print(">>> Syncing {0} directory with {1}".format(inputDir, rsync.config['targetDir']))
            rsync.rsync(source = inputDir, target = rsync.config['targetDir'], dryRun = False, swap = True)
            # then process all files in local input dir
            make_reports(inputDir = inputDir)
            # then copy everything back to remote destination
            print(">>> Syncing {0} directory with {1}".format(rsync.config['targetDir'], inputDir))
            rsync.rsync(source = inputDir, target = rsync.config['targetDir'], dryRun = False)
        else:
            # process all files in local input dir
            make_reports(inputDir = inputDir)

def parse():
    """
    Parses script args
    """
    parser = argparse.ArgumentParser(description='Checks a directory for input IR .tsv files that need to be processed')
    parser.add_argument('inputDirs', nargs='+', help="Local directories to monitor for input files")
    parser.add_argument("--rsync", action='store_true', dest = 'useRsync', help="Use rsync before and after checking input directories")
    parser.add_argument("--rsync-config", default = None, dest = 'rsyncConfig', help="JSON formatted config file to use for rsync parameters")

    args = parser.parse_args()

    main(**vars(args))

if __name__ == '__main__':
    parse()
