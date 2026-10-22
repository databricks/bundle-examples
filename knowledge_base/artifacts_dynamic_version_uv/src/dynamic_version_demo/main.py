from importlib.metadata import version

# Change this value and deploy again. You do not need to bump the version.
MARKER = "marker-v1"


def main():
    print(f"dynamic_version_demo {version('dynamic_version_demo')}: {MARKER}")


if __name__ == "__main__":
    main()
