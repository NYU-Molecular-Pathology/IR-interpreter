#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for monitoring a local directory and running the program based on discovered inputs
"""
import os
import report
import argparse
import rsync
import json

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

def make_reports(inputDir, overwrite = False):
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
        params = {}
        input_basename = os.path.splitext(input)[0]

        # check for params files
        input_json = input_basename + ".json"
        if os.path.exists(input_json):
            with open(input_json) as f:
                params.update(json.load(f))

        # check for output already exists
        output = input_basename + ".html"
        if os.path.exists(output):
            if overwrite is True:
                print(">>> Overwriting output: {0}".format(output))
                report.make_report(input = input, output = output, params = params)
        else:
            print(">>> Generating output: {0}".format(output))
            report.make_report(input = input, output = output, params = params)


def main(**kwargs):
    """
    Main control function for the script
    """
    inputDirs = kwargs.pop('inputDirs')
    useRsync = kwargs.pop('useRsync', False)
    rsyncConfig = kwargs.pop('rsyncConfig', None)
    overwrite = kwargs.pop('overwrite', False)
    removeSource = kwargs.pop('removeSource', False)



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
            make_reports(inputDir = inputDir, overwrite = overwrite)
            # then copy everything back to remote destination; remove local copies
            print(">>> Syncing {0} directory with {1}".format(rsync.config['targetDir'], inputDir))
            if removeSource:
                flags = ['--remove-source-files']
            else:
                flags = []
            rsync.rsync(source = inputDir, target = rsync.config['targetDir'], dryRun = False, flags = flags)
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
    parser.add_argument("--overwrite", action='store_true', dest = 'overwrite', help="Overwrite pre-existing HTML output for input .tsv files")
    parser.add_argument("--remove-source", action='store_true', dest = 'removeSource', help="Remove local source files when using rsync, so that only remote files remain after running")


    args = parser.parse_args()

    main(**vars(args))

if __name__ == '__main__':
    parse()
