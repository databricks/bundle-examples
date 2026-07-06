"""Refresh tests/test_data/expected_tasks.json — the saved copy of the job tasks the factory
generates for the sample manifest. The test `test_generated_tasks_match_expected` compares the
current output against this file, so run this script (via `make test-update-expected-tasks`) whenever
you intentionally change the generated output.

It builds the factory the exact same way the tests do (conftest.create_dbt_factory), so the saved
copy can't drift from what the tests expect.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from conftest import create_dbt_factory  # noqa: E402
from databricks_dbt_factory.Utils import read_dbt_manifest  # noqa: E402

TEST_DATA = Path(__file__).resolve().parent / "test_data"


def main() -> None:
    manifest = read_dbt_manifest(str(TEST_DATA / "manifest.json"))
    tasks = create_dbt_factory().create_tasks(manifest)
    (TEST_DATA / "expected_tasks.json").write_text(json.dumps(tasks, indent=2) + "\n")
    print(f"Wrote {len(tasks)} tasks to {TEST_DATA / 'expected_tasks.json'}")


if __name__ == "__main__":
    main()
