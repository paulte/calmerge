.PHONY: all format lint check clean test coverage precommit distclean

all: format  check

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
	$(MAKE) test

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
	python -m pytest

coverage:
	python -m pytest \
		--cov=src/calmerge \
		--cov-report=term-missing \
		--cov-report=xml:coverage.xml \
		--cov-report=html:coverage-report \
		--cov-fail-under=85
