import json
from pathlib import Path

import pytest

from databricks_dbt_factory.Utils import read_dbt_manifest

BASE_PATH = str(Path(__file__).resolve().parent)


def _model(package: str, name: str, depends_on: list[str] | None = None) -> tuple[str, dict]:
    full_name = f"model.{package}.{name}"
    return full_name, {
        "resource_type": "model",
        "name": name,
        "package_name": package,
        "fqn": [package, name],
        "depends_on": {"nodes": depends_on or []},
    }


def _test(
    package: str,
    name: str,
    depends_on: list[str],
    severity: str = "error",
    test_hash: str = "",
) -> tuple[str, dict]:
    full_name = f"test.{package}.{name}" + (f".{test_hash}" if test_hash else "")
    return full_name, {
        "resource_type": "test",
        "name": name,
        "package_name": package,
        "fqn": [package, name],
        "depends_on": {"nodes": depends_on},
        "config": {"severity": severity},
    }


def _seed(package: str, name: str) -> tuple[str, dict]:
    full_name = f"seed.{package}.{name}"
    return full_name, {
        "resource_type": "seed",
        "name": name,
        "package_name": package,
        "fqn": [package, name],
        "depends_on": {"nodes": []},
    }


def _snapshot(package: str, name: str, depends_on: list[str] | None = None) -> tuple[str, dict]:
    full_name = f"snapshot.{package}.{name}"
    return full_name, {
        "resource_type": "snapshot",
        "name": name,
        "package_name": package,
        "fqn": [package, name],
        "depends_on": {"nodes": depends_on or []},
    }


def _source(package: str, source_name: str, table: str) -> tuple[str, dict]:
    full_name = f"source.{package}.{source_name}.{table}"
    return full_name, {
        "resource_type": "source",
        "name": table,
        "source_name": source_name,
        "package_name": package,
        "fqn": [package, source_name, table],
    }


def _commands(task: dict) -> list[str]:
    """Extracts the dbt commands from a rendered (serverless notebook) task dict."""
    return json.loads(task["notebook_task"]["base_parameters"]["dbt_commands"])


def test_bundled_model_gates_on_tests_of_all_tested_upstreams(dbt_factory_bundled):
    nodes = dict(
        [
            _model("pkg", "customers"),
            _model("pkg", "products"),
            _model(
                "pkg",
                "orders",
                depends_on=["model.pkg.customers", "model.pkg.products"],
            ),
            _test("pkg", "unique_customers_id", ["model.pkg.customers"]),
            _test("pkg", "unique_products_id", ["model.pkg.products"]),
        ]
    )

    tasks = dbt_factory_bundled.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    assert "customers_test" in by_key
    assert "products_test" in by_key
    assert _commands(by_key["customers_test"]) == [
        "dbt test --select fqn:pkg.unique_customers_id,package:pkg,resource_type:test --target dev --indirect-selection empty"
    ]
    assert by_key["customers_test"]["depends_on"] == [{"task_key": "customers_model"}]

    # orders depends on both upstreams' bundled test tasks (rewired from their run tasks)
    assert {dep["task_key"] for dep in by_key["orders_model"]["depends_on"]} == {
        "customers_test",
        "products_test",
    }


def test_tests_on_seed_produce_task_and_gate_downstream(dbt_factory_bundled):
    nodes = dict(
        [
            _seed("pkg", "countries"),
            _model("pkg", "enriched", depends_on=["seed.pkg.countries"]),
            _test("pkg", "unique_countries_code", ["seed.pkg.countries"]),
        ]
    )

    tasks = dbt_factory_bundled.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    assert "countries_test" in by_key
    assert _commands(by_key["countries_test"]) == [
        "dbt test --select fqn:pkg.unique_countries_code,package:pkg,resource_type:test --target dev --indirect-selection empty"
    ]
    assert by_key["countries_test"]["depends_on"] == [{"task_key": "countries_seed"}]
    assert by_key["enriched_model"]["depends_on"] == [{"task_key": "countries_test"}]


