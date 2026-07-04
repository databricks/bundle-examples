# Databricks caps task keys at 100 characters (letters, numbers, underscores, hyphens).
MAX_TASK_KEY_LENGTH = 100

# dbt resource type -> the dbt verb the task runs, used as the task-key suffix.
_RUN_SUFFIX = {"model": "run", "seed": "seed", "snapshot": "snapshot"}


def _resource_name(unique_id: str) -> str:
    """
    The dbt resource name — everything after ``<type>.<package>.`` — with dots turned into
    underscores. Keeps a versioned model's version, e.g. ``model.shop.dim.v2`` -> ``dim_v2``.
    """
    return "_".join(unique_id.split(".")[2:])


def generate_task_key(unique_id: str) -> str:
    """
    Builds a readable Databricks task key from a dbt node ``unique_id``.

    The key is based on the dbt resource *name* (not the fully-qualified id), so the package
    prefix and dbt's test-name hash never appear, with a verb suffix per resource type:

    * ``model.shop.orders``              -> ``orders_run``
    * ``seed.shop.countries``            -> ``countries_seed``
    * ``snapshot.shop.orders_snap``      -> ``orders_snap_snapshot``
    * ``test.shop.unique_orders_id.9a1`` -> ``unique_orders_id_test``  (hash dropped)
    * ``source.shop.raw.customers``      -> ``raw_customers_test``

    dbt resource names are unique within a project and the verb suffix separates resource types,
    so keys don't collide in a single-package project (a cross-package clash would surface loudly
    as a duplicate task key at deploy time). Over-long test keys are truncated and disambiguated
    with dbt's hash to stay within the task-key length limit.
    """
    parts = unique_id.split(".")
    resource_type = parts[0]

    if resource_type in _RUN_SUFFIX:
        return f"{_resource_name(unique_id)}_{_RUN_SUFFIX[resource_type]}"

    if resource_type == "source":
        # A source only ever surfaces as a test task: source.<package>.<source_name>.<table>.
        return f"{parts[2]}_{parts[3]}_test"

    if resource_type == "test":
        # test.<package>.<test_name>[.<hash>] -> <test_name>_test (drop dbt's uniqueness hash).
        test_hash = parts[3] if len(parts) > 3 else ""
        return _bounded_test_key(parts[2], test_hash)

    # Unknown type: fall back to the sanitized id (still unique).
    return unique_id.replace(".", "_")


def bundled_test_key(unique_id: str) -> str:
    """
    Key for the single ``dbt test`` task that gates a tested resource in bundled mode:
    ``model.shop.orders`` -> ``orders_test``; ``source.shop.raw.customers`` -> ``raw_customers_test``.
    """
    parts = unique_id.split(".")
    if parts[0] == "source":
        return f"{parts[2]}_{parts[3]}_test"
    return f"{_resource_name(unique_id)}_test"


def _bounded_test_key(test_name: str, test_hash: str) -> str:
    """``<test_name>_test``, truncated and hash-disambiguated if it exceeds the key length limit."""
    key = f"{test_name}_test"
    if len(key) <= MAX_TASK_KEY_LENGTH:
        return key
    tail = (f"_{test_hash}" if test_hash else "") + "_test"
    return test_name[: MAX_TASK_KEY_LENGTH - len(tail)] + tail
