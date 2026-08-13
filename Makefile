requirements:
	pip-compile \
		--generate-hashes \
		--allow-unsafe \
		--output-file requirements.txt \
		pyproject.toml
	pip-compile \
		--extra dev \
		--generate-hashes \
		--allow-unsafe \
		--output-file requirements-dev.txt \
		pyproject.toml
	pip-compile \
		--extra ci \
		--generate-hashes \
		--allow-unsafe \
		--output-file .github/requirements-ci.txt \
		pyproject.toml

requirements-upgrade:
	pip-compile \
		--upgrade \
		--generate-hashes \
		--allow-unsafe \
		--output-file requirements.txt \
		pyproject.toml
	pip-compile \
		--upgrade \
		--extra dev \
		--generate-hashes \
		--allow-unsafe \
		--output-file requirements-dev.txt \
		pyproject.toml
	pip-compile \
		--upgrade \
		--extra ci \
		--generate-hashes \
		--allow-unsafe \
		--output-file .github/requirements-ci.txt \
		pyproject.toml
