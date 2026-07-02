import os
from tempfile import NamedTemporaryFile
from pathlib import Path
import pytest
import yaml


BASE_PATH = str(Path(__file__).resolve().parent)


def _model(package: str, name: str, depends_on: list[str] | None = None) -> tuple[str, dict]:
    full_name = f"model.{package}.{name}"
    return full_name, {
        "resource_type": "model",
        "name": name,
        "package_name": package,
        "depends_on": {"nodes": depends_on or []},
    }


def _test(package: str, name: str, depends_on: list[str], severity: str = "error") -> tuple[str, dict]:
    full_name = f"test.{package}.{name}"
    return full_name, {
        "resource_type": "test",
        "name": name,
        "package_name": package,
        "depends_on": {"nodes": depends_on},
        "config": {"severity": severity},
    }


def _seed(package: str, name: str) -> tuple[str, dict]:
    full_name = f"seed.{package}.{name}"
    return full_name, {
        "resource_type": "seed",
        "name": name,
        "package_name": package,
        "depends_on": {"nodes": []},
    }


def _snapshot(package: str, name: str, depends_on: list[str] | None = None) -> tuple[str, dict]:
    full_name = f"snapshot.{package}.{name}"
    return full_name, {
        "resource_type": "snapshot",
        "name": name,
        "package_name": package,
        "depends_on": {"nodes": depends_on or []},
    }


def _source(package: str, source_name: str, table: str) -> tuple[str, dict]:
    full_name = f"source.{package}.{source_name}.{table}"
    return full_name, {
        "resource_type": "source",
        "name": table,
        "source_name": source_name,
        "package_name": package,
    }


