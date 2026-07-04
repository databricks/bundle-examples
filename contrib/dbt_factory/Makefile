.PHONY: setup deps manifest validate deploy run test test-update-expected-tasks test-e2e

# Install dependencies into the .venv used by the bundle (databricks.yml -> python.venv_path).
setup:
	uv sync --dev

# Install dbt package dependencies declared in packages.yml / dependencies.yml (if any).
deps:
	uv run dbt deps

# Regenerate the dbt manifest that resources/__init__.py reads at deploy time.
# `dbt parse` does not connect to a warehouse; it only reads the project files.
manifest: deps
	uv run dbt parse --profiles-dir dbt_profiles

validate:
	databricks bundle validate

# Regenerate the manifest and deploy the generated job to the dev target.
deploy: manifest
	databricks bundle deploy --target dev

run:
	databricks bundle run dbt_factory_job

test:
	uv run pytest tests

# Refresh the saved "expected tasks" file the tests compare against, after you intentionally
# change the generated output.
test-update-expected-tasks:
	uv run python tests/update_expected_tasks.py

# End-to-end test: generate a project from the template, deploy the factory-generated job to your
# workspace, run it, verify the output, and tear it all down. Needs DBX_E2E_* env (see tests/e2e/run_e2e.py).
test-e2e:
	uv run python tests/e2e/run_e2e.py
