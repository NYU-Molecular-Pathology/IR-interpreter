# IR-interpreter

Clinical interpreter for Ion Reporter and Oncomine analysis results, to assist clinicians with reporting on patient cases. 

## Overview

The [Thermo Fisher S5](https://www.thermofisher.com/us/en/home/life-science/sequencing/next-generation-sequencing/ion-torrent-next-generation-sequencing-workflow/ion-torrent-next-generation-sequencing-run-sequence/ion-s5-ngs-targeted-sequencing.html) Next-Gen Sequencing platform can be used for the identification of structural variants, mutations, and other abnormalities in DNA and RNA samples using on-board Ion Reporter (IR) data analysis software suite. However, Ion Reporter does not include clinical interpretation of variants, which is required for clinicians to create customized reports on patient cases processed on the platform.

The [Precision Medicine Knowledge Base](https://pmkb.weill.cornell.edu/) ([PMKB](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5391733/)) offers curated interpretations of many such variants which can be used for this purpose. Users can manually enter their desired variant into the PMKB website, manually look up entries in the PMKB [Excel sheet](https://pmkb.weill.cornell.edu/therapies/download.xlsx) available for download, or may use an API to query entries programmatically. While the latter option would be most ideal for a scripted solution, API usage requires the inclusion of Tumor and Tissue Type parameters, which are not always available for the program-user.

Clinicians at NYU have also begun to compile their own sets of interpretations and tiers of clinically relevant variants, for use with sign-out of cases using the S5 system. 

IR-intepreter combines a pre-saved version of the PMKB database along with custom NYU variant interpretations in order to match clinical interpretations with user-provided variants exported from the Ion Reporter in .tsv format ([example here](https://github.com/NYU-Molecular-Pathology/IR-interpreter/blob/master/interpreter/fixtures/SeraSeq.tsv)). IR-intepreter presents a web application where users can upload their .tsv formatted variant export file and find interpretations for each variant, matched on gene, tissue type, and tumor type. 

<img width="800" alt="Screen Shot 2019-03-24 at 11 18 09 PM" src="https://user-images.githubusercontent.com/10505524/54893222-28984800-4e8b-11e9-9553-f8a250eee3db.png">

# Usage

## Installation

Clone this repo:

```
git clone https://github.com/NYU-Molecular-Pathology/IR-interpreter
cd IR-interpreter
```

Install app:

```
make install
```

This will:

- install all dependencies in the app's directory with conda

- initialize the app databases, prompting for the creation of an admin account

- import database entries from the included fixtures into the database (SQLite)

- copy over static files for web hosting

## Run App

The development server can be run locally for testing purposes:

```
make runserver
```

This will start the app in the Django server. 

### Deployment

For production deployment, instead use this:

```
make deploy GUNICORN_CONFIG=/path/to/gunicorn_config.py
```

This will start a gunicorn server based on the supplied configuration file (an example is included in this repo at `conf/example/gunicorn_config.py`). The gunicorn server can be stopped with `make kill`. The included configuration will utilize a Unix socket in the app directory, which can be used with a web server such as nginx to serve the app on your network. 

# Software

- Python 3.6 (conda installation included for macOS and Linux)

- SQLite

- Django 2.1.5

- gunicorn

- GNU make

An older version of the app based on Flask can be found here: https://github.com/NYU-Molecular-Pathology/IR-interpreter-flask. This version includes extra offline features such as CLI reporting and rsync across servers. 
