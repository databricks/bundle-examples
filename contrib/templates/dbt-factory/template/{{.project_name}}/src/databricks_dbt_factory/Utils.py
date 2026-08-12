import hashlib
import json
import re
from collections.abc import Iterable

# Databricks substitutes complete dynamic value references in task string fields before execution.
DYNAMIC_VALUE_REFERENCE = re.compile(r"\{\{[^{}]+\}\}")

# Databricks caps task keys at 100 characters (letters, numbers, underscores, hyphens).
MAX_TASK_KEY_LENGTH = 100

# dbt resource types whose task key is `<resource_name>_<type>` (the type doubles as the suffix).
_SUFFIXED_TYPES = frozenset({"model", "seed", "snapshot"})


def _resource_name(unique_id: str) -> str:
    """
    The dbt resource name — everything after `<type>.<package>.` — with dots turned into
    underscores. Keeps a versioned model's version, e.g. `model.shop.dim.v2` -> `dim_v2`.
    """
    return "_".join(unique_id.split(".")[2:])


def _source_key(parts: list[str], with_package: bool) -> str:
    """
    Test-task key for a source (`source.<package>.<source_name>.<table>`): `<source_name>_<table>_test`,
    package-prefixed (`<package>_<source_name>_<table>_test`) when disambiguating a collision.
    """
    prefix = f"{parts[1]}_" if with_package else ""
    return f"{prefix}{parts[2]}_{parts[3]}_test"


def _sanitized_id(unique_id: str) -> str:
    """Fallback key for an unhandled resource type: the sanitized `unique_id` (dots -> underscores)."""
    return unique_id.replace(".", "_")


# Minimum dot-separated segment count required to build a key for each resource type. dbt ids are
# `<type>.<package>.<name>[...]`; sources are `source.<package>.<source_name>.<table>`.
_MIN_SEGMENTS = {"model": 3, "seed": 3, "snapshot": 3, "test": 3, "source": 4}


def _split_unique_id(unique_id: str) -> list[str]:
    """
    Splits a dbt node `unique_id` into its dot-separated parts, validating it has enough segments
    for its resource type. Raises `ValueError` with a clear message on a malformed id (e.g. a
    name-less `model.pkg`, or a source missing its table).
    """
    parts = unique_id.split(".")
    minimum = _MIN_SEGMENTS.get(parts[0])
    if minimum is not None and len(parts) < minimum:
        raise ValueError(
            f"Malformed dbt node id {unique_id!r}: expected at least {minimum} dot-separated segments."
        )
    return parts


def generate_task_key(unique_id: str) -> str:
    """
    Builds a readable Databricks task key from a dbt node `unique_id`.

    The key is based on the dbt resource *name* (not the fully-qualified id), so the package
    prefix and dbt's test-name hash never appear, with the resource type as a suffix:

    * `model.shop.orders`              -> `orders_model`
    * `seed.shop.countries`            -> `countries_seed`
    * `snapshot.shop.orders_snap`      -> `orders_snap_snapshot`
    * `test.shop.unique_orders_id.9a1` -> `unique_orders_id_test`  (hash dropped)
    * `source.shop.raw.customers`      -> `raw_customers_test`

    Distinct nodes can map to the same plain key (the same custom test name on two models, a
    model name reused across packages), so job generation resolves keys through
    `build_task_key_maps`, which keeps these plain keys and disambiguates only actual
    collisions. Over-long test keys are truncated and disambiguated with dbt's hash to stay
    within the task-key length limit.
    """
    parts = _split_unique_id(unique_id)
    resource_type = parts[0]

    if resource_type in _SUFFIXED_TYPES:
        return f"{_resource_name(unique_id)}_{resource_type}"

    if resource_type == "source":
        # A source only ever surfaces as a test task: source.<package>.<source_name>.<table>.
        return _source_key(parts, with_package=False)

    if resource_type == "test":
        # test.<package>.<test_name>[.<hash>] -> <test_name>_test (drop dbt's uniqueness hash).
        test_hash = parts[3] if len(parts) > 3 else ""
        return _bounded_test_key(parts[2], test_hash)

    # Unknown type: fall back to the sanitized id (still unique).
    return _sanitized_id(unique_id)


def bundled_test_key(unique_id: str) -> str:
    """
    Key for the single `dbt test` task that gates a tested resource in bundled mode:
    `model.shop.orders` -> `orders_test`; `source.shop.raw.customers` -> `raw_customers_test`.
    """
    parts = _split_unique_id(unique_id)
    if parts[0] == "source":
        return _source_key(parts, with_package=False)
    return f"{_resource_name(unique_id)}_test"


