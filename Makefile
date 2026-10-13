.PHONY: dev build render photo params test lint fmt docs docs-dev clean

VENV   := .venv
PYTHON := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip
BOARD  ?= microsam

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

## Install package in editable mode with dev extras
dev: $(VENV)/bin/activate
	$(PIP) install -e ".[dev]"

## Build, check and export every design -> out/$(BOARD)/<design>/{stl,step}/
build: dev
	$(VENV)/bin/dais build --board $(BOARD) --clean

## Render the documentation views -> docs/public/img/
render: dev
	$(VENV)/bin/dais render --board $(BOARD)

## Run test suite
test: dev
	$(VENV)/bin/pytest

## Check linting and formatting (no fixes)
lint: dev
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

## Auto-fix lint issues and apply formatting
fmt: dev
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

## Photo renders through Blender Cycles (CPU only, GPU masked, RAM-capped) -> docs/public/photo/
photo: dev
	$(VENV)/bin/dais photo --board $(BOARD)

## Regenerate the parameter reference page from params.py
params: dev
	$(VENV)/bin/dais params

## Build the VitePress documentation -> docs/.vitepress/dist/
docs: params
	cd docs && npm install && npm run docs:build

## Serve the documentation with live reload
docs-dev: params
	cd docs && npm install && npm run docs:dev

## Remove build artifacts
clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info .pytest_cache .ruff_cache .coverage coverage.xml out/
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null; true
