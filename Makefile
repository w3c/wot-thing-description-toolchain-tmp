MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.SUFFIXES:
.SECONDARY:

RUN = poetry run
LINKML_SCHEMA_NAME=thing_description_schema
SCHEMA_NAME = $(LINKML_SCHEMA_NAME)
SOURCE_SCHEMA_PATH = resources/thing_description_schema.yaml
SOURCE_SCHEMA_DIR = $(dir $(SOURCE_SCHEMA_PATH))
SRC = src
DEST = resources/gens
PYMODEL= $(DEST)/datamodel
DOCDIR = $(DEST)/docs
EXAMPLEDIR = examples
TEMPLATE_DIR = resources/templates
LINKML_GENERATORS_CONFIG_YAML= --config-file src/linkml/config.yaml


$(DEST):
	mkdir -p $@

CONFIG_YAML =
ifdef LINKML_GENERATORS_CONFIG_YAML
CONFIG_YAML = ${LINKML_GENERATORS_CONFIG_YAML}
endif

GEN_DOC_ARGS =
ifdef LINKML_GENERATORS_DOC_ARGS
GEN_DOC_ARGS = ${GEN_DOC_ARGS}
endif

GEN_OWL_ARGS =
ifdef LINKML_GENERATORS_OWL_ARGS
GEN_OWL_ARGS = ${GEN_OWL_ARGS}
endif

GEN_TS_ARGS =
ifdef LINKML_GENERATORS_TYPESCRIPT_ARGS
GEN_TS_ARGS = ${GEN_TS_ARGS}
endif

.PHONY: all clean setup gen-project gen-examples gendoc

help: status
	@echo ""
	@echo "make setup -- initial setup (run this first)"
	@echo "make site -- makes site locally"
	@echo "make install -- install dependencies"
	@echo "make test -- runs tests"
	@echo "make testdoc -- builds docs and runs local test server"
	@echo "make deploy -- deploys site"
	@echo "make update -- updates linkml version"
	@echo "make help -- show this help"
	@echo ""


status: check-config
	@echo "Project: $(SCHEMA_NAME)"
	@echo "Source: $(SOURCE_SCHEMA_PATH)"

setup: check-config install gen-project gen-examples gendoc


check-config:
ifndef LINKML_SCHEMA_NAME
	$(error **Project not configured**:\n\n)
else
	$(info Ok)
endif


install:
	poetry install
.PHONY: install


update: update-linkml

update-linkml:
	poetry add -D linkml@latest

all: site
site: gen-project gendoc
%.yaml: gen-project
deploy: all mkd-gh-deploy


gen-project: $(DEST)
	$(RUN) gen-project ${CONFIG_YAML} -d $(DEST) $(SOURCE_SCHEMA_PATH) --exclude excel && mv $(DEST)/*.py $(PYMODEL)

ifneq ($(strip ${GEN_OWL_ARGS}),)
	mkdir -p ${DEST}/owl || true
	$(RUN) gen-owl ${GEN_OWL_ARGS} $(SOURCE_SCHEMA_PATH) >${DEST}/owl/${SCHEMA_NAME}.owl.ttl
endif

ifneq ($(strip ${GEN_TS_ARGS}),)
	mkdir -p ${DEST}/typescript || true
	$(RUN) gen-typescript ${GEN_TS_ARGS} $(SOURCE_SCHEMA_PATH) >${DEST}/typescript/${SCHEMA_NAME}.ts
endif

test: test-schema test-python test-examples

test-schema:
	$(RUN) gen-project ${CONFIG_YAML} -d tmp $(SOURCE_SCHEMA_PATH)

test-python:
	$(RUN) python -m unittest discover

convert-examples-to-%:
	$(patsubst %, $(RUN) linkml-convert  % -s $(SOURCE_SCHEMA_PATH) -C Person, $(shell ${SHELL} find src/data/examples -name "*.yaml"))

examples/%.yaml: src/data/examples/%.yaml
	$(RUN) linkml-convert -s $(SOURCE_SCHEMA_PATH) -C Person $< -o $@
examples/%.json: src/data/examples/%.yaml
	$(RUN) linkml-convert -s $(SOURCE_SCHEMA_PATH) -C Person $< -o $@
examples/%.ttl: src/data/examples/%.yaml
	$(RUN) linkml-convert -P EXAMPLE=http://example.org/ -s $(SOURCE_SCHEMA_PATH) -C Person $< -o $@

test-examples: examples/output

examples/output: src/thing_description_schema/schema/thing_description_schema.yaml
	mkdir -p $@
	$(RUN) linkml-run-examples \
		--output-formats json \
		--output-formats yaml \
		--counter-example-input-directory src/data/examples/invalid \
		--input-directory src/data/examples/valid \
		--output-directory $@ \
		--schema $< > $@/README.md

gendoc: $(DOCDIR)
	mkdir -p $(DOCDIR)
	cp -rf $(SRC)/docs/* $(DOCDIR)
	$(RUN) gen-doc ${GEN_DOC_ARGS} -d $(DOCDIR) $(SOURCE_SCHEMA_PATH)

testdoc: gendoc serve

serve: mkd-serve

MKDOCS = $(RUN) mkdocs
mkd-%:
	$(MKDOCS) $*

mkd-gh-deploy:
	$(RUN) mkdocs gh-deploy


clean:
	rm -rf $(DEST)
	rm -rf tmp
	rm -fr docs/*
	rm -fr $(PYMODEL)/*
