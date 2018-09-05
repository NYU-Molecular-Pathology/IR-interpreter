#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
import os
import sys
from flask import render_template, request, flash
from werkzeug.utils import secure_filename
from . import app
from .. import report

dirname = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(dirname, 'uploads')
ALLOWED_EXTENSIONS = set(['tsv'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = "super secret key"
# 1MB upload limit
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
def allowed_file(filename):
    """
    Check that file is allowed; has allowed extension
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    return(render_template('index.html'))

@app.route('/upload', methods=['POST'])
def upload():
    # check if the post request has the file part
    if 'file' not in request.files:
        return('No file provided')
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return('No file provided')
    if file and not allowed_file(file.filename):
        return('Invalid file type selected; types allowed: {0}'.format(ALLOWED_EXTENSIONS))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        html = report.make_report(input = filepath, params = None, output_type = "html")
        return(html)
