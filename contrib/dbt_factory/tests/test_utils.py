from databricks_dbt_factory.Utils import MAX_TASK_KEY_LENGTH, bundled_test_key, generate_task_key


def test_resource_keys_use_name_and_verb_suffix():
    assert generate_task_key("model.shop.orders") == "orders_run"
    assert generate_task_key("seed.shop.countries") == "countries_seed"
    assert generate_task_key("snapshot.shop.orders_snap") == "orders_snap_snapshot"


def test_versioned_model_keeps_version():
    assert generate_task_key("model.shop.dim_customers.v2") == "dim_customers_v2_run"


def test_test_key_drops_package_and_hash():
    assert generate_task_key("test.shop.unique_orders_id.9a1b2c3d4e") == "unique_orders_id_test"
    # singular test (no trailing hash segment)
    assert generate_task_key("test.shop.assert_positive_amount") == "assert_positive_amount_test"


def test_source_key():
    assert generate_task_key("source.shop.raw.customers") == "raw_customers_test"


def test_bundled_test_key():
    assert bundled_test_key("model.shop.orders") == "orders_test"
    assert bundled_test_key("seed.shop.countries") == "countries_test"
    assert bundled_test_key("source.shop.raw.customers") == "raw_customers_test"


def test_long_test_key_is_truncated_and_hash_disambiguated():
    long_name = "accepted_values_" + "x" * 200
    key = generate_task_key(f"test.shop.{long_name}.9a1b2c3d4e")
    assert len(key) <= MAX_TASK_KEY_LENGTH
    assert key.endswith("_9a1b2c3d4e_test")  # hash re-added so truncated names stay unique
