.PHONY: all tests clean
.DEFAULT_GOAL := tests

include .env
export

GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
GIT_COMMIT := $(shell git rev-list -1 HEAD)
GIT_VERSION := $(shell git describe --tags --always)

clean:
	@rm -rf .mypy_cache || echo ""
	@rm -rf .pytest_cache || echo ""
	@rm ./logs/* || echo ""
	@touch ./logs/.gitkeep && git add ./logs/.gitkeep
	@rm ./reports/* || echo ""
	@touch ./reports/.gitkeep && git add ./reports/.gitkeep
	@rm -rf ./coverage || echo ""
	@rm -rf ./.coverage.* || echo ""
	@rm .coverage || echo ""
	$(MAKE) clean_pycache
	rm -rf ./dist || echo ""
	@echo "Cleaned up the project files."

clean_pycache:
	@if directories=$$(find . -type d -name __pycache__); then \
		find . -type d -name __pycache__ -exec rm -rf {} +; \
	else \
		echo "No __pycache__ directories found."; \
	fi

poetry_install:
	poetry install --compile

poetry_install_dev:
	poetry install --compile --with dev

poetry_install_cmd:
	poetry install --compile --with cmd

lint_fix:
	poetry run black cmd_initial.py cmd_worker.py pybas_automation/ tests/
	poetry run isort cmd_initial.py cmd_worker.py pybas_automation/ tests/
	#poetry run autopep8 --in-place --aggressive --aggressive  pybas_automation/utils/utils.py

lint:
	mkdir ./dist || echo ""
	touch ./dist/README.md
	poetry check
	poetry run mypy cmd_initial.py cmd_worker.py pybas_automation/ tests/ || echo ""
	poetry run flake8 cmd_initial.py cmd_worker.py pybas_automation/ tests/ || echo ""
	pylint --load-plugins pylint_pydantic cmd_initial.py cmd_worker.py ./pybas_automation/ || echo ""

lint_docs:
	poetry run pydocstyle pybas_automation

tests:
	poetry run pytest -s -vv tests/
	$(MAKE) clean_pycache

tests_coverage:
	poetry run pytest -s -vv --cov=pybas_automation --cov-report=html:coverage/html/ tests/
	start "" "./coverage/html/index.html"

tests_coverage_e2e:
	poetry run pytest -s -vv --cov=pybas_automation --cov-report=html:coverage/html/e2e/ tests/e2e/
	start "" "./coverage/html/e2e/index.html"

tests_coverage_functional:
	poetry run pytest -s -vv --cov=pybas_automation --cov-report=html:coverage/html/functional/ tests/functional/
	start "" "./coverage/html/functional/index.html"

run_cmd_initial:
	@$(MAKE) clean
	poetry run python cmd_initial.py --bas_fingerprint_key="${FINGERPRINT_KEY}" --limit_tasks=1

run_cmd_initial_proxy:
	@$(MAKE) clean
	poetry run python cmd_initial.py --bas_fingerprint_key="${FINGERPRINT_KEY}" --limit_tasks=1 \
  --proxy_provider=brightdata --proxy_username="${BRIGHTDATA_USERNAME}" \
  --proxy_password="${BRIGHTDATA_PASSWORD}"

run_cmd_worker:
	poetry run python cmd_worker.py

publish:
	echo "Current branch is '${GIT_BRANCH}'."
    ifeq ($(GIT_BRANCH),master)
		@echo "Current branch is 'master'. Proceeding with publishing."
		poetry run python scripts/update_readme_links.py
		poetry build
		poetry publish --username=__token__ --password=${PYPI_PASSWORD}
		start "" "https://pypi.org/project/pybas-automation/"
    else
		@echo "Publishing is only allowed from the 'master' branch."
    endif

bump_version:
	@echo "Current branch is '${GIT_BRANCH}'."
    ifeq ($(GIT_BRANCH),master)
		poetry run python scripts/update_readme_links.py
		poetry check
		cz bump --check-consistency --changelog --increment=patch
    else
		@echo "Bump version is only allowed from the 'master' branch."
    endif

run_pydeps:
	pydeps pybas_automation

poetry_upgrade:
	poetry up --latest
	poetry update
	poetry show --outdated