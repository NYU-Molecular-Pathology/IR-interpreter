SHELL:=/bin/bash
SCRIPT_DIR:=scripts
PATH:=$(CURDIR)/conda/bin:$(SCRIPT_DIR):$(PATH)
unexport PYTHONPATH
unexport PYTHONHOME

setup: conda-install setup-db
.PHONY: setup

# ~~~~~ Setup Conda Python 3 ~~~~~ #
# Python 3.6.5 |Anaconda, Inc.| (default, Apr 29 2018, 16:14:56)
# [GCC 7.2.0]
CONDASH:=Miniconda3-4.5.4-Linux-x86_64.sh
CONDAURL:=https://repo.continuum.io/miniconda/$(CONDASH)
conda:
	@echo ">>> Setting up conda..."
	@wget "$(CONDAURL)" && \
	bash "$(CONDASH)" -b -p conda && \
	rm -f "$(CONDASH)"

conda-search: conda
	conda search '*jinja*'

conda-install: conda
	conda install -y pandas=0.23.4 'xlrd>=0.9.0' jinja2=2.10

test-conda:
	python -c 'import sys,pandas; print(sys.version); print(pandas.__version__)'

# ~~~~~~ Setup PMKB database ~~~~~ #
DB_DIR=db
PMKB_URL:=https://pmkb.weill.cornell.edu/therapies/download.xlsx
PMKB_DB=$(DB_DIR)/pmkb.db
PMKB_XLSX:=$(DB_DIR)/pmkb.xlsx
PMKB_INTERPRETATIONS:=$(DB_DIR)/pmkb.interpretations.tsv
PMKB_ENTRIES:=$(DB_DIR)/pmkb.entries.csv
PMKB_TUMORFILE:=$(DB_DIR)/pmkb.tumor-terms.txt
PMKB_TISSUEFILE:=$(DB_DIR)/pmkb.tissue-terms.txt

# download the PMKB database file
$(PMKB_XLSX):
	@echo ">>> Downloading clinical interpretations sheet from PMKB..."
	@wget "$(PMKB_URL)" -O "$(PMKB_XLSX)"

$(PMKB_DB): $(PMKB_XLSX) conda
	@echo ">>> Generating PMKB database..."
	@pmkb2db.py --pmkb-xlsx "$(PMKB_XLSX)" \
	--db "$(PMKB_DB)"

$(PMKB_ENTRIES): $(PMKB_XLSX) conda
	@echo ">>> Generating PMKB entries..."
	@pmkb2db.py --pmkb-xlsx "$(PMKB_XLSX)" \
	--entries "$(PMKB_ENTRIES)"

$(PMKB_INTERPRETATIONS): $(PMKB_XLSX) conda
	@echo ">>> Generating PMKB interpretations..."
	@pmkb2db.py --pmkb-xlsx "$(PMKB_XLSX)" \
	--interpretations "$(PMKB_INTERPRETATIONS)"

$(PMKB_TISSUEFILE):
	@echo ">>> Generating PMKB tissue entries..."
	@pmkb2db.py --pmkb-xlsx "$(PMKB_XLSX)" \
	--db "$(PMKB_DB)" \
	--tumors "$(PMKB_TISSUEFILE)"

$(PMKB_TUMORFILE): $(PMKB_XLSX) conda
	@echo ">>> Generating PMKB tumor entries..."
	@pmkb2db.py --pmkb-xlsx "$(PMKB_XLSX)" \
	--db "$(PMKB_DB)" \
	--tissues "$(PMKB_TUMORFILE)"

setup-db: $(PMKB_DB) $(PMKB_ENTRIES) $(PMKB_INTERPRETATIONS) $(PMKB_TISSUEFILE) $(PMKB_TUMORFILE)
.PHONY: setup-db

# ~~~~~ ~~~~~ ~~~~~ #
# run the unit test suite
test:
	app/test.py

# run a demo for example report output
demo:
	# app/IR.py
	app/template.py

# enter debug console
# t.records[0].interpretations[0]
# t.records[0].interpretations[0].keys()
debug:
	python -c 'from app.dev import debugger; from app.IR import demo; t = demo(); debugger(globals().copy())'
