import argparse
import time


parser = argparse.ArgumentParser()
parser.add_argument("--sleep-seconds", type=int, default=0)
parser.add_argument("--fail", choices=("true", "false"), default="false")
args = parser.parse_args()

if args.sleep_seconds < 0:
    parser.error("--sleep-seconds must be zero or greater")

print(f"Sleeping for {args.sleep_seconds} seconds")
time.sleep(args.sleep_seconds)

if args.fail == "true":
    raise RuntimeError("Intentional failure requested")

print("Task completed successfully")
