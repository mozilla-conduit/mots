# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

SHELL := /bin/bash
PYTHON := $(shell which python)


.PHONY: help
help:
	@echo "using python at $(PYTHON)."
	@$(PYTHON) --version
	@echo "usage: make <target>"
	@echo
	@echo "target is one of:"
	@echo "    help          show this message and exit"
	@echo "    build         build the python package and wheels"
	@echo "    clean         remove temporary files"
	@echo "    cov           run coverage check"
	@echo "    cov-html      generate html coverage report"
	@echo "    dev           setup local dev environment by installing required packages, etc."
	@echo "    dev-env       create a python virtual environment in ./mots-env"
	@echo "    docs          generate documentation"
	@echo "    publish-test  publish package to test.pypi.org"
	@echo "    publish       publish package to pypi.org"
	@echo "    requirements  regenerate requirements.txt"
	@echo "    serve-cov     simple http server for coverage report"
	@echo "    serve-docs    simple http server for docs"
	@echo "    test          run the test suite"

.PHONY: test
test:
	$(PYTHON) -m pytest -vvv

.PHONY: build
build:
	$(PYTHON) -m build

.PHONY: docs
docs:
	make -C documentation html

.PHONY: cov
cov:
	-@rm -R .coverage 2>/dev/null ||:
	$(PYTHON) -m pytest --cov-fail-under=50 --cov=src/mots tests

.PHONY: cov-html
cov-html:
	-@rm -R .coverage 2>/dev/null ||:
	-@rm -R .htmlcov 2>/dev/null ||:
	$(PYTHON) -m pytest --cov=src/mots tests --cov-report html

.PHONY: serve-cov
serve-cov:
	$(PYTHON) -m http.server -d htmlcov 8080

.PHONY: format
format:
	$(PYTHON) -m black src/mots
	$(PYTHON) -m black tests
	$(PYTHON) -m black documentation

.ONESHELL:
.PHONY: publish
publish:
ifdef PYPI_TOKEN
	$(PYTHON) -m twine upload -r pypi dist/* --verbose \
	--username __token__ --password $(PYPI_TOKEN)
else
	$(error "PYPI_TOKEN must be defined.")
endif

.ONESHELL:
.PHONY: publish-test
publish-test:
ifdef TESTPYPI_TOKEN
	$(PYTHON) -m twine upload -r testpypi dist/* --verbose \
	--username __token__ --password $(TESTPYPI_TOKEN)
else
	$(error "TESTPYPI_TOKEN must be defined.")
endif

.PHONY: requirements
requirements:
	rm requirements/*.txt
	docker-compose run generate-python3.7-requirements
	docker-compose run generate-python3.8-requirements
	docker-compose run generate-python3.9-requirements
	docker-compose run generate-python3.10-requirements

.ONESHELL:
.PHONY: dev-env
dev-env:
ifdef PY
	@echo "Creating virtual env in .mots-env using provided Python ($(PY))..."
	-@(/usr/bin/$(PY) -m venv .mots-env && ([ $$? -eq 0 ] && echo "$(PY) found.")) 2>/dev/null||
	-@(/usr/local/bin/$(PY) -m venv .mots-env && ([ $$? -eq 0 ] && echo "$(PY) found.")) 2>/dev/null
else
	@echo "PY variable not defined, using python3 if available..."
	@echo "Creating virtual env in .mots-env using python3..."
	-@(python3 -m venv .mots-env && ([ $$? -eq 0 ] && echo "Found $(shell python3 --version)")) 2>/dev/null
endif

.ONESHELL:
.PHONY: dev
dev:
	set -e
	. ./.mots-env/bin/activate
	python -m pip install --upgrade pip
	python -m pip install pip-tools
	python -m pip install -r requirements/$$(./requirements/get_filename)
	python -m pip install -e .

.PHONY: serve-docs
serve-docs:
	$(PYTHON) -m http.server -d documentation/_build/html 8080

.PHONY: clean
clean:
	-@rm -R htmlcov 2>/dev/null ||:
	-@rm -R documentation/_build 2>/dev/null ||:
	-@rm -R dist 2>/dev/null ||:
	-@rm -R src/*.egg-info 2>/dev/null ||:
	-@rm -R src/mots/__pycache__ 2>/dev/null ||:
	-@rm -R tests/__pycache__ 2>/dev/null ||:
	-@rm -R .coverage 2>/dev/null ||:
	-@rm -R .pytest_cache 2>/dev/null ||:
	-@rm -R .mots-env 2>/dev/null ||:
	-@rm -R .pytest_cache-env 2>/dev/null ||:
