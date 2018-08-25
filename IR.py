#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for parsing Ion Reporter exported .tsv file and looking up entries in database
"""
import json
import pandas as pd
from dev import debugger
import sqlite3

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
        Load the contents of the .tsv file into a dataframe
        """
        df = pd.read_csv(source, sep = '\t', comment = '#')
        return(df)

    def get_records(self, data):
        """
        Create a list of IRRecord objects for each entry in the table
        """
        records = [ IRRecord(record) for record in data.to_dict(orient='records') ]
        return(records)

    def load_header(self, source, pattern = '##'):
        """
        Load metadata from the file header
        """
        header_lines = []
        with open(source) as f:
            for line in f:
                if line.startswith(pattern):
                    header_lines.append(line.strip())
        return(header_lines)

    def lookup_all_interpretations(self, conn):
        """
        Query the interpretations for each record from the database
        """
        for i, _ in enumerate(self.records):
            sources = self.records[i].get_sources(conn)
            self.records[i].interpretations = self.records[i].get_interpretations(conn, sources)

class IRRecord(object):
    """
    An entry in the variant table output by Ion Reporter exporter

    y = IRRecord(data = '')
    y.get_genes('TMPRSS2(1) - ERG(2)')
    y.get_genes('EGFR,EGFR-AS1')
    """
    def __init__(self, data):
        self.data = data
        self.genes = self.get_genes(self.data['Genes'])

    def get_genes(self, text):
        """
        Parse the 'Genes' field in each entry
        """
        genes = set()
        # split fusions apart and remove number in parenthesis
        if len(text.split(' - ')) > 1:
            genes.update([ gene.split('(')[0] for gene in text.split(' - ') ])
        # split all other entries on comma
        if len(text.split(',')) > 1:
            genes.update([ gene for gene in text.split(',') ])
        return(list(genes))

    def get_sources(self, conn):
        """
        Query the database to produce a list of 'Source' values for each gene in the record
        """
        cur = conn.cursor()
        genes = self.genes
        sql = "SELECT Source from entries where Gene in ({seq})".format(
            seq=','.join(['?']*len(genes)))
        sources = [ row[0] for row in cur.execute(sql, genes).fetchall() ]
        return(sources)

    def get_interpretations(self, conn, sources):
        """
        Query the database to produce a list of all interpretations for sources
        """
        cur = conn.cursor()
        sql = "SELECT Interpretation, Citation from interpretations where Source in ({seq})".format(
            seq=','.join(['?']*len(sources)))
        interpretations = [ {'Interpretation': i, 'Citation': c} for i, c in cur.execute(sql, sources).fetchall() ]
        return(interpretations)

    def __repr__(self):
        # return(str(self.__class__) + ": " + str(self.__dict__))
        return(str(self.data))




if __name__ == '__main__':
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
    debugger(globals().copy())
