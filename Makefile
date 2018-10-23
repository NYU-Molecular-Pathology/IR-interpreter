SHELL:=/bin/bash
UNAME:=$(shell uname)
SCRIPT_DIR:=scripts
PATH:=$(CURDIR)/conda/bin:$(SCRIPT_DIR):$(PATH)
unexport PYTHONPATH
unexport PYTHONHOME

setup: conda-install setup-db
.PHONY: setup

# ~~~~~ Setup Conda Python 3 ~~~~~ #
# Python 3.6.5 |Anaconda, Inc.| (default, Apr 29 2018, 16:14:56)
# [GCC 7.2.0]
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

conda-search: conda
	conda search '*flask*'

conda-install: conda
	conda install -y pandas=0.23.4 'xlrd>=0.9.0' jinja2=2.10 flask=1.0.2

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

# ~~~~~ RUN PROGRAM ~~~~~ #
TIMESTAMP:=$(shell date +"%Y-%m-%d-%H-%M-%S")
LOGDIR=logs
LOGGING:=
# run the unit test suite
test:
	interpreter/test.py

# run a demo for example report output
demo:
	# interpreter/IR.py
	interpreter/report.py example-data/Seraseq-DNA_RNA-07252018_v1_79026a9c-e0ff-4a32-9686-ead82c35f793-2018-08-21-15-00-11200.tsv --tumorType "Adenocarcinoma" --tissueType "Lung"

# enter CLI debugger
debug:
	python -c 'import interpreter.pmkb as pmkb; import interpreter.ir as ir; import interpreter.dev as dev; p, i = pmkb.demo(); t = ir.demo(); dev.debugger(globals().copy())'

# Adenocarcinoma
# Lung
# enter debug console
# t.records[0].interpretations[0]
# t.records[5].interpretations
# t.records[0].interpretations[0].keys()
# p.get_sources(genes = ['NRAS'])
# genes = ['NRAS', 'EGFR']
# p.get_gene_sources(genes)
# t.lookup_all_interpretations(db = p)
# python -c 'from app.dev import debugger; from app.IR import demo; t = demo(); debugger(globals().copy())'
# python -c 'from app.dev import debugger; from app.PMKB import demo; p, i = demo(); debugger(globals().copy())'
# python -c 'import sys; import app; print(sys.modules); p, i = app.PMKB.demo(); t = app.IR.demo(); app.dev.debugger(globals().copy())'
# python -c 'import sys; import app; print(sys.modules); print(dir(app))'

# directory monitor script
RSYNC_CONFIG:=/ifs/data/molecpathlab/private_data/IR-interpreter-rsync.json
MONITOR_DIR:=/ifs/data/molecpathlab/production/IonReporter-interpretations
EP:=--rsync --rsync-config "$(RSYNC_CONFIG)" --overwrite
monitor:
	@if [ -z "$(LOGGING)" ]; then \
	interpreter/monitor.py "$(MONITOR_DIR)" $(EP) ; \
	else mkdir -p "./$(LOGDIR)"; \
	logfile="./$(LOGDIR)/monitor.$(TIMESTAMP).log" ; \
	interpreter/monitor.py "$(MONITOR_DIR)" $(EP) 2>&1 > "$${logfile}" ; \
	fi
# interpreter/monitor.py "$(MONITOR_DIR)" --rsync --rsync-config "$(RSYNC_CONFIG)" --overwrite --remove-source

# make crontab entry
# “At minute 0 past hour 12 and 23.” e.g. 12:00, 23:00 # https://crontab.guru/
CRONINTERVAL:=0 12,23 * * *
CRONCMD:=. $(shell echo $$HOME)/.bash_profile; cd $(shell pwd); make monitor LOGGING=1 >/dev/null 2>&1
crontab:
	@echo "$(CRONINTERVAL) $(CRONCMD)"

# run the Flask app
# for Click compatibility with Python3...
ifeq ($(UNAME), Darwin)
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
endif
ifeq ($(UNAME), Linux)
# export LC_ALL=C.UTF-8
# export LANG=C.UTF-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
endif
run:
	which python
	export FLASK_APP="interpreter/webapp" ; \
	export FLASK_ENV=development ; \
	flask run

# deploy the app on production server
PORT:=
IP:=
check-port:
	@[ -z "$(PORT)" ] && echo ">>> No PORT passed, exiting..." && exit 1 || :
check-ip:
	@[ -z "$(PORT)" ] && echo ">>> No PORT passed, exiting..." && exit 1 || :
deploy:
	@$(MAKE) check-port
	@$(MAKE) check-ip
	mkdir -p "./$(LOGDIR)" ; \
	logfile="./$(LOGDIR)/app.$(TIMESTAMP).log" ; \
	export FLASK_APP="interpreter/webapp" ; \
	flask run --port="$(PORT)" --host="$(IP)" 2>&1 > "$${logfile}" & appProcess="$$!" ; \
	echo ">>> Running app on port $(PORT), process ID $${appProcess}, logging to $${logfile}" 
# ;\
# wait $${appProcess}





