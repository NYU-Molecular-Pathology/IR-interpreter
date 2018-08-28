[![Build Status](https://travis-ci.org/NYU-Molecular-Pathology/IR-interpreter.svg?branch=master)](https://travis-ci.org/NYU-Molecular-Pathology/IR-interpreter)

# IR-interpreter
Clinical interpreter for Ion Reporter and Oncomine analysis results 

## Overview

The [Thermo Fisher S5](https://www.thermofisher.com/us/en/home/life-science/sequencing/next-generation-sequencing/ion-torrent-next-generation-sequencing-workflow/ion-torrent-next-generation-sequencing-run-sequence/ion-s5-ngs-targeted-sequencing.html) Next-Gen Sequencing platform can be used for the identification of structural variants, mutations, and other abnormalities in DNA and RNA samples using on-board Ion Reporter (IR) data analysis software suite. However, Ion Reporter does not include clinical interpretation of variants, which is required for clinicians to sign out patient cases processed on the platform. 

The [Precision Medicine Knowledge Base](https://pmkb.weill.cornell.edu/) ([PMKB](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5391733/)) offers curated interpretations of many such variants which can be used for this purpose. Users can manually enter their desired variant into the PMKB website, manually look up entries in the PMKB [Excel sheet](https://pmkb.weill.cornell.edu/therapies/download.xlsx) available for download, or may use an API to query entries programmatically. While the latter option would be most ideal for a scripted solution, API usage requires the inclusion of Tumor and Tissue Type parameters, which are not always available for the program-user. 

An offline solution the automation of the clinical interpretation of IR results was desired. `IR-interpreter` attempts to solve this through to following method(s):

- creation of a portable SQLite database based on the PMKB Excel sheet (included)

- importation of user-exported IR .tsv formatted variant list

- matching of IR entries to PMKB entries with as many provided criteria as possible

- output of plain-text interpretations for each variant that are easy to copy/paste into systems such as PowerPath and EPIC

# Software

- Python 3.6+
