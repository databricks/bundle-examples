"""Training entrypoint shipped inside the code_source tarball.

Reads the dataset the preprocess task produced (path passed by command.sh) and
echoes the distributed-run coordinates the AI Runtime injects. Replace the body
with your real training loop.
"""

import os
import sys


def main() -> None:
    rank = os.environ.get("NODE_RANK", "0")
    world_size = os.environ.get("WORLD_SIZE", "1")
    print(f"[train.py] hello from rank {rank} of {world_size}")

    dataset_path = sys.argv[1] if len(sys.argv) > 1 else ""
    if dataset_path and os.path.exists(dataset_path):
        with open(dataset_path) as f:
            num_examples = max(len(f.read().splitlines()) - 1, 0)  # minus header
        print(f"[train.py] training on {num_examples} examples from {dataset_path}")
    else:
        print(f"[train.py] dataset not found at {dataset_path!r}; training on synthetic data")

    print("[train.py] training complete")


if __name__ == "__main__":
    main()
