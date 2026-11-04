"""Read the generated payload that sync.include uploaded."""

import sys
from pathlib import Path


def main() -> None:
    # spark_python_task on serverless does not set __file__; pass the path in.
    payload = Path(sys.argv[1])
    text = payload.read_text(encoding="utf-8").strip()
    print(f"payload: {text}")
    assert text == "synced-from-predeploy", f"unexpected payload: {text!r}"


if __name__ == "__main__":
    main()
