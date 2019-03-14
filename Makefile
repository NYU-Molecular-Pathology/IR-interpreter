SHELL:=/bin/bash
UNAME:=$(shell uname)

# app locations and configs
export LOG_DIR:=logs
export DB_DIR:=db
export DJANGO_DB:=db.sqlite3
export INTERPRETER_DB:=interpreter.sqlite3
export SECRET_KEY_FILE:=$(HOME)/.ir-interpreter.txt
export SECRET_KEY="$(shell head -1 "$(SECRET_KEY_FILE)")"
TIMESTAMP:=$(shell date '+%Y-%m-%d-%H-%M-%S')
DB_BACKUP_DIR:=$(DB_DIR)/backup
DB_BACKUP_PATH:=$(DB_BACKUP_DIR)/$(TIMESTAMP)
DJANGO_DB_PATH:=$(DB_DIR)/$(DJANGO_DB)
INTERPRETER_DB_PATH:=$(DB_DIR)/$(INTERPRETER_DB)

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
	conda install -y django=2.1.2 \
	pandas=0.23.4 \
	'xlrd>=0.9.0'
	pip install django-ipware==2.1.0

# ~~~~~ SETUP DJANGO APP ~~~~~ #
# create the app for development
# start:
# 	django-admin startproject webapp .
# 	python manage.py startapp interpreter

# make  sure db dir exists
$(DB_DIR):
	mkdir -p "$(DB_DIR)"

# create secret key file
$(SECRET_KEY_FILE):
	python manage.py shell -c 'from django.core.management import utils; print(utils.get_random_secret_key())' > "$(SECRET_KEY_FILE)"
secret-key: $(SECRET_KEY_FILE)

# initialize app databases for the first time
init: secret-key $(DB_DIR)
	python manage.py makemigrations
	python manage.py migrate
	python manage.py migrate interpreter --database=interpreter_db
	python manage.py createsuperuser

# import data from PMKB .xlsx into database
import:
	python interpreter/importer.py --type tumor_type
	python interpreter/importer.py --type tissue_type
	python interpreter/importer.py --type nyu_tier
	python interpreter/importer.py --type PMKB

DJANGO_DB_BACKUP_SQL:=$(DB_BACKUP_PATH)/db.sql.gz
DJANGO_DB_BACKUP_JSON:=$(DB_BACKUP_PATH)/db.json.gz
INTERPRETER_DB_BACKUP_SQL:=$(DB_BACKUP_PATH)/interpreter.sql.gz
INTERPRETER_DB_BACKUP_JSON:=$(DB_BACKUP_PATH)/interpreter.json.gz
backup:
	mkdir -p "$(DB_BACKUP_PATH)" && \
	sqlite3 "$(DJANGO_DB_PATH)" '.dump' | gzip > "$(DJANGO_DB_BACKUP_SQL)" && \
	sqlite3 "$(INTERPRETER_DB_PATH)" '.dump' | gzip > "$(INTERPRETER_DB_BACKUP_SQL)" && \
	python manage.py dumpdata --indent 4 --traceback | gzip > "$(DJANGO_DB_BACKUP_JSON)" && \
	python manage.py dumpdata --database=interpreter_db interpreter --indent 4 --traceback | gzip > "$(INTERPRETER_DB_BACKUP_JSON)"

# ~~~~~ RUN ~~~~~ #
# runs the web server
runserver:
	python manage.py runserver

# start interactive shell
shell:
	python manage.py shell

# run arbitrary user-passed command
CMD:=
cmd:
	$(CMD)

# run the app's test suite
test:
	python manage.py test

# test report output
test-report:
	interpreter/report.py "interpreter/fixtures/SeraSeq.tsv" > report.html

# test variant interpretation
test-interpret:
	python -c 'import interpreter.interpret'
	interpreter/interpret.py "interpreter/fixtures/SeraSeq.tsv"

# write the unique tumor and tissue types to JSON files in the current directory from the PMKB file
get-pmkb-tumor-tissue-types:
	interpreter/scripts/get_pmkb_tissue_tumor_types.py

# ~~~~~ RESET ~~~~~ #
# re-initialize just the databases
reinit: nuke
	python manage.py makemigrations
	python manage.py migrate
	python manage.py migrate interpreter --database=interpreter_db

# destroy app database
nuke:
	@echo ">>> Removing database items:"; \
	rm -rfv interpreter/migrations/__pycache__ && \
	rm -fv interpreter/migrations/0*.py && \
	rm -fv "$$(python -c 'import os; print(os.path.join("$(DB_DIR)", "$(INTERPRETER_DB)"))')"

# delete the main Django database as well..
nuke-all: nuke
	rm -fv "$$(python -c 'import os; print(os.path.join("$(DB_DIR)", "$(DJANGO_DB)"))')"
