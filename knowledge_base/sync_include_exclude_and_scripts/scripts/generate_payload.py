"""Create generated/payload.txt for sync.include. Exit non-zero on failure."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEXT = "synced-from-predeploy"


def main() -> None:
    # Unset = default text. Empty PAYLOAD_TEXT fails the predeploy hook (and deploy).
    if "PAYLOAD_TEXT" in os.environ and os.environ["PAYLOAD_TEXT"] == "":
        raise SystemExit("PAYLOAD_TEXT is empty; unset it or set a non-empty value")

    text = os.environ.get("PAYLOAD_TEXT", DEFAULT_TEXT)
    out = ROOT / "generated" / "payload.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n", encoding="utf-8")
    if not out.is_file() or out.read_text(encoding="utf-8").strip() != text:
        raise SystemExit(f"failed to write {out}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
