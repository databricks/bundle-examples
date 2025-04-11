from functools import cache


@cache
def bundle_file_path() -> str:
    """
    Return the bundle file path.

    This function expects a job parameter called "bundle_file_path" to be set.

    It is mocked during testing.

    The dbutils import is done inside the function so it is omitted when run locally.
    """
    from databricks.sdk.runtime import dbutils
    return dbutils.widgets.get("bundle_file_path")


@cache
def bundle_target() -> str:
    """
    Return the bundle target.

    This function expects a job parameter called "bundle_target" to be set.

    It is mocked during testing.

    The dbutils import is done inside the function so it is omitted when run locally.
    """
    from databricks.sdk.runtime import dbutils
    return dbutils.widgets.get("bundle_target")
