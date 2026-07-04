from dataclasses import replace

from databricks_dbt_factory.TaskFactory import TaskFactory
from databricks_dbt_factory.DbtTask import DbtTask
from databricks_dbt_factory.Utils import generate_task_key, bundled_test_key


class DbtFactory:
    """Generates Databricks job task definitions from a dbt manifest."""

    def __init__(
        self,
        task_factories: dict[str, TaskFactory],
        bundle_tests: bool = False,
    ):
        """
        Initializes the dbt factory.

        Args:
            task_factories (dict[str, TaskFactory]): Maps dbt resource types (`model`, `seed`,
                `snapshot`, `test`) to their respective `TaskFactory` instances. Omitting `test`
                disables test-task generation entirely.
            bundle_tests (bool): When True, emit one `tests_<resource>` task per tested resource
                and rewire downstream models/seeds/snapshots to depend on the upstream's
                `tests_<resource>` task so failing tests halt the DAG. When False, emit one task
                per dbt test node.
        """
        self.task_factories = task_factories
        self.bundle_tests = bundle_tests

    def create_tasks(self, dbt_manifest: dict) -> list[dict]:
        """
        Generates the Databricks task dictionaries from a dbt manifest.

        Args:
            dbt_manifest (dict): Parsed dbt manifest content.

        Returns:
            list[dict]: Task dictionaries ready to be injected into the `tasks` list of a
            Databricks job spec.
        """
        tasks = self._create_tasks(dbt_manifest)
        return [task.to_dict() for task in tasks]

    _GATEABLE_TYPES = frozenset({"model", "seed", "snapshot"})
    _DBT_TEST_TARGET_PREFIXES = ("model.", "seed.", "snapshot.", "source.")

    def _create_tasks(self, dbt_manifest: dict) -> list[DbtTask]:
        """
        Builds `DbtTask` instances from the manifest, applying the bundling and gating policies.

        Args:
            dbt_manifest (dict): Parsed dbt manifest content.

        Returns:
            list[DbtTask]: `DbtTask` instances (not yet rendered to dicts).
        """
        dbt_nodes = dbt_manifest.get("nodes", {})
        dbt_sources = dbt_manifest.get("sources", {})

        bundle = "test" in self.task_factories and self.bundle_tests
        single_model_tested: set[str] = set()
        standalone_tests: list[tuple[str, dict]] = []
        tests_by_resource: dict[str, list[tuple[str, frozenset[str]]]] = {}
        ancestors: dict[str, set[str]] = {}
        if bundle:
            single_model_tested, standalone_tests = self._classify_tests(
                dbt_nodes, dbt_sources
            )
        elif "test" in self.task_factories:
            tests_by_resource = self._index_tests_by_resource(dbt_nodes, dbt_sources)
            ancestors = self._compute_ancestors(dbt_nodes, dbt_sources)
        test_key_by_resource = {
            generate_task_key(fn): bundled_test_key(fn) for fn in single_model_tested
        }

        tasks = self._build_resource_tasks(
            dbt_nodes, bundle, test_key_by_resource, tests_by_resource, ancestors
        )

        if bundle:
            tasks.extend(
                self._build_bundled_test_tasks(
                    dbt_nodes, dbt_sources, single_model_tested
                )
            )
            tasks.extend(self._build_standalone_test_tasks(standalone_tests))

        return tasks

    def _compute_ancestors(
        self, dbt_nodes: dict, dbt_sources: dict
    ) -> dict[str, set[str]]:
        """
        Maps each testable resource's full name to the set of resources it transitively depends
        on (not including itself). Used in per-test mode to decide whether a test can safely
        gate a downstream node: a test `T` with refs `R` is only safe to add to node `N`'s
        deps if `R ⊆ ancestors(N)` — i.e. `N` already waits for all of `T`'s endpoints,
        transitively. Otherwise adding `T` would create a cycle (since `T` depends on each
        ref, and some ref might depend on `N`).
        """
        ancestors: dict[str, set[str]] = {}

        def visit(full_name: str) -> set[str]:
            cached = ancestors.get(full_name)
            if cached is not None:
                return cached
            result: set[str] = set()
            info = dbt_nodes.get(full_name) or dbt_sources.get(full_name)
            if info is not None:
                for dep in info.get("depends_on", {}).get("nodes", []):
                    if dep in dbt_nodes or dep in dbt_sources:
                        result.add(dep)
                        result.update(visit(dep))
            ancestors[full_name] = result
            return result

        for full_name in list(dbt_nodes.keys()) + list(dbt_sources.keys()):
            visit(full_name)
        return ancestors

    def _index_tests_by_resource(
        self, dbt_nodes: dict, dbt_sources: dict
    ) -> dict[str, list[tuple[str, frozenset[str]]]]:
        """
        Maps each testable resource's full name to a list of (test_task_key, test_refs) pairs
        for tests whose `severity` is `error` (the default). Warn-severity tests still run but
        are NOT indexed here, so they do not appear in any downstream model's `depends_on` —
        their job is to surface findings, not halt the DAG. This matches `dbt build` semantics:
        dbt itself exits 0 on warn-severity failures, so even if we did gate on them the
        Databricks task would succeed and downstream would run; keeping warn tests out of the
        dep graph just avoids the extra DAG clutter.

        The refs set is carried alongside each test so `_extend_deps_with_upstream_tests` can
        avoid cycles: a test with refs that aren't all ancestors of a candidate node would
        create a cycle if added as that node's dep.
        """
        index: dict[str, list[tuple[str, frozenset[str]]]] = {}
        for node_full_name, node_info in dbt_nodes.items():
            if node_info["resource_type"] != "test":
                continue
            if self._test_severity(node_info) != "error":
                continue
            test_task_key = generate_task_key(node_full_name)
            refs: set[str] = set()
            for dep in node_info.get("depends_on", {}).get("nodes", []):
                if dep.startswith(self._DBT_TEST_TARGET_PREFIXES) and (
                    dep in dbt_nodes or dep in dbt_sources
                ):
                    refs.add(dep)
            frozen_refs = frozenset(refs)
            for resource_full in refs:
                index.setdefault(resource_full, []).append((test_task_key, frozen_refs))
        return index

    @staticmethod
    def _test_severity(test_node_info: dict) -> str:
        """Reads the test's severity from the manifest, defaulting to `error` when unset."""
        config = test_node_info.get("config") or {}
        severity = config.get("severity")
        if isinstance(severity, str):
            return severity.lower()
        return "error"

    @staticmethod
    def _extend_deps_with_upstream_tests(
        node_full_name: str,
        existing_deps: list[str] | None,
        tests_by_resource: dict[str, list[tuple[str, frozenset[str]]]],
        ancestors_by_node: dict[str, set[str]],
    ) -> list[str]:
        """
        Appends task keys of tests that safely gate this node — i.e. tests whose refs are all
        ancestors of the current node. This prevents both direct and transitive cycles: a test
        `T` with refs `R` is added to node `N`'s deps only if `N` transitively depends on every
        resource in `R`. If any ref of `T` is downstream of (or equal to) `N`, adding `T` would
        cycle because `T` already depends on that ref, and the ref depends on `N`.
        """
        extended: list[str] = list(existing_deps or [])
        seen = set(extended)
        node_ancestors = ancestors_by_node.get(node_full_name, set())
        for ancestor in node_ancestors:
            for test_key, test_refs in tests_by_resource.get(ancestor, []):
                if test_key in seen:
                    continue
                if test_refs <= node_ancestors:
                    extended.append(test_key)
                    seen.add(test_key)
        return extended

    def _classify_tests(
        self, dbt_nodes: dict, dbt_sources: dict
    ) -> tuple[set[str], list[tuple[str, dict]]]:
        """
        Classifies test nodes for bundled mode so that no test is silently dropped.

        - Tests with exactly 1 testable dep: will be covered by their resource's bundled
          `tests_<resource>` task under `--indirect-selection cautious`.
        - Tests with >1 testable deps (cross-model, e.g. `relationships`): emitted as their own
          tasks with multi-resource deps — `cautious` filters them out of bundles.
        - Tests with 0 testable deps (singular/custom tests that don't `ref()` or `source()`
          any resource): also emitted as their own tasks, since no bundle would pick them up.

        Returns:
            (single_model_tested, standalone_tests):
                - `single_model_tested`: full names of resources with at least one single-model
                  test — these become `tests_<resource>` bundled tasks.
                - `standalone_tests`: list of `(test_full_name, test_node_info)` for tests
                  that must run as individual tasks (cross-model or zero-dep).
        """
        single_model_tested: set[str] = set()
        standalone_tests: list[tuple[str, dict]] = []
        for node_full_name, node_info in dbt_nodes.items():
            if node_info["resource_type"] != "test":
                continue
            testable_deps: list[str] = []
            for dep in node_info.get("depends_on", {}).get("nodes", []):
                if dep.startswith(self._DBT_TEST_TARGET_PREFIXES) and (
                    dep in dbt_nodes or dep in dbt_sources
                ):
                    testable_deps.append(dep)
            if len(testable_deps) == 1:
                single_model_tested.add(testable_deps[0])
            else:
                standalone_tests.append((node_full_name, node_info))
        return single_model_tested, standalone_tests

    def _build_resource_tasks(
        self,
        dbt_nodes: dict,
        bundle: bool,
        test_key_by_resource: dict[str, str],
        tests_by_resource: dict[str, list[tuple[str, frozenset[str]]]],
        ancestors_by_node: dict[str, set[str]],
    ) -> list[DbtTask]:
        """Builds tasks for every non-test resource (plus per-test tasks when not bundling)."""
        tasks: list[DbtTask] = []
        for node_full_name, node_info in dbt_nodes.items():
            resource_type = node_info["resource_type"]
            if resource_type not in self.task_factories:
                continue
            if bundle and resource_type == "test":
                continue

            task_key = generate_task_key(node_full_name)
            factory = self.task_factories[resource_type]
            task = factory.create_task(node_info["name"], node_info, task_key)

            if resource_type in self._GATEABLE_TYPES:
                if bundle:
                    task = replace(
                        task,
                        depends_on=self._rewire_deps(
                            task.depends_on, test_key_by_resource
                        ),
                    )
                elif tests_by_resource:
                    task = replace(
                        task,
                        depends_on=self._extend_deps_with_upstream_tests(
                            node_full_name,
                            task.depends_on,
                            tests_by_resource,
                            ancestors_by_node,
                        ),
                    )

            tasks.append(task)
        return tasks

    @staticmethod
    def _rewire_deps(
        deps: list[str] | None, test_key_by_resource: dict[str, str]
    ) -> list[str]:
        """Rewrites a dependency on a tested resource to that resource's gating `<resource>_test` task."""
        return [test_key_by_resource.get(dep_key, dep_key) for dep_key in (deps or [])]

    def _build_bundled_test_tasks(
        self,
        dbt_nodes: dict,
        dbt_sources: dict,
        nodes_with_tests: set[str],
    ) -> list[DbtTask]:
        """Emits one `tests_<resource>` task per tested resource using `TestTaskFactory.create_bundled_task`."""
        test_factory = self.task_factories["test"]
        tasks: list[DbtTask] = []
        for full_name in sorted(nodes_with_tests):
            is_source = full_name.startswith("source.")
            info = dbt_sources[full_name] if is_source else dbt_nodes[full_name]
            bare_name = info["name"]
            qualified = f"{info['package_name']}.{bare_name}"
            select = (
                f"source:{info['package_name']}.{info['source_name']}.{bare_name}"
                if is_source
                else qualified
            )
            tasks.append(
                test_factory.create_bundled_task(
                    task_key=bundled_test_key(full_name),
                    select=select,
                    depends_on=[] if is_source else [generate_task_key(full_name)],
                )
            )
        return tasks

    def _build_standalone_test_tasks(
        self,
        standalone_tests: list[tuple[str, dict]],
    ) -> list[DbtTask]:
        """
        Emits one task per standalone test — cross-model tests (e.g. `relationships`) gated on
        every referenced resource, plus any zero-dep singular tests that bundles can't cover.
        """
        test_factory = self.task_factories["test"]
        tasks: list[DbtTask] = []
        for test_full_name, test_info in sorted(
            standalone_tests, key=lambda item: item[0]
        ):
            test_task_key = generate_task_key(test_full_name)
            tasks.append(
                test_factory.create_task(test_info["name"], test_info, test_task_key)
            )
        return tasks
