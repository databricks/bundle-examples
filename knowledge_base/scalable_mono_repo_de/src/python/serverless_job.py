from importlib.metadata import version
from get_taxis_data.main import get_taxis_data
from utils.main import add_processing_timestamp


def get_package_versions(packages: dict[str]):
    """
    Verify our package installs
    """
    for package in packages:
        print(f"{package} is installed & has version: {version(package)}")


def main():
    # Verify that we have our packages installed
    get_package_versions(["cowsay", "boto3", "get_taxis_data", "utils"])

    # Use our packages to read in taxi data & create a processing timestamp column
    df = get_taxis_data(spark)
    df = add_processing_timestamp(df=df)
    df.show(5)


if __name__ == "__main__":
    main()