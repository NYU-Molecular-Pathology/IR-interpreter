#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for parsing Ion Reporter exported .tsv file and looking up entries in database
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
    def __init__(self, source, params = None):
        self.source = source
        self.table = self.load_table(source = self.source)
        # self.header = self.load_header(source = self.source)
        self.params = {}
        if params:
            self.params.update(params)
        if 'tumorType' in self.params:
            self.table['TumorType'] = self.params['tumorType']
        else:
            self.table['TumorType'] = None
        if 'tissueType' in self.params:
            self.table['TissueType'] = self.params['tissueType']
        else:
            self.table['TissueType'] = None
        self.records = self.get_records(data = self.table, params = self.params)

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

    def get_records(self, data, params):
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
        ir_records = [ IRRecord(data = record, **params) for record in records ]
        return(ir_records)

    def load_header(self, source, pattern = '##'):
        """
        Loads metadata from the file header.

        Parameters
        ----------
        source: str
            path to .tsv file to read in.
        pattern: str
            the string pattern which is used to denote header lines in the file

        Returns
        -------
        list
            a list of header lines from the file

        Todo
        ----
        Update this to parse the header lines into a list of dictionaries, or a single dict
        Update this to work with ``tempfile.SpooledTemporaryFile``
        """
        header_lines = []
        with open(source) as f:
            for line in f:
                if line.startswith(pattern):
                    header_lines.append(line.strip())
        return(header_lines)

    def lookup_all_interpretations(self, db):
        """
        Queries the interpretations for each record from the database.

        Parameters
        ---------
        db:
            a database object such as ``PMKB.PMKB()``
        """
        for i, _ in enumerate(self.records):
            self.records[i]._get_interpretations(db)

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

    Notes
    -----
    ``IRRecord`` objects do not have ``interpretations`` upon initialization, because an extra database connection is required. Set a record's interpretations by calling ``record._get_interpretations(conn)``
    """
    def __init__(self, data, tumorType = None, tissueType = None, variant = None):
        self.data = data
        self.tumorType = tumorType
        self.tissueType = tissueType
        self.variant = variant
        self.genes = self.parse_genes(self.data['Genes'])
        self.afs = self.parse_af(self.data['% Frequency'])
        self.af_str = ' '.join(self.afs)

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

    def parse_af(self, af_str):
        """
        Split the Percent Allele Frequency entry in the table into separate entries and only keep non-zero entries

        Parameters
        ----------
        af_str: A character string of allele frequency values from a row in the Ion Reporter .tsv table

        Returns
        -------
        list:
            a list of the non-zero allele frequency values

        Examples:
        ---------
        Example usage::

            >>> parse_af(af_str = 'AA=0.00, AG=0.00, CG=11.27, CT=0.00, GG=0.00')
            ['CG=11.27']

            >>> parse_af(af_str = '9.09')
            ['9.09']

            >>> import numpy as np
            >>> parse_af(af_str = np.nan)
            ['nan']

        """
        all_values = []

        # data is coming from Pandas df and might have nan's, otherwise will be str
        if not pd.isnull(af_str):
            parts = af_str.split(', ')
            if len(parts) > 1:
                for part in parts:
                    values = part.split('=')
                    allele = values[0]
                    af = values[1]
                    non_zero = float(af) != 0.0
                    if non_zero:
                        all_values.append(part)
            else:
                all_values.append(af_str)
        else:
            all_values.append(str(af_str))
        return(all_values)

    def _get_interpretations(self, db):
        """
        Internal method to set object's own ``interpretations`` value

        Parameters
        ----------
        db:
            a database object such as ``PMKB.PMKB()``
        """
        # sources = self.get_sources(conn)
        params = {
        'genes': self.genes,
        'tumorType': self.tumorType,
        'tissueType': self.tissueType
        }
        interpretations = db.query(params = params)
        self.interpretations = interpretations
        self.data['interpretations'] = interpretations

    def __repr__(self):
        """
        Console representation of the object
        """
        # return(str(self.__class__) + ": " + str(self.__dict__))
        return(str(self.data))

def demo(IRtable = None, PMKBdb = None):
    """
    Returns a demo IRTable object loaded table with interpretations based on the included example data and database

    Returns
    -------
    IRTable:
        ``IRTable`` object with example data
    """
    if IRtable is None:
        IRtable = "example-data/Seraseq-DNA_RNA-07252018_v1_79026a9c-e0ff-4a32-9686-ead82c35f793-2018-08-21-15-00-11200.tsv"
    if PMKBdb is None:
        PMKBdb = "db/pmkb.db"

    # load demo IR table
    table = IRTable(source = IRtable, params = {'tumorType': 'Adenocarcinoma', 'tissueType': 'Lung'})

    # get interpretations from database
    # db = pmkb.PMKB(source = PMKBdb)
    # table.lookup_all_interpretations(db = db)
    return(table)





if __name__ == '__main__':
    """
    Initialize a demo session if called directly
    """
    # IR_file = "example-data/Seraseq-DNA_RNA-07252018_v1_79026a9c-e0ff-4a32-9686-ead82c35f793-2018-08-21-15-00-11200.tsv"
    # t = IRTable(source = IR_file)
    # x = t.records[34].data['Genes']
    # t.records[34].genes # ['TMPRSS2', 'ERG']
    # t.records[19].genes # ['EGFR', 'EGFR-AS1']

    # PMKB_db = "db/pmkb.db"
    # conn = sqlite3.connect(PMKB_db)
    # t.lookup_all_interpretations(conn)
    # sources = t.records[19].get_sources(conn)
    # interpretations = t.records[19].get_interpretations(conn, sources)
    # from dev import debugger
    # debugger(globals().copy())
