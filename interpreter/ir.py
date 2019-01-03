#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for parsing Ion Reporter exported .tsv file
"""
import pandas as pd
from collections import OrderedDict

class IRTable(object):
    """
    Class for parsing the .tsv formatted data exported from Ion Reporter web interface

    Parameters
    ----------
    source: str
        path to .tsv file to read in.
    params: dict
        dictionary of extra meta data parameters; 'tumorType', 'tissueType'
    """
    def __init__(self, source):
        self.source = source
        self.table = self.load_table(source = self.source)
        # TODO: fix header load method, need to do a seek(0) or something to read file again from start to allow load from memory
        # self.header = self.load_header(source = self.source)
        self.records = self.get_records(data = self.table)

    def load_table(self, source):
        """
        Loads the contents of the Ion Reporter .tsv file into a Pandas dataframe.

        Raw table maniupluation logic goes here.

        Parameters
        ----------
        source: str
            path to .tsv file to read in.

        Returns
        -------
        pandas.dataframe
            A dataframe with the loaded data

        Todo:
        -----
        Develop methods to load table from in-memory location, not just file on disk
        """
        df = pd.read_csv(source, sep = '\t', comment = '#')
        # add original table row numbers as a column in the table
        df.index.names = ['Row']
        df = df.reset_index()
        return(df)

    def get_records(self, data):
        """
        Creates a list of IRRecord objects for each entry in the table

        Parameters
        ----------
        data: pandas.dataframe
            A dataframe representing the Ion Reporter data read in

        Returns
        -------
        list
            a list of ``IRRecord`` objects, representing each record in the Ion Reporter output
        """
        # convert dataframe to list of dictionaries
        records = data.to_dict(orient='records')
        # initialize IRRecord objects
        ir_records = [ IRRecord(data = record) for record in records ]
        return(ir_records)

class IRRecord(object):
    """
    An entry in the variant table output by Ion Reporter exporter

    Parameters
    ----------
    data: dict
        dictionary of values parsed from the Ion Reporter .tsv table


    Examples
    --------
    Example usage::

        y = IRRecord(data = '')
        y.parse_genes('TMPRSS2(1) - ERG(2)')
        y.parse_genes('EGFR,EGFR-AS1')

    """
    def __init__(self, data, variant = None):
        self.data = data
        self.genes = self.parse_genes(self.data['Genes'])
        self.afs = self.parse_af(self.data['% Frequency'])
        self.af_str = ' '.join([str(x) for x in self.afs])

    def parse_genes(self, text):
        """
        Parses text to find the gene names

        Parameters
        ---------
        text: str
            a text string to be split into gene names

        Returns
        -------
        list
            a list of character strings representing gene names

        Examples
        --------
        Example usage::

            parse_genes('TMPRSS2(1) - ERG(2)')
            >>> ['TMPRSS2', 'ERG']
            parse_genes('EGFR,EGFR-AS1')
            >>> ['EGFR', 'EGFR-AS1']
            parse_genes('NRAS')
            >>> ['NRAS']

        """
        # use dict to maintain unique key values
        genes = OrderedDict()
        # try to split fusions apart and remove number in parenthesis
        if len(text.split(' - ')) > 1:
            # genes.update([ gene.split('(')[0] for gene in text.split(' - ') ])
            for gene in text.split(' - '):
                gene = gene.split('(')[0]
                genes[gene] = ''
        # try to split all other entries on comma
        if len(text.split(',')) > 1:
            # genes.update([ gene for gene in text.split(',') ])
            for gene in text.split(','):
                genes[gene] = ''
        # if there are still no genes in the dict, then use the entry as given
        if len(list(genes.keys())) < 1:
            gene = text
            genes[gene] = ''
        return(list(genes.keys()))

    def parse_af(self, af):
        """
        Attempts to split the Percent Allele Frequency ('% Frequency') entry in the IR table into separate entries and only keep non-zero entries.

        Parameters
        ----------
        af: str
            Allele frequency values from a row in the Ion Reporter .tsv table; coerced to type ``str``

        Returns
        -------
        list:
            a list character strings of the non-zero allele frequency values

        Examples:
        ---------
        Example usage::

            >>> parse_af(af = 'AA=0.00, AG=0.00, CG=11.27, CT=0.00, GG=0.00')
            ['CG=11.27']

            >>> parse_af(af = '9.09')
            ['9.09']

            >>> parse_af(af = 38.44)
            ['38.44']

            >>> import numpy as np
            >>> parse_af(af = np.nan)
            ['nan']

        """
        all_values = []

        # check if data is a Pandas nan value
        if not pd.isnull(af):
            # coerce to str and attempt to split
            parts = str(af).split(', ')
            # if split produced multiple parts, continue parsing
            if len(parts) > 1:
                for part in parts:
                    # attempt to split again on '='
                    values = part.split('=')
                    # separate nucleotide and af
                    allele = values[0]
                    af_val = values[1]
                    # only return the alleles with non-zero af value
                    non_zero = float(af_val) != 0.0
                    if non_zero:
                        all_values.append(part)
            else:
                all_values.append(str(af))
        else:
            all_values.append(str(af))
        # make sure everything returned is a str
        return([str(x) for x in all_values])

    def __repr__(self):
        """
        Console representation of the object
        """
        return(str(self.data))

def demo():
    """
    from interpreter.ir import IRTable
    """
    x = IRTable("../example-data/SeraSeq.tsv")
    print(x.records[0])
    print(x.records[0].genes)
    print(x.records[0].afs)
    print(x.records[0].af_str)

if __name__ == '__main__':
    demo()
