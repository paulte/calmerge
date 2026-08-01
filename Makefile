.PHONY: all format lint check clean test precommit distclean

all: check precommit

format:
	ruff format .
	ruff check . --fix

lint:
	ruff check .
	yamllint .
	actionlint

precommit:
	pre-commit run --all-files

check:
	ruff format --check .
	ruff check .
	yamllint .
	actionlint
	pytest

distclean:
	rm -rf .cache
	rm -rf calendars/
	rm -rf venv/
	rm -rf tests/__pycache__
	rm -rf __pycache__
	rm -rf src/calmerge/__pycache__
	rm -rf src/*.egg-info
	rm -rf .pytest_cache
	rm -rf build
	rm -rf dist

clean:
	rm -rf .cache
	rm -rf tests/__pycache__
	rm -rf __pycache__
	rm -rf src/calmerge/__pycache__

test:
	pytest
