"""Write a small customer change feed as JSON files to a Unity Catalog volume."""

import json
import os
import sys

# Each file is one batch. The pipeline reads one file per micro-batch.
BATCHES = {
    "batch_1.json": [
        {"id": 1, "name": "Alice", "city": "Seattle", "operation": "INSERT", "seq": 1},
        {"id": 2, "name": "Bob", "city": "Austin", "operation": "INSERT", "seq": 2},
        {"id": 3, "name": "Carol", "city": "Denver", "operation": "INSERT", "seq": 3},
        {"id": 1, "name": "Alice", "city": "Portland", "operation": "UPDATE", "seq": 5},
    ],
    "batch_2.json": [
        # Late event: seq 4 arrives after seq 5 for the same key.
        {"id": 1, "name": "Alice", "city": "Boston", "operation": "UPDATE", "seq": 4},
        {"id": 2, "name": None, "city": None, "operation": "DELETE", "seq": 6},
        {"id": 3, "name": "Carol", "city": "Miami", "operation": "UPDATE", "seq": 7},
    ],
}

path = sys.argv[1]
os.makedirs(path, exist_ok=True)
for file_name, rows in BATCHES.items():
    with open(os.path.join(path, file_name), "w") as f:
        f.write("\n".join(json.dumps(row) for row in rows))
    print(f"Wrote {len(rows)} changes to {path}/{file_name}")