def build_task_key_maps(
    task_ids: Iterable[str], bundled_test_ids: Iterable[str] = ()
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Assigns every task-producing dbt node a unique Databricks task key.

    `task_ids` are nodes that become their own task (keys from `generate_task_key`);
    `bundled_test_ids` are tested resources that additionally get a bundled test task in
    bundled mode (keys from `bundled_test_key`). Plain keys are kept untouched unless
    several nodes claim the same key; each claimant of a contested key then gets a
    disambiguated key with dbt's test hash (or the package name, when there is no hash) folded
    in, falling back to the sanitized `unique_id`. Every assigned key is passed through
    `_reserve`, which enforces both uniqueness and the `MAX_TASK_KEY_LENGTH` limit, so the
    returned keys are always unique and within length — a valid dbt project cannot fail
    deployment with a duplicate or over-long task key.

    Returns `(task_keys, bundled_test_keys)`, both keyed by `unique_id`.
    """
    claims: dict[str, list[tuple[str, bool]]] = {}
    for uid in task_ids:
        claims.setdefault(generate_task_key(uid), []).append((uid, False))
    for uid in bundled_test_ids:
        claims.setdefault(bundled_test_key(uid), []).append((uid, True))

    task_keys: dict[str, str] = {}
    bundled_test_keys: dict[str, str] = {}
    taken: set[str] = set()
    # Both passes walk their claims in sorted order rather than manifest order. `_reserve`'s
    # numeric suffix is handed out first-come, so iterating in manifest order would let the
    # *arrangement* of the manifest decide which of two colliding nodes keeps the readable key —
    # adding or renaming an unrelated model could then silently swap two task keys, repointing
    # per-task run history and task-level alerts at a different model. Sorting makes every
    # assigned key a function of the node ids alone.
    ordered_claims = sorted(
        (key, sorted(claimants)) for key, claimants in claims.items()
    )
    # Assign uncontested keys first so a contested claimant's fallback never steals a plain key.
    for key, claimants in ordered_claims:
        if len(claimants) == 1:
            uid, is_bundled = claimants[0]
            (bundled_test_keys if is_bundled else task_keys)[uid] = _reserve(key, taken)
    for key, claimants in ordered_claims:
        if len(claimants) == 1:
            continue
        for uid, is_bundled in claimants:
            candidate = (
                _disambiguated_bundled_test_key(uid)
                if is_bundled
                else _disambiguated_task_key(uid)
            )
            (bundled_test_keys if is_bundled else task_keys)[uid] = _reserve(
                candidate, taken
            )
    return task_keys, bundled_test_keys


def _reserve(candidate: str, taken: set[str]) -> str:
    """
    Returns a unique task key at most `MAX_TASK_KEY_LENGTH` characters long, records it in
    `taken`, and never returns the same key twice.

    `candidate` is first bounded to the length limit (its tail replaced by a short hash of the
    full candidate so distinct over-long keys stay distinct). If the bounded key is already
    taken, a numeric suffix is appended and the result re-bounded, until an unused key is found.
    """
    key = _bounded(candidate)
    if key not in taken:
        taken.add(key)
        return key
    counter = 2
    while True:
        key = _bounded(f"{candidate}_{counter}")
        if key not in taken:
            taken.add(key)
            return key
        counter += 1


def _bounded(key: str) -> str:
    """
    Returns `key` unchanged if within `MAX_TASK_KEY_LENGTH`, otherwise truncates it and appends
    a short hash of the full key so distinct over-long keys map to distinct bounded keys.
    """
    if len(key) <= MAX_TASK_KEY_LENGTH:
        return key
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]
    return f"{key[: MAX_TASK_KEY_LENGTH - len(digest) - 1]}_{digest}"


def _disambiguated_task_key(unique_id: str) -> str:
    """
    Key for a node whose plain key collides with another node's: dbt's test hash (or the
    package name, when there is no hash) is folded in to keep the key unique yet readable,
    e.g. `test.shop.dup_check.9a1` -> `dup_check_9a1_test`, `model.pkg.orders` ->
    `pkg_orders_model`.
    """
    parts = unique_id.split(".")
    resource_type = parts[0]
    if resource_type in _SUFFIXED_TYPES:
        return f"{parts[1]}_{_resource_name(unique_id)}_{resource_type}"
    if resource_type == "source":
        return _source_key(parts, with_package=True)
    if resource_type == "test":
        if len(parts) > 3:
            return _hashed_test_key(parts[2], parts[3])
        return f"{parts[1]}_{parts[2]}_test"
    return _sanitized_id(unique_id)


def _disambiguated_bundled_test_key(unique_id: str) -> str:
    """Package-prefixed variant of `bundled_test_key`, for contested bundled test keys."""
    parts = unique_id.split(".")
    if parts[0] == "source":
        return _source_key(parts, with_package=True)
    return f"{parts[1]}_{_resource_name(unique_id)}_test"


def _bounded_test_key(test_name: str, test_hash: str) -> str:
    """`<test_name>_test`, truncated and hash-disambiguated if it exceeds the key length limit."""
    key = f"{test_name}_test"
    if len(key) <= MAX_TASK_KEY_LENGTH:
        return key
    return _hashed_test_key(test_name, test_hash)


def _hashed_test_key(test_name: str, test_hash: str) -> str:
    """`<test_name>_<hash>_test`, truncating the name so the hash survives the length limit."""
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
        ValueError: If the file is not valid JSON, or is valid JSON that is not an object. A non-object
            (list, scalar, null) would parse here and only fail later as an AttributeError on
            `manifest.get(...)`, which `main` does not catch — a traceback instead of a clean `error:`.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            manifest = json.load(file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Manifest file not found: {path}. Details: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Error parsing JSON from manifest file: {path}. Details: {e}"
        ) from e
    if not isinstance(manifest, dict):
        raise ValueError(
            f"Manifest file {path} must contain a JSON object, got {type(manifest).__name__}."
        )
    return manifest
