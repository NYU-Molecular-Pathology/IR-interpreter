SHELL:=/bin/bash
UNAME:=$(shell uname)

# ~~~~~ Setup Conda ~~~~~ #
PATH:=$(CURDIR)/conda/bin:$(PATH)
unexport PYTHONPATH
unexport PYTHONHOME

# install versions of conda for Mac or Linux
ifeq ($(UNAME), Darwin)
CONDASH:=Miniconda3-4.5.4-MacOSX-x86_64.sh
endif

ifeq ($(UNAME), Linux)
CONDASH:=Miniconda3-4.5.4-Linux-x86_64.sh
endif

CONDAURL:=https://repo.continuum.io/miniconda/$(CONDASH)
conda:
	@echo ">>> Setting up conda..."
	@wget "$(CONDAURL)" && \
	bash "$(CONDASH)" -b -p conda && \
	rm -f "$(CONDASH)"

conda-install: conda
	conda install -y django=2.1.2 pandas=0.23.4 'xlrd>=0.9.0'

# ~~~~~ SETUP DJANGO APP ~~~~~ #
# create the app for development
# start:
# 	django-admin startproject webapp .
# 	python manage.py startapp interpreter

# initialize app databases for the first time
init:
	python manage.py makemigrations
	python manage.py migrate
	python manage.py migrate interpreter --database=interpreter_db
	python manage.py migrate interpreter --database=pmkb_db
	python manage.py createsuperuser

# import data from PMKB .xlsx into database
import:
	python interpreter/importer.py

# ~~~~~ RUN ~~~~~ #
export DB_DIR:=db
export DJANGO_DB:=db.sqlite3
export PMKB_DB:=pmkb.sqlite3
export INTERPRETER_DB:=interpreter.sqlite3

# runs the web server
runserver:
	python manage.py runserver

# start interactive shell
shell:
	python manage.py shell

# requires full PMKB database import to work...
test:
	python manage.py test

test1:
	python -c 'from interpreter.ir import IRTable ; \
	x = IRTable("example-data/SeraSeq.tsv") ; \
	print(x.records[0]) ; \
	print(x.records[0].genes) ; \
	print(x.records[0].afs) ; \
	print(x.records[0].af_str) ; \
	'

test-report:
	interpreter/report.py "example-data/SeraSeq.tsv"
	python -c 'import interpreter.report as report; \
	report_html = report.make_report_html(input = "example-data/SeraSeq.tsv") ; \
	# print(report_html) \
	'
	interpreter/report.py "example-data/SeraSeq.tsv" > report.html

test-interpret:
	python -c 'import interpreter.interpret'
	interpreter/interpret.py "example-data/SeraSeq.tsv"

# ~~~~~ RESET ~~~~~ #
# re-initialize just the databases
reinit: nuke
	python manage.py makemigrations
	python manage.py migrate
	python manage.py migrate interpreter --database=interpreter_db
	python manage.py migrate interpreter --database=pmkb_db

# destroy app database
nuke:
	@echo ">>> Removing database items:"; \
	rm -rfv interpreter/migrations/__pycache__ && \
	rm -fv interpreter/migrations/0*.py && \
	rm -fv "$$(python -c 'import os; print(os.path.join("$(DB_DIR)", "$(INTERPRETER_DB)"))')" && \
	rm -fv "$$(python -c 'import os; print(os.path.join("$(DB_DIR)", "$(PMKB_DB)"))')"

# delete the main Django database as well..
nuke-all: nuke
	rm -fv "$$(python -c 'import os; print(os.path.join("$(DB_DIR)", "$(DJANGO_DB)"))')"
