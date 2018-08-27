#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for parsing Ion Reporter exported .tsv file and looking up entries in database
"""
import json
import pandas as pd
import sqlite3
from collections import OrderedDict

class IRTable(object):
    """
    Class for parsing the .tsv formatted data exported from Ion Reporter web interface
    """
    def __init__(self, source):
        self.source = source
        self.table = self.load_table(source = self.source)
        self.records = self.get_records(data = self.table)
        self.header = self.load_header(source = self.source)

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
        ir_records = [ IRRecord(record) for record in records ]
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
        """
        header_lines = []
        with open(source) as f:
            for line in f:
                if line.startswith(pattern):
                    header_lines.append(line.strip())
        return(header_lines)

    def lookup_all_interpretations(self, conn):
        """
        Queries the interpretations for each record from the database.

        Parameters
        ---------
        conn:
            Connection to database object
        """
        for i, _ in enumerate(self.records):
            self.records[i]._get_interpretations(conn)

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
        y.get_genes('TMPRSS2(1) - ERG(2)')
        y.get_genes('EGFR,EGFR-AS1')

    Notes
    -----
    ``IRRecord`` objects do not have ``interpretations`` upon initialization, because an extra database connection is required. Set a record's interpretations by calling ``record._get_interpretations(conn)``
    """
    def __init__(self, data):
        self.data = data
        self.genes = self.get_genes(self.data['Genes'])

    def get_genes(self, text):
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

            get_genes('TMPRSS2(1) - ERG(2)')
            >>> ['TMPRSS2', 'ERG']
            get_genes('EGFR,EGFR-AS1')
            >>> ['EGFR', 'EGFR-AS1']
            get_genes('NRAS')
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

    def get_sources(self, conn):
        """
        Queries the PMKB database to produce a list of matching 'Source' values for the record.

        IR Record to PMKB matching logic goes here.

        Parameters
        ---------
        conn:
            Connection to database object

        Returns
        -------
        list:
            a list of values representing the 'Source' identifiers for matching entries in the database

        Notes
        -----
        Currently only matches on Gene ID's

        Todo
        ----
        Pull in match filtering based on Tissue and Tumor types, potentially IR reported variant as well.
        """
        cur = conn.cursor()
        genes = self.genes
        sql = "SELECT Source from entries where Gene in ({seq})".format(
            seq=','.join(['?']*len(genes)))
        sources = [ row[0] for row in cur.execute(sql, genes).fetchall() ]
        sources = list(set(sources))
        return(sources)

    def get_interpretations(self, conn, sources):
        """
        Queries the PMKB database interpretations table to produce a list of all interpretations for sources which were matched to the record.

        Parameters
        ----------
        conn:
            Connection to database object
        sources: list
            list of 'source' identifiers from the PMKB entries table to search for in the interpretations table

        Returns
        -------
        list:
            a list of dictionaries containing the interpretations
        """
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        sql = "SELECT * from interpretations where Source in ({seq})".format(seq=','.join(['?']*len(sources)))
        interpretations = [ dict(row) for row in cur.execute(sql, sources).fetchall() ]
        return(interpretations)

    def _get_interpretations(self, conn):
        """
        Internal method to set object's own ``interpretations`` value

        Parameters
        ----------
        conn:
            Connection to database object
        """
        sources = self.get_sources(conn)
        interpretations = self.get_interpretations(conn, sources)
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
    table = IRTable(source = IRtable)
    # get interpretations from database
    conn = sqlite3.connect(PMKBdb)
    table.lookup_all_interpretations(conn)
    return(table)





if __name__ == '__main__':
    """
    Initialize a demo session if called directly
    """
    IR_file = "example-data/Seraseq-DNA_RNA-07252018_v1_79026a9c-e0ff-4a32-9686-ead82c35f793-2018-08-21-15-00-11200.tsv"
    t = IRTable(source = IR_file)
    # x = t.records[34].data['Genes']
    # t.records[34].genes # ['TMPRSS2', 'ERG']
    # t.records[19].genes # ['EGFR', 'EGFR-AS1']

    PMKB_db = "db/pmkb.db"
    conn = sqlite3.connect(PMKB_db)
    t.lookup_all_interpretations(conn)
    # sources = t.records[19].get_sources(conn)
    # interpretations = t.records[19].get_interpretations(conn, sources)
    # from dev import debugger
    # debugger(globals().copy())
