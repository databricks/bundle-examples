import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--name", required=True)
parser.add_argument("--fail", choices=("true", "false"), default="false")
args = parser.parse_args()

if args.fail == "true":
    raise RuntimeError(f"Item {args.name} failed on purpose")

print(f"Processed item {args.name}")