def test_tests_on_snapshot_produce_task_and_gate_downstream(dbt_factory_bundled):
    nodes = dict(
        [
            _snapshot("pkg", "orders_snap"),
            _model("pkg", "orders_history", depends_on=["snapshot.pkg.orders_snap"]),
            _test("pkg", "not_null_orders_snap_id", ["snapshot.pkg.orders_snap"]),
        ]
    )

    tasks = dbt_factory_bundled.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    assert "orders_snap_test" in by_key
    assert _commands(by_key["orders_snap_test"]) == [
        "dbt test --select fqn:pkg.not_null_orders_snap_id,package:pkg,resource_type:test --target dev --indirect-selection empty"
    ]
    assert by_key["orders_snap_test"]["depends_on"] == [{"task_key": "orders_snap_snapshot"}]
    assert by_key["orders_history_model"]["depends_on"] == [{"task_key": "orders_snap_test"}]


def test_tests_on_source_produce_standalone_task(dbt_factory_bundled):
    nodes = dict(
        [
            _test("pkg", "unique_raw_customers_id", ["source.pkg.raw.customers"]),
        ]
    )
    sources = dict([_source("pkg", "raw", "customers")])

    tasks = dbt_factory_bundled.create_tasks({"nodes": nodes, "sources": sources})
    by_key = {t["task_key"]: t for t in tasks}

    assert "raw_customers_test" in by_key
    assert _commands(by_key["raw_customers_test"]) == [
        "dbt test --select fqn:pkg.unique_raw_customers_id,package:pkg,resource_type:test --target dev --indirect-selection empty"
    ]
    assert by_key["raw_customers_test"]["depends_on"] == []


def test_flat_mode_emits_one_task_per_test_node_and_gates_downstream(dbt_factory):
    # Per-test mode mirrors `dbt build`: downstream models wait on upstream tests, so a
    # failing `severity: error` test skips downstream via Databricks task failure.
    nodes = dict(
        [
            _model("pkg", "customers"),
            _model("pkg", "orders", depends_on=["model.pkg.customers"]),
            _test("pkg", "unique_customers_id", ["model.pkg.customers"]),
            _test("pkg", "not_null_customers_id", ["model.pkg.customers"]),
        ]
    )

    tasks = dbt_factory.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    assert "unique_customers_id_test" in by_key
    assert "not_null_customers_id_test" in by_key
    assert "customers_test" not in by_key  # no bundling in per-test mode

    assert _commands(by_key["unique_customers_id_test"]) == [
        "dbt test --select fqn:pkg.unique_customers_id,package:pkg,resource_type:test --target dev --indirect-selection empty"
    ]
    assert by_key["unique_customers_id_test"]["depends_on"] == [{"task_key": "customers_model"}]
    # orders depends on customers AND every test attached to customers
    assert {dep["task_key"] for dep in by_key["orders_model"]["depends_on"]} == {
        "customers_model",
        "unique_customers_id_test",
        "not_null_customers_id_test",
    }


def test_flat_mode_cross_model_test_does_not_create_cycle(dbt_factory):
    # Relationship test references BOTH `orders` and `customers`. Without care, extending
    # `orders`'s deps with "tests of upstream (customers)" would pull in the relationship test,
    # which itself depends on `orders` — a direct cycle.
    nodes = dict(
        [
            _model("pkg", "customers"),
            _model("pkg", "orders", depends_on=["model.pkg.customers"]),
            _model("pkg", "payments", depends_on=["model.pkg.orders"]),
            _test("pkg", "unique_customers_id", ["model.pkg.customers"]),
            _test(
                "pkg",
                "relationships_orders_customer_id__ref_customers",
                ["model.pkg.orders", "model.pkg.customers"],
            ),
        ]
    )

    tasks = dbt_factory.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    # orders depends on customers + unique_customers_id, but NOT on the relationship test
    # (that test references orders itself — including it would cycle)
    assert {dep["task_key"] for dep in by_key["orders_model"]["depends_on"]} == {
        "customers_model",
        "unique_customers_id_test",
    }

    # payments (downstream of orders) picks up the relationship test — safe, payments
    # transitively depends on both orders and customers (the test's refs)
    payments_deps = {dep["task_key"] for dep in by_key["payments_model"]["depends_on"]}
    assert "orders_model" in payments_deps
    assert "relationships_orders_customer_id__ref_customers_test" in payments_deps