def test_same_model_name_across_packages_produces_distinct_bundled_test_tasks(dbt_factory_bundled):
    nodes = dict(
        [
            _model("pkg_a", "customers"),
            _model("pkg_b", "customers"),
            _model("pkg_a", "orders", depends_on=["model.pkg_a.customers", "model.pkg_b.customers"]),
            _test("pkg_a", "unique_customers_id", ["model.pkg_a.customers"]),
            _test("pkg_b", "not_null_customers_id", ["model.pkg_b.customers"]),
        ]
    )

    tasks = dbt_factory_bundled.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    assert "tests_model_pkg_a_customers" in by_key
    assert "tests_model_pkg_b_customers" in by_key
    assert by_key["tests_model_pkg_a_customers"]["dbt_task"]["commands"] == [
        "dbt test --select pkg_a.customers --indirect-selection cautious --target dev"
    ]
    assert by_key["tests_model_pkg_b_customers"]["dbt_task"]["commands"] == [
        "dbt test --select pkg_b.customers --indirect-selection cautious --target dev"
    ]
    assert by_key["tests_model_pkg_a_customers"]["depends_on"] == [{"task_key": "model_pkg_a_customers"}]
    assert by_key["tests_model_pkg_b_customers"]["depends_on"] == [{"task_key": "model_pkg_b_customers"}]

    assert {dep["task_key"] for dep in by_key["model_pkg_a_orders"]["depends_on"]} == {
        "tests_model_pkg_a_customers",
        "tests_model_pkg_b_customers",
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

    assert "tests_seed_pkg_countries" in by_key
    assert by_key["tests_seed_pkg_countries"]["dbt_task"]["commands"] == [
        "dbt test --select pkg.countries --indirect-selection cautious --target dev"
    ]
    assert by_key["tests_seed_pkg_countries"]["depends_on"] == [{"task_key": "seed_pkg_countries"}]
    assert by_key["model_pkg_enriched"]["depends_on"] == [{"task_key": "tests_seed_pkg_countries"}]


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

    assert "tests_snapshot_pkg_orders_snap" in by_key
    assert by_key["tests_snapshot_pkg_orders_snap"]["dbt_task"]["commands"] == [
        "dbt test --select pkg.orders_snap --indirect-selection cautious --target dev"
    ]
    assert by_key["tests_snapshot_pkg_orders_snap"]["depends_on"] == [{"task_key": "snapshot_pkg_orders_snap"}]
    assert by_key["model_pkg_orders_history"]["depends_on"] == [{"task_key": "tests_snapshot_pkg_orders_snap"}]


def test_tests_on_source_produce_standalone_task(dbt_factory_bundled):
    nodes = dict(
        [
            _test("pkg", "unique_raw_customers_id", ["source.pkg.raw.customers"]),
        ]
    )
    sources = dict([_source("pkg", "raw", "customers")])

    tasks = dbt_factory_bundled.create_tasks({"nodes": nodes, "sources": sources})
    by_key = {t["task_key"]: t for t in tasks}

    assert "tests_source_pkg_raw_customers" in by_key
    assert by_key["tests_source_pkg_raw_customers"]["dbt_task"]["commands"] == [
        "dbt test --select source:pkg.raw.customers --indirect-selection cautious --target dev"
    ]
    assert by_key["tests_source_pkg_raw_customers"]["depends_on"] == []


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

    assert "test_pkg_unique_customers_id" in by_key
    assert "test_pkg_not_null_customers_id" in by_key
    assert "tests_model_pkg_customers" not in by_key

    assert by_key["test_pkg_unique_customers_id"]["dbt_task"]["commands"] == [
        "dbt test --select unique_customers_id --target dev"
    ]
    assert by_key["test_pkg_unique_customers_id"]["depends_on"] == [{"task_key": "model_pkg_customers"}]
    # orders depends on customers AND every test attached to customers
    assert {dep["task_key"] for dep in by_key["model_pkg_orders"]["depends_on"]} == {
        "model_pkg_customers",
        "test_pkg_unique_customers_id",
        "test_pkg_not_null_customers_id",
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
    assert {dep["task_key"] for dep in by_key["model_pkg_orders"]["depends_on"]} == {
        "model_pkg_customers",
        "test_pkg_unique_customers_id",
    }

    # payments (downstream of orders) picks up the relationship test — safe, payments
    # transitively depends on both orders and customers (the test's refs)
    payments_deps = {dep["task_key"] for dep in by_key["model_pkg_payments"]["depends_on"]}
    assert "model_pkg_orders" in payments_deps
    assert "test_pkg_relationships_orders_customer_id__ref_customers" in payments_deps


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
    assert by_key["model_pkg_b"]["depends_on"] == [{"task_key": "model_pkg_a"}]
    # C's ancestors = {A, B}. C IS in T.refs → skip T (direct self-reference).
    assert by_key["model_pkg_c"]["depends_on"] == [{"task_key": "model_pkg_b"}]
    # D's ancestors = {A, B, C}. T.refs = {A, C} ⊆ ancestors(D) → add T.
    d_deps = {dep["task_key"] for dep in by_key["model_pkg_d"]["depends_on"]}
    assert d_deps == {"model_pkg_c", "test_pkg_relationship_a_c"}


def test_flat_mode_warn_severity_tests_do_not_gate_downstream(dbt_factory):
    # Only error-severity tests gate downstream (matches `dbt build`: dbt exits 0 on warn
    # so a gate wouldn't block anyway; we just keep the DAG cleaner).
    nodes = dict(
        [
            _model("pkg", "customers"),
            _model("pkg", "orders", depends_on=["model.pkg.customers"]),
            _test("pkg", "unique_customers_id", ["model.pkg.customers"], severity="warn"),
            _test("pkg", "not_null_customers_id", ["model.pkg.customers"], severity="error"),
        ]
    )

    tasks = dbt_factory.create_tasks({"nodes": nodes})
    by_key = {t["task_key"]: t for t in tasks}

    # Both test tasks still exist (warn tests still run — they just don't gate anything)
    assert "test_pkg_unique_customers_id" in by_key
    assert "test_pkg_not_null_customers_id" in by_key

    # orders gates on customers + the error-severity test, but NOT the warn-severity one
    assert {dep["task_key"] for dep in by_key["model_pkg_orders"]["depends_on"]} == {
        "model_pkg_customers",
        "test_pkg_not_null_customers_id",
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

    assert by_key["test_pkg_unique_countries_code"]["depends_on"] == [{"task_key": "seed_pkg_countries"}]


def test_bundled_task_factory_assembles_commands(dbt_factory_bundled):
    test_factory = dbt_factory_bundled.task_factories["test"]
    task = test_factory.create_bundled_task(
        task_key="tests_model_pkg_customers",
        select="pkg.customers",
        deps_command_name="customers",
        depends_on=["model_pkg_customers"],
    )
    assert task.task_key == "tests_model_pkg_customers"
    assert task.commands == ["dbt test --select pkg.customers --indirect-selection cautious --target dev"]
    assert task.depends_on == ["model_pkg_customers"]


def test_cross_model_test_in_bundled_mode_is_emitted_as_standalone_task(dbt_factory_bundled):
    # The relationship test spans two models, so it must NOT be collapsed into either model's
    # bundled `_tests` task (dbt would hit a TABLE_OR_VIEW_NOT_FOUND on the un-built endpoint).
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

    # Single-model test → bundled with cautious selection (relationship test is excluded by dbt)
    assert "tests_model_pkg_team_cities" in by_key
    assert by_key["tests_model_pkg_team_cities"]["dbt_task"]["commands"] == [
        "dbt test --select pkg.team_cities --indirect-selection cautious --target dev"
    ]

    # Cross-model test → its own task, gated on BOTH referenced models
    cross_test_key = "test_pkg_relationships_game_details_winner__team_city__ref_team_cities_"
    assert cross_test_key in by_key
    assert by_key[cross_test_key]["dbt_task"]["commands"] == [
        "dbt test --select relationships_game_details_winner__team_city__ref_team_cities_ --target dev"
    ]
    assert {dep["task_key"] for dep in by_key[cross_test_key]["depends_on"]} == {
        "model_pkg_team_cities",
        "model_pkg_game_details",
    }

    # `game_details` has no single-model tests, so no bundled `game_details_tests` exists
    assert "tests_model_pkg_game_details" not in by_key


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

    assert "tests_model_pkg_a_customers" in by_key
    assert by_key["tests_model_pkg_a_customers"]["dbt_task"]["commands"] == [
        "dbt test --select pkg_a.customers --indirect-selection cautious --target dev"
    ]
    assert by_key["model_pkg_a_orders"]["depends_on"] == [{"task_key": "tests_model_pkg_a_customers"}]


def test_create_job_spec_and_update(dbt_factory):
    run_job_spec_test(
        dbt_factory,
        BASE_PATH + "/test_data/job_definition_no_deps.yaml",
    )


def test_create_job_spec_and_update_with_dbt_deps(dbt_factory_with_deps):
    run_job_spec_test(
        dbt_factory_with_deps,
        BASE_PATH + "/test_data/job_definition.yaml",
    )


def test_create_job_spec_and_update_with_selected_dbt_deps(dbt_factory_with_deps_selected):
    run_job_spec_test(
        dbt_factory_with_deps_selected,
        BASE_PATH + "/test_data/job_definition_deps_selected.yaml",
    )


def test_notebook_task_generation(notebook_factory):
    run_job_spec_test(
        notebook_factory,
        BASE_PATH + "/test_data/job_definition_notebook_no_deps.yaml",
    )


def run_job_spec_test(dbt_factory, expected_job_definition_path):
    """Helper function to test databricks job definition generation."""
    dbt_manifest_path = BASE_PATH + "/test_data/manifest.json"
    input_job_definition_path = BASE_PATH + "/test_data/job_definition_template.yaml"

    with NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        actual_job_definition_path = temp_file.name

    try:
        dbt_factory.create_tasks_and_update_job_spec(
            dbt_manifest_path, input_job_definition_path, actual_job_definition_path
        )

        with open(expected_job_definition_path, "r", encoding="utf-8") as file:
            expected_job_definition = yaml.safe_load(file)

        with open(actual_job_definition_path, "r", encoding="utf-8") as file:
            job_definition = yaml.safe_load(file)

        assert job_definition == expected_job_definition
    finally:
        if os.path.exists(actual_job_definition_path):
            os.remove(actual_job_definition_path)


@pytest.mark.skip("Manual testing")
def test_generate(databricks_dbt_factory):
    """Test job definition generation and saving to file."""
    dbt_manifest_path = BASE_PATH + "/test_data/manifest.json"
    job_definition_path = BASE_PATH + "/test_data/job_definition_template.yaml"
    destination_job_definition_path = "job_definition.yaml"

    databricks_dbt_factory.create_tasks_and_update_job_spec(
        dbt_manifest_path, job_definition_path, destination_job_definition_path, "new_job_name"
    )
