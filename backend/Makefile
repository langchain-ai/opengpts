.PHONY: all lint format test help

# Default target executed when no arguments are given to make.
all: help

build_ui:
	cd ../frontend && yarn build && cp -r dist/* ../backend/ui

######################
# TESTING AND COVERAGE
######################

# Define a variable for the test file path.
TEST_FILE ?= tests/unit_tests/

start:
	poetry run uvicorn app.server:app --reload --port 8100

test:
	# We need to update handling of env variables for tests
	YDC_API_KEY=placeholder OPENAI_API_KEY=placeholder poetry run pytest $(TEST_FILE)


test_watch:
	# We need to update handling of env variables for tests
	YDC_API_KEY=placeholder OPENAI_API_KEY=placeholder poetry run ptw . -- $(TEST_FILE)

######################
# LINTING AND FORMATTING
######################

# Define a variable for Python and notebook files.
PYTHON_FILES=.
lint format: PYTHON_FILES=.
lint_diff format_diff: PYTHON_FILES=$(shell git diff --relative=. --name-only --diff-filter=d master | grep -E '\.py$$|\.ipynb$$')

lint lint_diff:
	poetry run ruff .
	poetry run ruff format $(PYTHON_FILES) --check

format format_diff:
	poetry run ruff format $(PYTHON_FILES)
	poetry run ruff --select I --fix $(PYTHON_FILES)

spell_check:
	poetry run codespell --toml pyproject.toml

spell_fix:
	poetry run codespell --toml pyproject.toml -w

######################
# HELP
######################

help:
	@echo '===================='
	@echo '-- LINTING --'
	@echo 'format                       - run code formatters'
	@echo 'lint                         - run linters'
	@echo 'spell_check                 	- run codespell on the project'
	@echo 'spell_fix                		- run codespell on the project and fix the errors'
	@echo '-- TESTS --'
	@echo 'coverage                     - run unit tests and generate coverage report'
	@echo 'test                         - run unit tests'
	@echo 'test TEST_FILE=<test_file>   - run all tests in file'
	@echo '-- DOCUMENTATION tasks are from the top-level Makefile --'
