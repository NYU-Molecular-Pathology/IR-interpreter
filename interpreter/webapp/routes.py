#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
import os
import sys
import subprocess
from flask import render_template, request, flash
from werkzeug.utils import secure_filename
from . import app
from .. import report
from .. import pmkb

# ~~~~~ ROUTE CONFIGS ~~~~~ #
# dirname = os.path.dirname(__file__)
# UPLOAD_FOLDER = os.path.join(dirname, 'uploads')
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app_version = None
try:
    app_version = subprocess.check_output(['git', 'describe', '--always']).decode('ascii').strip()
except:
    pass

ALLOWED_EXTENSIONS = set(['tsv'])
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = "super secret key"

# 1MB upload limit
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
def allowed_file(filename):
    """
    Check that file is allowed; has allowed extension
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = pmkb.PMKB()
tissueTypes = db.get_tissueTypes()
tumorTypes = db.get_tumorTypes()

# ~~~~~ ROUTES ~~~~~ #
@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    return(render_template('index.html', tissueTypes = tissueTypes, tumorTypes = tumorTypes, version = app_version))

@app.route('/upload', methods=['POST'])
def upload():
    # validate the params provided & get tumor and tissue types from the form
    req_tissueType = None
    req_tumorType = None
    if 'tissueType' in request.form:
        if request.form['tissueType'] in tissueTypes:
            req_tissueType = request.form['tissueType']
    if 'tumorType' in request.form:
        if request.form['tumorType'] in tumorTypes:
            req_tumorType = request.form['tumorType']

    # set up params for db query
    req_params = {
    'tissueType': req_tissueType,
    'tumorType': req_tumorType
    }

    # check if the post request has the file part
    if 'file' not in request.files:
        return('No file provided')
    file = request.files['file']
    # if user does not select file, browser also can submit an empty part without filename
    if file.filename == '':
        return('No file provided')
    # check for invalid filetype
    if file and not allowed_file(file.filename):
        return('Invalid file type selected; types allowed: {0}'.format(ALLOWED_EXTENSIONS))
    if file and allowed_file(file.filename):
        # # writing file to temp location on disk
        # filename = secure_filename(file.filename)
        # filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # file.save(filepath)
        # html = report.make_report(input = filepath, params = None, output_type = "html")

        # operating on in-memory file only
        try:
            html = report.make_report(input = file.stream._file, output = False, params = req_params, output_type = "html")
            return(html)
        except:
            print("Upload file could not be parsed")
            return("Upload file could not be parsed")
        finally:
            file.stream._file.close()
