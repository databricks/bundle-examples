"""Main entry point for UDTF registration"""

import argparse
import kmeans_udtf


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    args = parser.parse_args()

    fn = kmeans_udtf.register(args.catalog, args.schema)
    print(f"✅ Registered {fn}")