def test_flat_mode_transitive_cross_model_test_does_not_create_cycle(dbt_factory):
    # Transitive cycle case: test T refs {A, C} where C is downstream of B which is downstream
    # of A. Extending B's deps with "tests of upstream (A)" must NOT add T, because T depends
    # on C and C depends on B → B → T → C → B cycle. Only nodes downstream of both A and C
    # (i.e. downstream of C) should get T.
    nodes = dict(
        [
            _model("pkg", "a"),
            _model("pkg", "b", depends_on=["model.pkg.a"]),
            _model("pkg", "c", depends_on=["model.pkg.b"]),
            _model("pkg", "d", depends_on=["model.pkg.c"]),
            _test("pkg", "relationship_a_c", ["model.pkg.a", "model.pkg.c"]),
        ]
    )

    tasks = dbt_factory.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    # B's ancestors = {A}. Test T refs = {A, C}. C ∉ ancestors(B) → skip T.
    assert by_key["b_model"]["depends_on"] == [{"task_key": "a_model"}]
    # C's ancestors = {A, B}. C IS in T.refs → skip T (direct self-reference).
    assert by_key["c_model"]["depends_on"] == [{"task_key": "b_model"}]
    # D's ancestors = {A, B, C}. T.refs = {A, C} ⊆ ancestors(D) → add T.
    d_deps = {dep["task_key"] for dep in by_key["d_model"]["depends_on"]}
    assert d_deps == {"c_model", "relationship_a_c_test"}


def test_flat_mode_tests_gate_downstream_regardless_of_severity(dbt_factory):
    # Gating follows dbt's dependency graph, not a test's severity: a warn test can still fail the
    # run under `--warn-error`, so both warn- and error-severity tests gate their downstream models.
    nodes = dict(
        [
            _model("pkg", "customers"),
            _model("pkg", "orders", depends_on=["model.pkg.customers"]),
            _test("pkg", "unique_customers_id", ["model.pkg.customers"], severity="warn"),
            _test(
                "pkg",
                "not_null_customers_id",
                ["model.pkg.customers"],
                severity="error",
            ),
        ]
    )

    tasks = dbt_factory.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    assert "unique_customers_id_test" in by_key
    assert "not_null_customers_id_test" in by_key

    # orders gates on customers and both attached tests, warn and error alike
    assert {dep["task_key"] for dep in by_key["orders_model"]["depends_on"]} == {
        "customers_model",
        "unique_customers_id_test",
        "not_null_customers_id_test",
    }


def test_flat_mode_test_on_seed_gates_on_seed(dbt_factory):
    nodes = dict(
        [
            _seed("pkg", "countries"),
            _test("pkg", "unique_countries_code", ["seed.pkg.countries"]),
        ]
    )

    tasks = dbt_factory.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    assert by_key["unique_countries_code_test"]["depends_on"] == [{"task_key": "countries_seed"}]


def test_bundled_task_factory_assembles_commands(dbt_factory_bundled):
    test_factory = dbt_factory_bundled.task_factories["test"]
    task = test_factory.create_bundled_task(
        task_key="customers_test",
        selects_by_indirect_selection={"cautious": ["fqn:pkg.unique_customers_id,package:pkg,resource_type:test"]},
        deps_command_name="customers",
        depends_on=["customers_model"],
    )
    assert task.task_key == "customers_test"
    assert task.commands == [
        "dbt test --select fqn:pkg.unique_customers_id,package:pkg,resource_type:test --target dev --indirect-selection cautious"
    ]
    assert task.depends_on == ["customers_model"]


def test_cross_model_test_in_bundled_mode_is_emitted_as_standalone_task(
    dbt_factory_bundled,
):
    # The relationship test spans two models, so it must NOT be collapsed into either model's
    # bundled test task (dbt would hit a TABLE_OR_VIEW_NOT_FOUND on the un-built endpoint).
    # It should emit its own task with deps on both referenced models.
    nodes = dict(
        [
            _model("pkg", "team_cities"),
            _model("pkg", "game_details", depends_on=["model.pkg.team_cities"]),
            _test("pkg", "not_null_team_cities_name", ["model.pkg.team_cities"]),
            _test(
                "pkg",
                "relationships_game_details_winner__team_city__ref_team_cities_",
                ["model.pkg.game_details", "model.pkg.team_cities"],
            ),
        ]
    )

    tasks = dbt_factory_bundled.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    # Single-model test → its own bundled task addressing the exact test node
    assert "team_cities_test" in by_key
    assert _commands(by_key["team_cities_test"]) == [
        "dbt test --select fqn:pkg.not_null_team_cities_name,package:pkg,resource_type:test --target dev --indirect-selection empty"
    ]

    # Cross-model test → its own task, gated on BOTH referenced models
    cross_test_key = "relationships_game_details_winner__team_city__ref_team_cities__test"
    assert cross_test_key in by_key
    assert _commands(by_key[cross_test_key]) == [
        "dbt test --select fqn:pkg.relationships_game_details_winner__team_city__ref_team_cities_,package:pkg,resource_type:test --target dev --indirect-selection empty"
    ]
    assert {dep["task_key"] for dep in by_key[cross_test_key]["depends_on"]} == {
        "team_cities_model",
        "game_details_model",
    }

    # `game_details` has no single-model tests, so no bundled `game_details_test` exists
    assert "game_details_test" not in by_key


