import json
from collections.abc import Iterable

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

    Distinct nodes can map to the same plain key (the same custom test name on two models, a
    model name reused across packages), so job generation resolves keys through
    :func:`build_task_key_maps`, which keeps these plain keys and disambiguates only actual
    collisions. Over-long test keys are truncated and disambiguated with dbt's hash to stay
    within the task-key length limit.
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


def build_task_key_maps(
    task_ids: Iterable[str], bundled_test_ids: Iterable[str] = ()
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Assigns every task-producing dbt node a unique Databricks task key.

    ``task_ids`` are nodes that become their own task (keys from :func:`generate_task_key`);
    ``bundled_test_ids`` are tested resources that additionally get a bundled test task in
    bundled mode (keys from :func:`bundled_test_key`). Plain keys are kept untouched unless
    several nodes claim the same key; each claimant of a contested key then gets a
    disambiguated key with dbt's test hash (or the package name, when there is no hash) folded
    in, falling back to the sanitized ``unique_id``. The returned keys are therefore always
    unique, so a valid dbt project cannot fail deployment with a duplicate task key.

    Returns ``(task_keys, bundled_test_keys)``, both keyed by ``unique_id``.
    """
    claims: dict[str, list[tuple[str, bool]]] = {}
    for uid in task_ids:
        claims.setdefault(generate_task_key(uid), []).append((uid, False))
    for uid in bundled_test_ids:
        claims.setdefault(bundled_test_key(uid), []).append((uid, True))

    task_keys: dict[str, str] = {}
    bundled_test_keys: dict[str, str] = {}
    taken = {key for key, claimants in claims.items() if len(claimants) == 1}
    for key, claimants in claims.items():
        if len(claimants) == 1:
            uid, is_bundled = claimants[0]
            (bundled_test_keys if is_bundled else task_keys)[uid] = key
            continue
        for uid, is_bundled in claimants:
            unique = _disambiguated_bundled_test_key(uid) if is_bundled else _disambiguated_task_key(uid)
            if unique in taken:
                unique = uid.replace(".", "_") + ("_test" if is_bundled else "")
            base, counter = unique, 2
            while unique in taken:
                unique = f"{base}_{counter}"
                counter += 1
            taken.add(unique)
            (bundled_test_keys if is_bundled else task_keys)[uid] = unique
    return task_keys, bundled_test_keys


def _disambiguated_task_key(unique_id: str) -> str:
    """
    Key for a node whose plain key collides with another node's: dbt's test hash (or the
    package name, when there is no hash) is folded in to keep the key unique yet readable,
    e.g. ``test.shop.dup_check.9a1`` -> ``dup_check_9a1_test``, ``model.pkg.orders`` ->
    ``pkg_orders_run``.
    """
    parts = unique_id.split(".")
    resource_type = parts[0]
    if resource_type in _RUN_SUFFIX:
        return f"{parts[1]}_{_resource_name(unique_id)}_{_RUN_SUFFIX[resource_type]}"
    if resource_type == "source":
        return f"{parts[1]}_{parts[2]}_{parts[3]}_test"
    if resource_type == "test":
        if len(parts) > 3:
            return _hashed_test_key(parts[2], parts[3])
        return f"{parts[1]}_{parts[2]}_test"
    return unique_id.replace(".", "_")


def _disambiguated_bundled_test_key(unique_id: str) -> str:
    """Package-prefixed variant of :func:`bundled_test_key`, for contested bundled test keys."""
    parts = unique_id.split(".")
    if parts[0] == "source":
        return f"{parts[1]}_{parts[2]}_{parts[3]}_test"
    return f"{parts[1]}_{_resource_name(unique_id)}_test"


def _bounded_test_key(test_name: str, test_hash: str) -> str:
    """``<test_name>_test``, truncated and hash-disambiguated if it exceeds the key length limit."""
    key = f"{test_name}_test"
    if len(key) <= MAX_TASK_KEY_LENGTH:
        return key
    return _hashed_test_key(test_name, test_hash)


def _hashed_test_key(test_name: str, test_hash: str) -> str:
    """``<test_name>_<hash>_test``, truncating the name so the hash survives the length limit."""
    tail = (f"_{test_hash}" if test_hash else "") + "_test"
    if len(test_name) + len(tail) <= MAX_TASK_KEY_LENGTH:
        return test_name + tail
    return test_name[: MAX_TASK_KEY_LENGTH - len(tail)] + tail


def read_dbt_manifest(path: str) -> dict:
    """
    Reads a dbt manifest JSON file and returns its parsed content.

    Args:
        path (str): Path to the manifest file.

    Returns:
        dict: Parsed manifest content.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not valid JSON.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Manifest file not found: {path}. Details: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing JSON from manifest file: {path}. Details: {e}") from e
