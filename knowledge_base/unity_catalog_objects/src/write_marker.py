"""Write a marker file into the bundle-managed Unity Catalog volume."""

import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: write_marker.py <volume_file_path>")
    path = Path(sys.argv[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"written_at={datetime.now(timezone.utc).isoformat()}\n", encoding="utf-8"
    )
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
