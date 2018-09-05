#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for handling the PMKB database
"""
import sqlite3
import pandas as pd

class PMKB(object):
    """
    Class for handling the PMKB database
    """
    def __init__(self, source = "db/pmkb.db"):
        self.source = source
        self.conn = sqlite3.connect(self.source)
        self.conn.row_factory = sqlite3.Row

    def query(self, params):
        """
        Submits a query for the PMKB database

        Parameters
        ----------
        params: dict
            a dictionary of fields for querying. Must include key 'genes' with a list of gene IDs to match


        Returns
        -------
        list
            a list of dictionaries containing the interpretations retrieved from the database

        Examples
        --------
        Example usage::
            genes = ['NRAS']; tumorType = 'Urothelial Carcinoma'; tissueType = 'Kidney'
            params = {'genes': genes, 'tumorType': tumorType, 'tissueType': tissueType}
            i = p.query(params = params)

        """
        genes = params.pop('genes')

        # get all the matches on gene
        df = self.get_gene_matches(genes = genes)

        # apply other filters
        df = self.filter_matches(params = params, df = df)

        # get list of Source interpretations to use
        sources = list(set(df['Source'].tolist()))

        # get the interpretations
        interpretations = self.get_interpretations(sources = sources)

        return(interpretations)

    def filter_matches(self, params, df):
        """
        Filters database for matches based on criteria provided

        Parameters
        ----------
        params: dict
            dictionary of of fields for matching against
        df: pandas.dataframe
            a dataframe of matches that were queried from the database

        Returns
        -------
        pandas.dataframe
            a subset dataframe with only the matching entries
        """
        tumorType = params.pop('tumorType', None)
        tissueType = params.pop('tissueType', None)
        variant = params.pop('variant', None)

        # filter provided criteria
        if tumorType:
            df = df[df['TumorType'] == tumorType]
        if tissueType:
            df = df[df['TissueType'] == tissueType]
        if variant:
            df = df[df['Variant'] == variant]

        return(df)

    def get_gene_matches(self, genes):
        """
        Queries the PMKB database to produce a list of matching 'Source' values for the provided genes.

        IR Record to PMKB matching logic goes here.

        Parameters
        ---------
        genes:
            List of gene identifiers (str)

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
        cur = self.conn.cursor()
        sql = "SELECT * from entries where Gene in ({seq})".format(seq=','.join(['?']*len(genes)))
        # get results as a list of dicts
        res = [ dict(row) for row in cur.execute(sql, genes).fetchall() ]
        # check for empty results
        if len(res) < 1:
            # get the first row of the table
            sql = 'SELECT * FROM entries'
            d = cur.execute(sql).fetchone()
            # make empty dataframe
            df = pd.DataFrame(columns = d.keys())
        else:
            # convert list of dicts to dataframe
            df = pd.DataFrame(res).drop_duplicates()
        return(df)

    def get_interpretations(self, sources):
        """
        Queries the PMKB database interpretations table to produce a list of all interpretations for sources provided.

        Parameters
        ----------
        sources: list
            list of 'source' identifiers from the PMKB entries table to search for in the interpretations table

        Returns
        -------
        list:
            a list of dictionaries containing the interpretations
        """
        cur = self.conn.cursor()
        sql = "SELECT * from interpretations where Source in ({seq})".format(seq=','.join(['?']*len(sources)))
        interpretations = [ dict(row) for row in cur.execute(sql, sources).fetchall() ]
        return(interpretations)

    def get_tumorTypes(self):
        """
        Returns a list of the Tumor Types in the database

        Returns
        -------
        list
            a list of character strings representing tumor types in the database
        """
        cur = self.conn.cursor()
        sql = "SELECT DISTINCT TumorType FROM entries"
        tumorTypes = list(set([ dict(row)['TumorType'] for row in cur.execute(sql).fetchall() ]))
        tumorTypes.sort()
        return(tumorTypes)

    def get_tissueTypes(self):
        """
        Returns a list of the Tissue Types in the database

        Returns
        -------
        list
            a list of character strings representing tissue types in the database
        """
        cur = self.conn.cursor()
        sql = "SELECT DISTINCT TissueType FROM entries"
        tissueTypes = list(set([ dict(row)['TissueType'] for row in cur.execute(sql).fetchall() ]))
        tissueTypes.sort()
        return(tissueTypes)

def demo():
    """
    A demo of the database API functionality.

    Returns
    -------
    tuple
        a tuple in the format ``(PMKB_object, interpretations)``

    Usage

    """
    p = PMKB()
    genes = ['EGFR', 'NRAS']
    tumorType = 'Urothelial Carcinoma'
    tissueType = 'Kidney'
    params = {'genes': genes, 'tumorType': tumorType, 'tissueType': tissueType}
    # params = {'genes': genes, 'tumorType': 'Urothelial Carcinoma', 'tissueType': None}
    i = p.query(params)
    return((p, i))

if __name__ == '__main__':
    """
    Initialize a demo session if called directly
    """
    p, i = demo()
    from dev import debugger
    debugger(globals().copy())
