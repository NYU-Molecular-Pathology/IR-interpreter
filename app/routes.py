#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
import os
import sys
from flask import render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from app import app

# import the IR interpreter library from parent repo dir
# scriptdir = os.path.dirname(os.path.realpath(__file__)) # this script's dir
# parentdir = os.path.dirname(scriptdir) # this script's parent dir
# sys.path.insert(0, parentdir)
# import interpreter
# sys.path.pop(0)
# print(interpreter.__file__)
# print(interpreter.__package__)
# print(dir(interpreter.report))

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
    user = {'username': 'Miguel'}
    return(render_template('index.html', title = 'Home', user = user))

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        print(request)
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
        file = request.files['file']
        print(file)
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
        if file and not allowed_file(file.filename):
            flash('Invalid file type selected')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(filepath)
            file.save(filepath)
            # html = interpreter.report.make_report(input = filepath, params = None, output_type = "html")
            # return(html)
