[![Build Status](https://travis-ci.org/NYU-Molecular-Pathology/IR-interpreter.svg?branch=master)](https://travis-ci.org/NYU-Molecular-Pathology/IR-interpreter)

- __Demo site available [here](https://ir-interpreter.herokuapp.com/)__ (not secured for clinical usage; for demonstration purpose only!)

# IR-interpreter
Clinical interpreter for Ion Reporter and Oncomine analysis results

## Overview

The [Thermo Fisher S5](https://www.thermofisher.com/us/en/home/life-science/sequencing/next-generation-sequencing/ion-torrent-next-generation-sequencing-workflow/ion-torrent-next-generation-sequencing-run-sequence/ion-s5-ngs-targeted-sequencing.html) Next-Gen Sequencing platform can be used for the identification of structural variants, mutations, and other abnormalities in DNA and RNA samples using on-board Ion Reporter (IR) data analysis software suite. However, Ion Reporter does not include clinical interpretation of variants, which is required for clinicians to sign out cases processed on the platform.

The [Precision Medicine Knowledge Base](https://pmkb.weill.cornell.edu/) ([PMKB](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5391733/)) offers curated interpretations of many such variants which can be used for this purpose. Users can manually enter their desired variant into the PMKB website, manually look up entries in the PMKB [Excel sheet](https://pmkb.weill.cornell.edu/therapies/download.xlsx) available for download, or may use an API to query entries programmatically. While the latter option would be most ideal for a scripted solution, API usage requires the inclusion of Tumor and Tissue Type parameters, which are not always available for the program-user.

`IR-interpreter` provides an automated offline solution to this using the following method(s):

- creation of a portable SQLite database based on the PMKB Excel sheet (included)

- importation of user-exported IR .tsv formatted variant list

- matching of IR entries to PMKB entries with as many provided criteria as possible

- output of plain-text interpretations for each variant that are easy to copy/paste into systems such as PowerPath and EPIC

# Usage

## Installation

Clone this repo:

```
git clone --depth 1 https://github.com/NYU-Molecular-Pathology/IR-interpreter.git
cd IR-interpreter
```

The included `conda` recipe can install all required dependencies in a fresh conda installation in the current directory:

```
make conda-install
```

- by default, all commands invoked through the included `Makefile` use this conda installation

- configurations for macOS and Linux are supported at this step

If you would prefer to manage dependency installation yourself, you can install required libraries from the included `requirements.txt` file.

## Run Web App

You can start the web app with the Flask server with the following command:

```
make run
```

## Make a Report

You can make a report from an Ion Reporter .tsv export file with the following command:

```
interpreter/report.py /path/to/Ion_Reporter_Sample.tsv
```

By default, output will be written to a file with the same path with the extension '.html'.

### Filter by Tumor and Tissue type

You can provide a tumor or tissue type to filter interpretations by including extra arguments to the script:

```
interpreter/report.py /path/to/Ion_Reporter_Sample.tsv --tumorType "Adenocarcinoma" --tissueType "Lung"
```

An example can be run with the following command:

```
make demo
```

## Monitored Directory

`IR-interpreter` can automatically process all input .tsv files in a directory with the included `monitor.py` module:

```
interpreter/monitor.py /path/to/inputDir
```

It can also be combined with `rsync` to first copy files from a directory on a remote server, process all inputs, then copy results back. A JSON formatted config file should be used for this (example `.rsync.json` included):

```
interpreter/monitor.py /path/to/inputDir --rsync --rsync-config /path/to/rsync.json
```

### Filter by Tumor and Tissue type

You can enable interpretation filtering by tumor and tissue type by including a JSON formatted file with the same name adjacent to your input .tsv file. For example:

```
$ ls -1
Ion_Reporter_Sample.json
Ion_Reporter_Sample.tsv

$ cat Ion_Reporter_Sample.json
{
    "tumorType": "Adenocarcinoma",
    "tissueType": "Lung"
}
```

The JSON file (`Ion_Reporter_Sample.json` in this example) will be automatically detected by the monitor script and used to update filter criteria for interpretation output.

### Automation

`cron` can be used to run this feature automatically. A sample `crontab` entry can be generated with

```
make crontab
```

And will look like this:

```
0 12,23 * * * . /ifs/home/kellys04/.bash_profile; cd /ifs/production/IR-interpreter; make monitor LOG=1 >/dev/null 2>&1
```

Timestamped logs will be deposited in the `logs` subdir in this directory.

# Software

- Python 3.6+ (conda installation included for macOS and Linux)
