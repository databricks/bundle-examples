"""Minimal training entrypoint shipped inside the code_source tarball.

Replace this with your real training code. It runs on each node; here it just
echoes the distributed-run coordinates the AI Runtime injects.
"""

import os


def main() -> None:
    rank = os.environ.get("NODE_RANK", "0")
    world_size = os.environ.get("WORLD_SIZE", "1")
    print(f"[train.py] hello from rank {rank} of {world_size}")
    print("[train.py] training complete")


if __name__ == "__main__":
    main()
