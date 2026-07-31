.PHONY: format lint check clean run test precommit

format:
	ruff format .
	ruff check . --fix

lint:
	ruff check .
	yamllint .
	actionlint

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


run:
	calmerge

test:
	pytest

precommit:
	pre-commit run --all-files
