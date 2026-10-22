"""Create generated/payload.txt for sync.include. Exit non-zero on failure."""

from pathlib import Path


def main() -> None:
    out = Path("generated/payload.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("synced-from-predeploy\n", encoding="utf-8")
    if (
        not out.is_file()
        or out.read_text(encoding="utf-8").strip() != "synced-from-predeploy"
    ):
        raise SystemExit("failed to write generated/payload.txt")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
