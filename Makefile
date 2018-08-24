SHELL:=/bin/bash
SCRIPT_DIR:=scripts
PATH:=$(CURDIR)/conda/bin:$(SCRIPT_DIR):$(PATH)
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

test-conda:
	python -c 'import sys,pandas; print(sys.version); print(pandas.__version__)'

# ~~~~~~ Setup PMKB ~~~~~ #
DB_DIR=db
PMKB_URL:=https://pmkb.weill.cornell.edu/therapies/download.xlsx
PMKB_BASENAME:=pmkb
PMKB_DB=$(DB_DIR)/pmkb.db
PMKB_XLSX:=$(DB_DIR)/pmkb.xlsx
PMKB_TSV:=$(DB_DIR)/pmkb.tsv
PMKB_INTERPRETATIONS:=$(DB_DIR)/pmkb.interpretations.tsv
PMKB_ENTRIES:=$(DB_DIR)/pmkb.entries.csv
PMKB_TUMORFILE:=$(DB_DIR)/pmkb.tumor-terms.txt
PMKB_TISSUEFILE:=$(DB_DIR)/pmkb.tissue-terms.txt


# make sure db exists
$(DB_DIR):
	@mkdir -p "$(DB_DIR)"

# download the PMKB database file
$(PMKB_XLSX): $(DB_DIR)
	@echo ">>> Downloading clinical interpretations sheet from PMKB"
	@wget "$(PMKB_URL)" -O "$(PMKB_XLSX)"

# # dump the .xlsx file to .tsv
# $(PMKB_TSV): $(PMKB_XLSX) conda
# 	@echo ">>> Dumping .xlsx to .tsv"
# 	@dump-xlsx.py "$(PMKB_XLSX)"

# # get a list of the Tumor and Tissue terms
# $(PMKB_TUMORFILE): $(PMKB_TSV)
# 	@cut.py "$(PMKB_TSV)" -f 2 -e "utf-16" | \
# 	tr ',' '\n'| \
# 	sed -e 's|^[[:space:]]||g' -e 's|[[:space:]]$$||g' -e 's|^$$||g' | \
# 	sort -u > "$(PMKB_TUMORFILE)"

# $(PMKB_TISSUEFILE): $(PMKB_TSV)
# 	@cut.py "$(PMKB_TSV)" -f 3 -e "utf-16" | \
# 	tr ',' '\n' | \
# 	sed -e 's|^[[:space:]]||g' -e 's|[[:space:]]$$||g' -e 's|^$$||g' | \
# 	sort -u > "$(PMKB_TISSUEFILE)"

# setup-db: $(PMKB_TISSUEFILE) $(PMKB_TUMORFILE)

$(PMKB_DB) $(PMKB_ENTRIES) $(PMKB_INTERPRETATIONS) $(PMKB_TISSUEFILE) $(PMKB_TUMORFILE): $(PMKB_XLSX) conda
	pmkb.py --pmkb-xlsx "$(PMKB_XLSX)" \
	--db "$(PMKB_DB)" \
	--entries "$(PMKB_ENTRIES)" \
	--interpretations "$(PMKB_INTERPRETATIONS)" \
	--tumors "$(PMKB_TUMORFILE)" \
	--tissues "$(PMKB_TISSUEFILE)"

setup-db: $(PMKB_DB) $(PMKB_ENTRIES) $(PMKB_INTERPRETATIONS) $(PMKB_TISSUEFILE) $(PMKB_TUMORFILE)
	