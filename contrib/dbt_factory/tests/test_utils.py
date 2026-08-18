from databricks_dbt_factory.utils import (
    MAX_TASK_KEY_LENGTH,
    build_task_key_maps,
    bundled_test_key,
    generate_task_key,
)


def test_resource_keys_use_name_and_type_suffix():
    assert generate_task_key("model.shop.orders") == "orders_model"
    assert generate_task_key("seed.shop.countries") == "countries_seed"
    assert generate_task_key("snapshot.shop.orders_snap") == "orders_snap_snapshot"


def test_versioned_model_keeps_version():
    assert generate_task_key("model.shop.dim_customers.v2") == "dim_customers_v2_model"


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


def test_key_maps_keep_plain_keys_when_unique():
    task_keys, bundled = build_task_key_maps(["model.shop.orders", "test.shop.unique_orders_id.9a1b2c3d4e"])
    assert task_keys == {
        "model.shop.orders": "orders_model",
        "test.shop.unique_orders_id.9a1b2c3d4e": "unique_orders_id_test",
    }
    assert bundled == {}


def test_key_maps_disambiguate_same_named_tests_with_dbt_hash():
    # The same custom test name on two models: dbt keeps them apart only via the unique_id hash.
    task_keys, _ = build_task_key_maps(["test.shop.dup_check.6ea6b2ac82", "test.shop.dup_check.a9ab3a6e12"])
    assert task_keys["test.shop.dup_check.6ea6b2ac82"] == "dup_check_6ea6b2ac82_test"
    assert task_keys["test.shop.dup_check.a9ab3a6e12"] == "dup_check_a9ab3a6e12_test"


def test_key_maps_disambiguate_singular_vs_custom_named_test():
    # A singular test file and a custom-named generic test can share a name; the singular test
    # has no hash, so it gets the package folded in instead.
    task_keys, _ = build_task_key_maps(["test.shop.raw_customers", "test.shop.raw_customers.e58cc24de2"])
    assert task_keys["test.shop.raw_customers"] == "shop_raw_customers_test"
    assert task_keys["test.shop.raw_customers.e58cc24de2"] == "raw_customers_e58cc24de2_test"


def test_key_maps_disambiguate_cross_package_models_with_package_name():
    task_keys, _ = build_task_key_maps(["model.shop.a", "model.subpkg.a", "model.shop.b"])
    assert task_keys["model.shop.a"] == "shop_a_model"
    assert task_keys["model.subpkg.a"] == "subpkg_a_model"
    assert task_keys["model.shop.b"] == "b_model"


def test_key_maps_disambiguate_bundled_test_key_against_task_keys():
    # Bundled mode: model `orders` claims the bundled key `orders_test`, and so does a singular
    # test named `orders`. Every returned key must still be unique.
    task_keys, bundled = build_task_key_maps(
        ["model.shop.orders", "test.shop.orders"], bundled_test_ids=["model.shop.orders"]
    )
    all_keys = list(task_keys.values()) + list(bundled.values())
    assert len(all_keys) == len(set(all_keys))
    assert task_keys["model.shop.orders"] == "orders_model"
    assert task_keys["test.shop.orders"] == "shop_orders_test_2"
    assert bundled["model.shop.orders"] == "shop_orders_test"


def test_key_maps_disambiguated_long_test_keys_keep_hash_within_limit():
    long_name = "accepted_values_" + "y" * 200
    ids = [f"test.shop.{long_name}.6ea6b2ac82", f"test.shop.{long_name}.a9ab3a6e12"]
    task_keys, _ = build_task_key_maps(ids)
    assert len(set(task_keys.values())) == 2
    for uid, key in task_keys.items():
        assert len(key) <= MAX_TASK_KEY_LENGTH
        assert key.endswith(f"_{uid.split('.')[3]}_test")
