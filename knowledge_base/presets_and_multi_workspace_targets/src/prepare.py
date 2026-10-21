"""Prepare step for the presets demo job."""

import sys


def main() -> None:
    batch_size = sys.argv[1] if len(sys.argv) > 1 else "unset"
    print(f"prepare: batch_size={batch_size}")


if __name__ == "__main__":
    main()
