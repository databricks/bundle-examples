#!/usr/bin/env python3
#
# test.py runs the unit tests for this project using pytest.
#
import os
import subprocess


def main():
    os.environ["DATABRICKS_SERVERLESS_COMPUTE_ID"] = "auto"
    subprocess.run(["pytest"], check=True)


if __name__ == "__main__":
    main()
