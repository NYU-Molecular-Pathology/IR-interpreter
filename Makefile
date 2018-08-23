SHELL:=/bin/bash
SCRIPT_DIR:=scripts
PATH:=$(CURDIR)/conda/bin:$(PATH)
unexport PYTHONPATH
unexport PYTHONHOME

setup: conda-install setup-db

# ~~~~~ Setup Conda Python 3 ~~~~~ #
# Python 3.6.5 |Anaconda, Inc.| (default, Apr 29 2018, 16:14:56)
# [GCC 7.2.0]
CONDASH:=Miniconda3-4.5.4-Linux-x86_64.sh
CONDAURL:=https://repo.continuum.io/miniconda/$(CONDASH)
.INTERMEDIATE: $(CONDASH)
conda:
	wget "$(CONDAURL)" && \
	bash "$(CONDASH)" -b -p conda && \
	rm -f "$(CONDASH)" 

conda-install: conda
	conda install -y pandas=0.23.4 'xlrd>=0.9.0'

test:
	python -c 'import sys,pandas; print(sys.version); print(pandas.__version__)'

# ~~~~~~ Setup PMKB ~~~~~ #
DB_DIR=db
PMKB_URL:=https://pmkb.weill.cornell.edu/therapies/download.xlsx
PMKB_BASENAME:=pmkb
PMKB_XLSX:=$(DB_DIR)/$(PMKB_BASENAME).xlsx
PMKB_TSV:=$(DB_DIR)/$(PMKB_BASENAME).Interpretations.tsv

# make sure db exists
$(DB_DIR): 
	@mkdir -p "$(DB_DIR)"

# download the PMKB database file 
$(PMKB_XLSX): $(DB_DIR)
	@echo ">>> Downloading clinical interpretations sheet from PMKB"
	@wget "$(PMKB_URL)" -O "$(PMKB_XLSX)"

# dump the .xlsx file to .tsv 
$(PMKB_TSV): $(PMKB_XLSX) conda
	@echo ">>> Dumping .xlsx to .tsv"
	@python "$(SCRIPT_DIR)/dump-xlsx.py" "$(PMKB_XLSX)"

# get a list of the Tumor and Tissue terms 
PMKB_TUMORFILE:=$(DB_DIR)/$(PMKB_BASENAME)-tumor-terms.txt
PMKB_TISSUEFILE:=$(DB_DIR)/$(PMKB_BASENAME)-tissue-terms.txt
$(PMKB_TUMORFILE): $(PMKB_TSV)
	@python "$(SCRIPT_DIR)/cut.py" "$(PMKB_TSV)" -f 2 -e "utf-16" | \
	tr ',' '\n'| \
	sed -e 's|^[[:space:]]||g' -e 's|[[:space:]]$$||g' -e 's|^$$||g' | \
	sort -u > "$(PMKB_TUMORFILE)"

$(PMKB_TISSUEFILE): $(PMKB_TSV)
	@python "$(SCRIPT_DIR)/cut.py" "$(PMKB_TSV)" -f 3 -e "utf-16" | \
	tr ',' '\n' | \
	sed -e 's|^[[:space:]]||g' -e 's|[[:space:]]$$||g' -e 's|^$$||g' | \
	sort -u > "$(PMKB_TISSUEFILE)"

setup-db: $(PMKB_TISSUEFILE) $(PMKB_TUMORFILE)