def test_single_package_bundled_test_uses_qualified_select(dbt_factory_bundled):
    nodes = dict(
        [
            _model("pkg_a", "customers"),
            _model("pkg_a", "orders", depends_on=["model.pkg_a.customers"]),
            _test("pkg_a", "unique_customers_id", ["model.pkg_a.customers"]),
        ]
    )

    tasks = dbt_factory_bundled.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    assert "customers_test" in by_key
    assert _commands(by_key["customers_test"]) == [
        "dbt test --select fqn:pkg_a.unique_customers_id,package:pkg_a,resource_type:test --target dev --indirect-selection empty"
    ]
    assert by_key["orders_model"]["depends_on"] == [{"task_key": "customers_test"}]


def test_flat_mode_two_tests_sharing_a_name_and_fqn_are_refused(dbt_factory):
    # dbt lets the same custom test name land twice with the same fqn, telling the nodes apart only
    # via the unique_id hash — which dbt exposes as no selector method. The factory cannot prove a
    # selector addresses one without also running the other before its own dependencies are ready,
    # so it refuses rather than emit a task that runs the wrong node.
    nodes = dict(
        [
            _model("pkg", "customers"),
            _model("pkg", "orders", depends_on=["model.pkg.customers"]),
            _test("pkg", "dup_check", ["model.pkg.customers"], test_hash="6ea6b2ac82"),
            _test("pkg", "dup_check", ["model.pkg.customers"], test_hash="a9ab3a6e12"),
        ]
    )

    with pytest.raises(ValueError, match="also runs"):
        dbt_factory.create_tasks({"nodes": nodes})


def test_flat_mode_cross_package_models_get_package_prefixed_keys(dbt_factory):
    # Two packages may ship a model with the same name (materialized to different schemas).
    nodes = dict(
        [
            _model("shop", "stg_orders"),
            _model("subpkg", "stg_orders"),
            _model(
                "shop",
                "mart",
                depends_on=["model.shop.stg_orders", "model.subpkg.stg_orders"],
            ),
        ]
    )

    tasks = dbt_factory.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    assert "shop_stg_orders_model" in by_key
    assert "subpkg_stg_orders_model" in by_key
    assert {dep["task_key"] for dep in by_key["mart_model"]["depends_on"]} == {
        "shop_stg_orders_model",
        "subpkg_stg_orders_model",
    }


def test_bundled_mode_singular_test_named_like_tested_model_keeps_keys_unique(
    dbt_factory_bundled,
):
    # The bundled test task for model `orders` claims `orders_test`, and so does a singular
    # test file named `orders`. Both stay unique (and deploy cannot fail on a duplicate key).
    nodes = dict(
        [
            _model("pkg", "orders"),
            _test("pkg", "unique_orders_id", ["model.pkg.orders"], test_hash="9a1b2c3d4e"),
            _test("pkg", "orders", []),
        ]
    )

    tasks = dbt_factory_bundled.create_tasks({"nodes": nodes})
    keys = [t["task_key"] for t in tasks]
    by_key = {t["task_key"]: t for t in tasks}

    assert len(keys) == len(set(keys))
    assert _commands(by_key["pkg_orders_test"]) == [
        "dbt test --select fqn:pkg.unique_orders_id,package:pkg,resource_type:test --target dev --indirect-selection empty"
    ]
    assert _commands(by_key["pkg_orders_test_2"]) == [
        "dbt test --select fqn:pkg.orders,package:pkg,resource_type:test --target dev --indirect-selection empty"
    ]


def test_generated_tasks_match_expected(dbt_factory):
    """Safety check: the full set of tasks generated for the sample manifest matches the saved
    copy in test_data/expected_tasks.json. If you change the generated output on purpose, refresh
    that file with `make test-update-expected-tasks`.
    """
    manifest = read_dbt_manifest(BASE_PATH + "/test_data/manifest.json")
    tasks = dbt_factory.create_tasks(manifest)

    expected = json.loads(Path(BASE_PATH + "/test_data/expected_tasks.json").read_text())
    assert tasks == expected
