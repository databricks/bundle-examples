import heapq
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from pathlib import PurePosixPath, PureWindowsPath
from typing import cast

from databricks_dbt_factory.DbtTask import DbtTask
from databricks_dbt_factory.TaskFactory import TaskFactory, TestTaskFactory
from databricks_dbt_factory.Utils import DYNAMIC_VALUE_REFERENCE, build_task_key_maps

# The `unique_id` prefixes of resources a test can be attached to.
_DBT_TEST_TARGET_PREFIXES = ("model.", "seed.", "snapshot.", "source.")


def _flatten_fqn(fqn: list[str]) -> list[str]:
    """
    Flattens an fqn the way dbt does before comparing it, splitting every segment on `.`.

    `is_selected_node` treats dots inside a segment as namespace separators, so a test named
    `check.nested` with fqn `['probe', 'check.nested']` compares as `['probe', 'check', 'nested']` —
    which is why the shorter `probe.check` matches it as a subtree parent.
    """
    return [part for segment in fqn for part in segment.split(".")]


@dataclass
class _SelectionPlan:
    """A dbt selector paired with the indirect-selection mode needed to keep it exact."""

    select: str
    indirect_selection: str


@dataclass
class _Gating:
    """
    What deciding a node's gating test edges needs, in per-test mode.

    `tests` indexes each test under its referenced resources, `ancestors` records strict dbt ancestors,
    `resources_by_task_key` maps immediate emitted dependencies back to manifest resource ids, and
    `eligible_test_keys` memoizes the tests eligible at each resource's downstream frontier.
    """

    tests: dict[str, list[tuple[str, frozenset[str]]]] = field(default_factory=dict)
    ancestors: dict[str, set[str]] = field(default_factory=dict)
    resources_by_task_key: dict[str, str] = field(default_factory=dict)
    eligible_test_keys: dict[str, frozenset[str]] = field(default_factory=dict)


def _candidate_file_names(original_file_path: str) -> frozenset[str]:
    """Returns every base name implied by POSIX and Windows path semantics."""
    return frozenset(
        {
            PurePosixPath(original_file_path).name,
            PureWindowsPath(original_file_path).name,
        }
    )


def _base_file_name(original_file_path: str) -> str:
    """
    Returns the path-flavour-invariant base name dbt's `file:` selector matches.

    dbt assembles `original_file_path` with `os.path.join`/`os.path.relpath` and `FileSelectorMethod`
    splits it with `Path(...).name`, so a path containing a backslash can mean either a Windows hierarchy
    or a literal POSIX file name. Manifest JSON carries no producer-platform metadata. A `file:` term
    is therefore emitted only when both path flavours yield the same base name; otherwise the remaining
    selector terms must prove exactness or generation refuses the resource.
    """
    candidates = _candidate_file_names(original_file_path)
    return next(iter(candidates)) if len(candidates) == 1 else ""


class DbtFactory:
    """A factory for generating Databricks job definitions from dbt manifests."""

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
            bundle_tests (bool): When True, emit one bundled `<resource>_test` task per tested
                resource and rewire downstream models/seeds/snapshots to depend on the upstream's
                bundled test task so failing tests halt the DAG. When False, emit one task per
                dbt test node.
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

        Raises:
            ValueError: If the generated job would exceed Databricks' 1,000-task limit.
        """
        tasks = self._create_tasks(dbt_manifest)
        if len(tasks) > 1_000:
            raise ValueError(
                f"Databricks jobs support at most 1,000 tasks; this manifest generates {len(tasks):,}. "
                f"Reduce the generated resources or enable test bundling."
            )
        return [task.to_dict() for task in tasks]

    _GATEABLE_TYPES = frozenset({"model", "seed", "snapshot"})
    _DBT_TEST_TARGET_PREFIXES = _DBT_TEST_TARGET_PREFIXES

    # Characters that still change how an *explicit* `fqn:` selector is interpreted, so a component
    # containing one cannot be used to address a node. Each verified against dbt 1.12.0 with `dbt ls`.
    #
    #   ' '    union separator (`graph/cli.py` splits the raw spec on spaces) — the fragments then match
    #          independently. dbt rejects a space in a resource *name* outright, but a space in a
    #          *directory* reaches the fqn, and `fqn:probe.my dir.orders` selects nothing.
    #   ','    intersection separator — the component is read as two, matching zero nodes
    #   '*?[]' `fnmatch` pattern syntax, still honoured after the `fqn:` prefix: `fqn:probe.a*star`
    #          selects `a*star` *and* `aXstar`, so the glob is live rather than literal
    #
    # Databricks substitutes complete `{{...}}` dynamic value references in task commands before the
    # task runs. Those references are screened separately; literal single braces and incomplete pairs
    # remain ordinary selector text under `fqn:`.
    #
    # Emitting `fqn:` rather than a bare value is what keeps this list short. dbt's
    # `SelectionCriteria.default_method` dispatches a bare value containing `/` to `MethodName.Path` and
    # one ending `.sql`/`.py`/`.csv` to `MethodName.File`, both of which then match nothing; naming the
    # method explicitly bypasses that heuristic entirely. Verified: bare `probe.orders.sql` and
    # `probe.check/slash` select nothing, while `fqn:probe.orders.sql` and `fqn:probe.check/slash` each
    # resolve to exactly their node. `:` and literal braces are likewise literal under `fqn:`.
    _SELECTOR_METACHARACTERS = frozenset(" ,*?[]")

    @classmethod
    def _node_select(
        cls,
        node_info: dict,
        source_info: dict | None = None,
        peers: dict | None = None,
    ) -> str:
        """
        Returns the dbt `--select` argument addressing exactly one node.

        `peers` is every selectable resource in the manifest, keyed by id, used to prove the finished
        selector matches only `node_info` (see `_assert_exact`). It is optional so the library API and
        unit tests can build a selector for a lone node, but callers with a manifest should pass it:
        without it, exactness is assumed rather than established.

        Every node is addressed the same way — the intersection (`,`, dbt's AND) of every independent
        fact the manifest gives us about it:

            <fqn>,package:<package>,file:<file name>[,test_name:<generic test>]

        No term is exact alone, which is why they are combined rather than chosen between:

        * the **fqn** is matched as a positional path *prefix*, so it also selects nodes nested
          beneath it — and dbt compares a node's fqn with its package stripped too, so a package's
          `models/probe/alpha.sql` is matched by the root project's `pkg.alpha` as well;
        * **`package:`** narrows to the owning package, but matches all of it;
        * **`file:`** narrows to one source file, but matches that base name in every package, and a
          `schema.yml` is shared by every test declared in it;
        * **`test_name:`** narrows a generic test to its type (`not_null`, `unique`), separating tests
          that share a `schema.yml` — but only when their types differ, so two `not_null` tests in one
          file still need the bare **name**, which dbt matches against the fqn's leaf. The name stands
          in for the fqn when the fqn itself is unusable.

        A term is omitted when dbt cannot express it literally or when combining it with the other
        terms would form a Databricks dynamic value reference. Exactness is rechecked against `peers`
        after any omission. `source_info` addresses a source's tests, which dbt selects by
        `source:<package>.<source>.<table>` rather than by fqn.

        **The fqn or the bare name must survive, and the result must then be checked for exactness.**

        dbt has no `unique_id:` selector method, so a selector is always a *predicate*, and its
        exactness has to be established rather than assumed. Requiring the fqn or the bare name is
        necessary — `package:`, `file:`, `resource_type:` and `test_name:` each address a group — but
        is not sufficient. An fqn is a positional prefix over dbt's *flattened* fqn, so it names a
        subtree, not a node:

        * a test named `check.nested` flattens to `[probe, check, nested]`, so the sibling `check`'s
          selector `probe.check` matches it too — even with `package:`, `file:` and `test_name:` all
          present and identical;
        * a unit test on `orders` (`[probe, orders, unit_orders]`) and a data test named
          `orders.unit_orders` (`[probe, orders.unit_orders]`) flatten identically, which `resource_type:`
          does separate;
        * dbt clones a unit test per model version leaving both clones the same fqn, name and file;
        * two generic tests may simply *share* an fqn: dbt does not require test names to be unique and
          disambiguates in the `unique_id` hash only.

        `_assert_exact` checks direct selectors against the manifest. Test selectors whose direct form is
        ambiguous may instead use `_test_selection_plan`, which scopes the selector to one exact parent.

        Exactness is checked per node against the rest of the manifest because it is a property of the
        node and its selectable neighbours, not of one manifest entry in isolation.

        Raises:
            ValueError: when neither the fqn nor the bare name survives, when the final selector cannot
                avoid a Databricks dynamic value reference, or when it also matches another resource.
        """
        if source_info is not None:
            return cls._source_select(source_info)

        # Exactly one of the fqn and the bare name is used, and one of them must be: they are the only
        # terms that address a *single* resource, so a selector without either could run another task's
        # resource. dbt offers no `unique_id:` method — the full set it accepts, confirmed against dbt
        # 1.12.0, is `fqn`, `tag`, `source`, `path`, `file`, `package`, `config`, `test_name`,
        # `test_type`, `resource_type`, `state`, `exposure`, `metric`, `result`, `source_status`,
        # `group`, `version`, `access`, `semantic_model`, `saved_query`, `unit_test`, `selector`.
        terms: list[str] = []
        fqn = node_info.get("fqn") or []
        # The `fqn:` prefix does *not* neutralise graph operators: `fqn:probe.orders+1` still selects
        # `orders` and its children, verified with `dbt ls` on dbt 1.12.0. The boundary check therefore
        # applies to the joined value; naming the method only bypasses the dispatch heuristic.
        if fqn and cls._is_usable_selector(".".join(fqn)) and all(cls._is_usable_component(part) for part in fqn):
            # `fqn:` names the method explicitly so `/` and `.sql` remain literal fqn text instead of
            # dispatching to path or file matching. `fqn:probe.orders.sql` and
            # `fqn:probe.check/slash` each resolve to exactly their node on dbt 1.12.0.
            terms.append(f"fqn:{'.'.join(fqn)}")
        elif cls._is_usable_component(name := node_info.get("name") or "") and cls._is_usable_selector(name):
            # The fqn is unusable, so fall back to the bare resource name, which dbt matches against
            # the fqn's leaf. It is the only term that tells apart two nodes sharing a package, a
            # file and a test type — two `not_null` tests in one `schema.yml`, say. Not used *with* a
            # usable fqn, whose leaf already carries it.
            terms.append(f"fqn:{name}")
        else:
            raise cls._unaddressable(node_info)

        package = node_info.get("package_name") or ""
        if cls._is_usable_component(package):
            terms.append(f"package:{package}")

        file_name = cls._base_file_name(node_info.get("original_file_path") or "")
        if cls._is_usable_component(file_name):
            terms.append(f"file:{file_name}")

        # `resource_type:` separates nodes whose flattened fqns coincide across *types*, which the
        # other terms cannot: a unit test `unit_orders` on `orders` (fqn [probe, orders, unit_orders])
        # and a data test named `orders.unit_orders` (fqn [probe, orders.unit_orders]) flatten to the
        # same string and share their file. Confirmed on dbt 1.12.0: adding `resource_type:unit_test`
        # and `resource_type:test` respectively isolates each to one node.
        #
        # It does *not* undo dbt's indirect selection: `resource_type:test` still admits the attached
        # tests eagerly pulled in with a selected model, because dbt intersects sets that are already
        # expanded. Suppressing that expansion is the selection plan's job, not this term's: direct test
        # plans pin `--indirect-selection empty`, and parent-scoped cautious plans are accepted only when
        # `_eager_expansion_superset` proves the expanded result is the intended test alone.
        resource_type = node_info.get("resource_type") or ""
        if cls._is_usable_component(resource_type):
            terms.append(f"resource_type:{resource_type}")

        test_name = (node_info.get("test_metadata") or {}).get("name") or ""
        if cls._is_usable_component(test_name):
            terms.append(f"test_name:{test_name}")

        select = cls._compose_selector_terms(terms, node_info)
        if peers is not None:
            cls._assert_exact(select, node_info, peers)
        return select

    @classmethod
    def _compose_selector_terms(cls, terms: list[str], node_info: dict) -> str:
        """Joins terms while preserving the required first term and omitting unsafe optional terms."""
        safe_terms = list(terms)
        while match := DYNAMIC_VALUE_REFERENCE.search(select := ",".join(safe_terms)):
            offset = 0
            closing_term = 0
            for index, term in enumerate(safe_terms):
                offset += len(term)
                if match.end() <= offset:
                    closing_term = index
                    break
                offset += 1
            if closing_term == 0:
                raise cls._dynamic_reference(node_info, select)
            safe_terms.pop(closing_term)
        return select

    @classmethod
    def _assert_no_dynamic_reference(cls, select: str, node_info: dict) -> None:
        """Rejects a complete dynamic value reference in a final Databricks task selector."""
        if DYNAMIC_VALUE_REFERENCE.search(select):
            raise cls._dynamic_reference(node_info, select)

    @classmethod
    def _test_selection_plan(cls, test_info: dict, peers: dict) -> _SelectionPlan:
        """
        Builds an exact plan for one direct test task.

        An already-exact test selector runs with indirect selection disabled. If the direct selector
        matches multiple tests, a test with exactly one manifest parent can be isolated by intersecting
        the parent's exact selector with the test selector under `cautious`, provided the conservative
        per-term expansion proof shows that the finished selector can run only the intended test.
        """
        select = cls._node_select(test_info)
        intended = cls._own_ids(test_info, peers)
        selected = set(cls._matching_ids(select, peers))
        if selected == intended:
            return _SelectionPlan(select, "empty")

        surplus = selected - intended
        missing = intended - selected
        if missing or not surplus:
            cls._assert_exact(select, test_info, peers)

        parents = cls._test_parent_ids(test_info)
        if len(parents) != 1:
            cls._assert_exact(select, test_info, peers)
        parent_id = next(iter(parents))
        if parent_id not in peers:
            cls._assert_exact(select, test_info, peers)
        parent_info = peers[parent_id]
        parent_select = cls._node_select(
            parent_info,
            source_info=parent_info if parent_info.get("resource_type") == "source" else None,
            peers=peers,
        )
        scoped_select = f"{parent_select},{select}"
        cls._assert_no_dynamic_reference(scoped_select, test_info)
        if cls._eager_expansion_superset(scoped_select, peers) != intended:
            cls._assert_exact(select, test_info, peers)
        return _SelectionPlan(scoped_select, "cautious")

    @classmethod
    def _eager_expansion_superset(cls, select: str, peers: dict) -> set[str]:
        """
        Returns a conservative superset of a cautious selector's result.

        dbt expands every comma-separated term before intersecting the term results. For each term this
        proof uses eager expansion: its direct matches plus every test with any directly matched parent.
        Cautious expansion can only admit fewer tests, so intersecting these eager term sets remains a
        superset of the finished cautious result. A parent-scoped plan is accepted only when that superset
        is exactly the intended test.

        The intended single-parent test is present by construction: every test term matches it directly,
        and every exact-parent term matches its sole parent and therefore adds the test indirectly.
        """
        possible: set[str] | None = None
        for term in select.split(","):
            direct = set(cls._matching_ids(term, peers))
            expanded = direct | cls._tests_attached_to_any(direct, peers)
            possible = expanded if possible is None else possible & expanded
        return possible or set()

    @classmethod
    def _tests_attached_to_any(cls, parent_ids: set[str], peers: dict) -> set[str]:
        """Returns enabled test ids having at least one manifest parent in `parent_ids`."""
        if isinstance(peers, _SelectorIndex):
            return peers.tests_attached_to_any(parent_ids)
        return {
            full_name
            for full_name, info in peers.items()
            if info.get("resource_type") in {"test", "unit_test"} and cls._test_parent_ids(info) & parent_ids
        }

    @classmethod
    def _test_parent_ids(cls, test_info: dict) -> frozenset[str]:
        """Returns every model, seed, snapshot, or source dependency id, including absent resources."""
        return frozenset(
            dep
            for dep in test_info.get("depends_on", {}).get("nodes", [])
            if dep.startswith(cls._DBT_TEST_TARGET_PREFIXES)
        )

    @classmethod
    def _assert_exact(cls, select: str, node_info: dict, peers: dict) -> None:
        """
        Raises unless `select` runs only the node it was built for.

        Direct test plans pin `--indirect-selection empty`, so their exactness is a plain intersection of
        the emitted terms. Parent-scoped cautious plans apply their additional proof in
        `_test_selection_plan`. Bundled tasks reuse these per-test plans and union only plans with the
        same indirect-selection mode.

        The contract is **equality**, not "no surplus". A selector that matches nothing is just as wrong as
        one that matches too much: `dbt test` and `dbt run` both exit 0 on a zero-match selector, so the
        task would go green having asserted or built nothing.

        The node recognises itself by object identity *or* by `unique_id`: identity alone would call a
        node its own collision if a caller passed a copy, and `unique_id` alone fails on hand-written
        fixtures that omit the field.
        """
        allowed = cls._own_ids(node_info, peers)
        run = set(cls._matching_ids(select, peers))
        surplus = run - allowed
        if surplus:
            raise cls._ambiguous(node_info, select, sorted(surplus))
        missing = allowed - run
        if missing:
            raise cls._selects_nothing(node_info, select, sorted(missing))

    @staticmethod
    def _own_ids(node_info: dict, peers: dict) -> set[str]:
        """
        The `peers` keys that *are* this node, by `unique_id` when present or by object identity.

        `unique_id` is a direct dict lookup, so the common path costs nothing. The identity scan is the
        fallback for hand-written fixtures that omit the field — walking every peer here once per node was
        itself quadratic, and defeated the index added to avoid exactly that.
        """
        own_id = node_info.get("unique_id")
        if own_id is not None and peers.get(own_id) is not None:
            return {own_id}
        return {full_name for full_name, info in peers.items() if info is node_info}

    @staticmethod
    def _base_file_name(original_file_path: str) -> str:
        """The base name dbt's `file:` selector matches — see the module-level `_base_file_name`."""
        return _base_file_name(original_file_path)

    @classmethod
    def _source_select(cls, source_info: dict) -> str:
        """
        Returns the `source:<package>.<source>.<table>` selector for a source's tests.

        A source has no fqn selector of its own, so all three parts must be usable: unlike a node
        there is no other term to fall back on.

        `.` is disallowed on top of the usual metacharacters. It delimits this grammar, which accepts
        at most three parts, so a dot inside one makes four and dbt rejects the whole selector with a
        Runtime Error ("Invalid source selector value") rather than merely selecting nothing —
        confirmed against dbt 1.12.0 with `dbt ls`. A node's fqn is unaffected: there the dot is the
        separator we are already building with, and a dotted segment stays addressable.

        Complete Databricks dynamic value references are checked after assembly, including references
        completed by the separator between the source and table. None of the three source parts can be
        omitted, so such a selector is refused with the unsafe final value in the error.

        The finished string is checked with `_is_usable_selector` too: like a bare name, the whole
        `source:...` is one raw selector, so a trailing `+N` on the table is read as a graph operator
        and matches nothing while `dbt test` still exits 0. Only the boundary matters —
        `source:pkg.raw.2+ord` resolves exactly — so the check goes on the assembled string rather
        than on each part.
        """
        package = source_info.get("package_name") or ""
        source_name = source_info.get("source_name") or ""
        table = source_info.get("name") or ""
        select = f"source:{package}.{source_name}.{table}"
        cls._assert_no_dynamic_reference(select, source_info)
        parts = (package, source_name, table)
        if not all(cls._is_usable_component(part) and "." not in part for part in parts):
            raise cls._unaddressable(source_info)
        if not cls._is_usable_selector(select):
            raise cls._unaddressable(source_info)
        return select

    @classmethod
    def _is_usable_component(cls, value: str) -> bool:
        """Whether `value` can appear inside a selector component and still mean itself."""
        return (
            bool(value)
            and not cls._SELECTOR_METACHARACTERS & set(value)
            and DYNAMIC_VALUE_REFERENCE.search(value) is None
        )

    @classmethod
    def _is_usable_selector(cls, value: str) -> bool:
        """
        Whether a fully assembled selector avoids dbt graph expansion and Databricks substitution.

        dbt reads a trailing `+N` as child depth even after an explicit method prefix, so
        `fqn:probe.orders+1` selects `orders` and its child. Leading `@` and `N+` forms, and `+` inside
        a segment, remain literal under an explicit `fqn:` method; `fqn:@weird`, `fqn:2+orders`,
        `fqn:pkg.+leading`, and `fqn:pkg.raw.2+ord` each address their exact node on dbt 1.12.0.

        Complete `{{...}}` references are unusable because Databricks substitutes them before dbt receives
        the command. The check applies after selector components are joined so references spanning
        components are also rejected.
        """
        return not value.rstrip("0123456789").endswith("+") and DYNAMIC_VALUE_REFERENCE.search(value) is None

    @staticmethod
    def _flat_fqn(fqn: list[str]) -> list[str]:
        """Flattens an fqn as dbt does — see the module-level `_flatten_fqn`."""
        return _flatten_fqn(fqn)

    @classmethod
    def _fqn_term_matches(cls, term: str, node_info: dict) -> bool:
        """
        Whether dbt's fqn selector `term` matches `node_info`.

        Mirrors `QualifiedNameSelectorMethod.node_is_match` on dbt 1.12.0, including the two details
        that make an fqn a *predicate* rather than an identifier:

        * the comparison is a positional walk over the *flattened* fqn, and a selector that runs out of
          parts still matches — so `probe.check` matches `['probe', 'check', 'nested']`, i.e. anything
          nested beneath it, whether the nesting comes from a directory or from a dot in a name;
        * it is retried with the node's own package stripped, so a package's `models/probe/alpha.sql`
          is matched by the root project's `probe.alpha` too.

        Wildcards are not handled: `_is_usable_component` rejects `*?[]` outright, so no term reaching
        here contains one. This mirrors dbt rather than reasoning about it because being *lenient* here
        would mean accepting a selector that matches two nodes, which is the whole bug class; the
        integration suite pins the mirror against `dbt ls`.
        """
        fqn = node_info.get("fqn") or []
        if not fqn:
            # A manifest missing `fqn` is not something dbt produces, but a hand-rolled or truncated one
            # can be, and the selector then falls back to the bare name. dbt would still match that name
            # against the fqn's leaf, so compare against the name rather than declining outright —
            # otherwise the exactness check reports a selector that reaches nothing.
            return bool(node_info.get("name")) and node_info.get("name") == term
        # dbt's `is_versioned` requires the resource type to be a model (`VERSIONED_NODE_TYPES`), not
        # merely that `version` is set — and a unit-test clone *does* carry `version`. Deriving it from
        # the field alone takes dbt's versioned branch for unit tests and so skips its plain
        # `fqn[-1] == term` match, making the mirror stricter than dbt and hiding a real collision on
        # such a node's bare-name selector.
        is_versioned = node_info.get("resource_type") == "model" and node_info.get("version") is not None
        return cls._is_selected_node(fqn, term, is_versioned) or cls._is_selected_node(fqn[1:], term, is_versioned)

    @classmethod
    def _is_selected_node(cls, fqn: list[str], term: str, is_versioned: bool) -> bool:
        """Mirrors dbt's `is_selected_node` for the operator-free, wildcard-free terms we emit."""
        if not fqn:
            return False
        selector_parts = term.split(".")
        if cls._matches_fqn_leaf(fqn, term, selector_parts, is_versioned):
            return True
        flat_fqn = cls._flat_fqn(fqn)
        if len(flat_fqn) < len(selector_parts):
            return False
        for index, part in enumerate(selector_parts):
            if flat_fqn[index] != part:
                return False
        return True

    @staticmethod
    def _matches_fqn_leaf(fqn: list[str], term: str, selector_parts: list[str], is_versioned: bool) -> bool:
        """
        Whether `term` matches the fqn's leaf, dbt's shortcut before the positional walk.

        A versioned model's fqn ends `[..., <name>, v<N>]`, and dbt lets the last two segments match on
        either the `.` or `_` delimiter, so `orders`, `orders.v1` and `orders_v1` all hit
        `['probe', 'orders', 'v1']`.
        """
        if not is_versioned:
            return fqn[-1] == term
        if len(fqn) < 2:
            return False
        return fqn[-2] == term or "_".join(fqn[-2:]) == "_".join(selector_parts[-2:])

    @classmethod
    def _term_matches(cls, term: str, node_info: dict) -> bool:
        """Whether one emitted selector term matches `node_info`."""
        method, _, value = term.partition(":")
        if not _ or method == "fqn":
            # A bare value is still accepted so a hand-written selector keeps working; everything the
            # factory emits now carries the explicit `fqn:` method.
            return cls._fqn_term_matches(value if method == "fqn" else term, node_info)
        if method == "source":
            parts = value.split(".")
            return (
                len(parts) == 3
                and node_info.get("resource_type") == "source"
                and (node_info.get("package_name") or "") == parts[0]
                and (node_info.get("source_name") or "") == parts[1]
                and (node_info.get("name") or "") == parts[2]
            )
        if method == "package":
            return (node_info.get("package_name") or "") == value
        if method == "file":
            # dbt's `FileSelectorMethod` matches the base name *or* its stem, so `file:a.yml` also
            # matches a node declared in `a.yml.yml`. Mirroring only the name would let that collision
            # past `_assert_exact` — confirmed with `dbt ls` on dbt 1.12.0, where the `a.yml` task's
            # selector resolves to the `a.yml.yml` test as well.
            for base in _candidate_file_names(node_info.get("original_file_path") or ""):
                if value in (base, base.rsplit(".", 1)[0] if "." in base else base):
                    return True
            return False
        if method == "resource_type":
            return (node_info.get("resource_type") or "") == value
        if method == "test_name":
            return ((node_info.get("test_metadata") or {}).get("name") or "") == value
        return True  # pragma: no cover - no other method is emitted

    @staticmethod
    def _selector_index(peers: dict) -> dict:
        """Wraps `peers` in the narrowing index used for exactness checks (see `_SelectorIndex`)."""
        return _SelectorIndex(peers)

    @classmethod
    def _matching_ids(cls, select: str, candidates: dict) -> list[str]:
        """
        The ids in `candidates` that `select` matches, by intersecting every term as dbt does.

        This is a *direct* match: it does not model dbt's indirect selection, so it is only exactness
        evidence for a plan that suppresses expansion. Direct test plans pin `--indirect-selection empty`
        and so need nothing further; parent-scoped cautious plans are proved instead by
        `_eager_expansion_superset`, which expands each term itself.

        `candidates` should be a `_SelectorIndex` on any real manifest: scanning every node for every
        node is quadratic, and measurably so — 90 seconds for a 6,000-node manifest. The index narrows the
        scan to the nodes sharing this selector's `package:` and `file:`, which is a handful. A plain dict
        still works, for the unit tests and library callers that pass one.
        """
        terms = select.split(",")
        scan = candidates.narrow(terms) if isinstance(candidates, _SelectorIndex) else candidates
        matched: list[str] = []
        for full_name, info in scan.items():
            if all(cls._term_matches(term, info) for term in terms):
                matched.append(full_name)
        return matched

    @staticmethod
    def _ambiguous(node_info: dict, select: str, also_matched: list[str]) -> ValueError:
        """
        Builds the error raised when a selector is valid but not exact.

        Distinct from `_unaddressable`: nothing about *this* resource's name is wrong, so the remedy is
        about the collision with its neighbours rather than about selector syntax.
        """
        name = node_info.get("name")
        path = node_info.get("original_file_path")
        return ValueError(
            f"Cannot generate a task for {name!r} ({path}): the generated selector for it "
            f"({select}) also runs {', '.join(sorted(also_matched))}. dbt has no unique-id selector, so "
            f"the factory cannot prove a task addresses these separately. It does not search alternate "
            f"spellings once a usable FQN exists, and refuses to risk running the others before their own "
            f"dependencies have completed. Rename {name!r} so that its dotted "
            f"name neither matches nor prefixes a "
            f"sibling's, or move it to a file of its own."
        )

    @staticmethod
    def _dynamic_reference(node_info: dict, select: str) -> ValueError:
        """Builds the error for a selector Databricks would interpret as a dynamic value reference."""
        name = node_info.get("name")
        path = node_info.get("original_file_path")
        return ValueError(
            f"Cannot generate a task for {name!r} ({path}): the final selector ({select}) contains a "
            f"Databricks dynamic value reference. Rename the resource or file so its selector terms do "
            f"not form a complete reference."
        )

    @staticmethod
    def _selects_nothing(node_info: dict, select: str, missing: list[str]) -> ValueError:
        """
        Builds the error raised when a selector fails to reach what the task is meant to run.

        Distinct from `_ambiguous`, which is the opposite failure. This one is easy to overlook because it
        is silent at run time: `dbt test` and `dbt run` exit 0 on a selector that matches nothing, so the
        task goes green having asserted or built nothing at all.
        """
        name = node_info.get("name")
        path = node_info.get("original_file_path")
        return ValueError(
            f"Cannot generate a task for {name!r} ({path}): the selector dbt offers for it ({select}) "
            f"does not reach {', '.join(missing)}. dbt exits 0 for a selector that matches nothing, so "
            f"the task would report success having run nothing. This is a bug in selector construction "
            f"rather than something to fix in the project — please report it."
        )

    @staticmethod
    def _unaddressable(node_info: dict) -> ValueError:
        """
        Builds the error raised when no selector can address a node.

        This message is the whole of what a CLI user sees (`main` reports it without a traceback), so
        it leads with the resource and the remedy and keeps the reasoning to one closing line.
        """
        name = node_info.get("name")
        path = node_info.get("original_file_path")
        return ValueError(
            f"Cannot generate a task for {name!r} ({path}): dbt cannot select it uniquely. "
            f"Rename the resource or its file so that it does not end with a dbt graph operator (a "
            f"trailing +N), contains none of a space, comma or one of *?[], and contains no complete "
            f"Databricks dynamic value reference (`{{{{...}}}}`) — or, for a source, a dot. Without a "
            f"usable name or path, the only terms left match a group of "
            f"resources, so the task could run another task's resource."
        )

    def _create_tasks(self, dbt_manifest: dict) -> list[DbtTask]:
        """
        Builds `DbtTask` instances from the manifest, applying the bundling and gating policies.

        Args:
            dbt_manifest (dict): Parsed dbt manifest content.

        Returns:
            list[DbtTask]: `DbtTask` instances (not yet rendered to dicts).
        """
        dbt_nodes = self._enabled_only(dbt_manifest.get("nodes", {}))
        dbt_sources = self._enabled_only(dbt_manifest.get("sources", {}))
        dbt_unit_tests = self._enabled_only(dbt_manifest.get("unit_tests", {}))

        # All directly selectable resources participate in selector exactness and test selection-plan
        # checks, including sources even though no emitted command builds a source directly.
        peers = _SelectorIndex({**dbt_nodes, **dbt_unit_tests, **dbt_sources})

        bundle = "test" in self.task_factories and self.bundle_tests
        bundled_tests: dict[str, list[tuple[str, dict]]] = {}
        standalone_tests: list[tuple[str, dict]] = []
        if bundle:
            bundled_tests, standalone_tests = self._classify_tests(dbt_nodes, dbt_sources, dbt_unit_tests)
        standalone_test_ids = {full_name for full_name, _ in standalone_tests}

        # Unit tests live under the manifest `unit_tests` key, not `nodes`. In per-test mode each
        # gets its own task (those whose target model is absent are skipped), so include their ids
        # here to receive a task key from `build_task_key_maps`.
        unit_test_ids = (
            self._emitted_unit_test_ids(dbt_unit_tests, dbt_nodes)
            if not bundle and "test" in self.task_factories
            else []
        )

        task_ids = []
        for full_name, info in dbt_nodes.items():
            if self._node_gets_own_task(full_name, info, bundle, standalone_test_ids):
                task_ids.append(full_name)
        task_ids += unit_test_ids
        task_keys, bundled_test_keys = build_task_key_maps(task_ids, sorted(bundled_tests))

        gating = _Gating()
        if not bundle and "test" in self.task_factories:
            indexed_tests = self._index_tests_by_resource(dbt_nodes, dbt_sources, dbt_unit_tests, task_keys)
            gating = _Gating(
                tests=indexed_tests,
                ancestors=self._compute_ancestors(dbt_nodes, dbt_sources) if indexed_tests else {},
                resources_by_task_key={task_key: full_name for full_name, task_key in task_keys.items()},
            )

        tasks = self._build_resource_tasks(
            dbt_nodes,
            bundle,
            task_keys,
            bundled_test_keys,
            gating,
            peers,
        )

        if bundle:
            tasks.extend(
                self._build_bundled_test_tasks(
                    dbt_nodes,
                    dbt_sources,
                    bundled_tests,
                    task_keys,
                    bundled_test_keys,
                    peers,
                )
            )
            tasks.extend(self._build_standalone_test_tasks(standalone_tests, task_keys, peers))
        elif "test" in self.task_factories:
            tasks.extend(self._build_unit_test_tasks(dbt_unit_tests, task_keys, peers))

        return tasks

    @staticmethod
    def _enabled_only(entries: dict) -> dict:
        """
        Drops entries dbt has disabled.

        dbt normally files an `enabled=false` resource under the manifest's own `disabled` key, which
        we never read — but not always: a versioned model whose declared version has no file leaves
        its test in `nodes` with `config.enabled` false. dbt selects nothing for such a node, and
        `dbt test` on a zero-match selector still exits 0, so a task built from it would go green
        having asserted nothing. Filtering here rather than at each decision site keeps the task-key
        map, the bundling classification and the dependency graph working from one view of the
        manifest. Confirmed against dbt 1.12.0.
        """
        return {
            full_name: info
            for full_name, info in entries.items()
            if (info.get("config") or {}).get("enabled") is not False
        }

    def _node_gets_own_task(self, full_name: str, node_info: dict, bundle: bool, standalone_test_ids: set[str]) -> bool:
        """
        Whether a `dbt_nodes` entry becomes its own task (and so receives a task key). True for any
        resource type with a factory, except single-resource test nodes in bundle mode — those fold
        into their resource's bundled test task. The single authority for this decision, so the
        task-key map and the task-building loops stay in agreement.
        """
        resource_type = node_info["resource_type"]
        if resource_type not in self.task_factories:
            return False
        if bundle and resource_type == "test" and full_name not in standalone_test_ids:
            return False
        return True

    def _emitted_unit_test_ids(self, dbt_unit_tests: dict, dbt_nodes: dict) -> list[str]:
        """
        Full names of the unit tests that become their own task in per-test mode: those whose
        target model resolves and is present in the manifest. This is the emission decision for
        unit tests — the returned ids enter `task_ids`, so a unit test's presence in `task_keys`
        is how every consumer knows it was emitted.

        Each versioned unit-test clone receives its own task and depends on its exact model version.
        """
        emitted: list[str] = []
        for full_name, info in dbt_unit_tests.items():
            model_full_name = self._unit_test_model(info)
            if model_full_name is not None and model_full_name in dbt_nodes:
                emitted.append(full_name)
        return emitted

    def _compute_ancestors(self, dbt_nodes: dict, dbt_sources: dict) -> dict[str, set[str]]:
        """
        Maps each testable resource's full name to the set of resources it transitively depends
        on (not including itself). Used in per-test mode to decide whether a test can safely
        gate a downstream node: a test `T` with refs `R` is only safe to add to node `N`'s
        deps if `R ⊆ ancestors(N)` — i.e. `N` already waits for all of `T`'s endpoints,
        transitively. Otherwise adding `T` would create a cycle (since `T` depends on each
        ref, and some ref might depend on `N`).
        """
        resources = {**dbt_nodes, **dbt_sources}
        dependencies: dict[str, set[str]] = {}
        dependents: dict[str, list[str]] = {full_name: [] for full_name in resources}
        for full_name, info in resources.items():
            direct_dependencies = {
                dependency for dependency in info.get("depends_on", {}).get("nodes", []) if dependency in resources
            }
            dependencies[full_name] = direct_dependencies
            for dependency in direct_dependencies:
                dependents[dependency].append(full_name)

        unresolved_counts = {
            full_name: len(direct_dependencies) for full_name, direct_dependencies in dependencies.items()
        }
        ready = [full_name for full_name, count in unresolved_counts.items() if count == 0]
        heapq.heapify(ready)
        ancestors: dict[str, set[str]] = {}
        while ready:
            full_name = heapq.heappop(ready)
            node_ancestors: set[str] = set()
            for dependency in sorted(dependencies[full_name]):
                node_ancestors.add(dependency)
                node_ancestors.update(ancestors[dependency])
            ancestors[full_name] = node_ancestors

            for dependent in sorted(dependents[full_name]):
                unresolved_counts[dependent] -= 1
                if unresolved_counts[dependent] == 0:
                    heapq.heappush(ready, dependent)

        if len(ancestors) != len(resources):
            unresolved = {full_name for full_name, count in unresolved_counts.items() if count > 0}
            cycle = self._dependency_cycle(dependencies, unresolved)
            raise ValueError(
                f"Cannot compute test gates because the manifest contains the dependency cycle "
                f"{' -> '.join(cycle)}. Regenerate the manifest after removing the cycle."
            )
        return ancestors

    @staticmethod
    def _dependency_cycle(dependencies: dict[str, set[str]], candidates: set[str]) -> list[str]:
        """Returns one deterministic cycle from a graph that could not be topologically ordered."""
        active = 1
        complete = 2
        state: dict[str, int] = {}
        for start in sorted(candidates):
            if state.get(start) == complete:
                continue

            path = [start]
            positions = {start: 0}
            state[start] = active
            stack: list[tuple[str, Iterator[str]]] = [(start, iter(sorted(dependencies[start] & candidates)))]
            while stack:
                full_name, direct_dependencies = stack[-1]
                try:
                    dependency = next(direct_dependencies)
                except StopIteration:
                    stack.pop()
                    path.pop()
                    positions.pop(full_name)
                    state[full_name] = complete
                    continue

                dependency_state = state.get(dependency)
                if dependency_state is None:
                    positions[dependency] = len(path)
                    path.append(dependency)
                    state[dependency] = active
                    stack.append((dependency, iter(sorted(dependencies[dependency] & candidates))))
                elif dependency_state == active:
                    return path[positions[dependency] :] + [dependency]

        raise RuntimeError("A non-topological dependency graph did not contain a cycle.")

    def _index_tests_by_resource(
        self, dbt_nodes: dict, dbt_sources: dict, dbt_unit_tests: dict, task_keys: dict[str, str]
    ) -> dict[str, list[tuple[str, frozenset[str]]]]:
        """
        Maps each testable resource's full name to a list of (test_task_key, test_refs) pairs
        for every emitted data test. A test's task exit status decides whether the dependency blocks:
        warn-severity tests normally succeed, while `--warn-error` can make the same task fail. Keeping
        one graph rule preserves dbt's ordering without reproducing its option-dependent severity logic.

        Unit tests are indexed too. A unit test has no severity — it always fails the run — so it
        always gates. Only unit tests that were emitted as tasks (present in `task_keys`) are
        indexed, so a downstream node never gates on a unit-test task that was skipped.

        The refs set is carried alongside each test so `_extend_deps_with_upstream_tests` can
        avoid cycles: a test with refs that aren't all ancestors of a candidate node would
        create a cycle if added as that node's dep.
        """
        index: dict[str, list[tuple[str, frozenset[str]]]] = {}
        for node_full_name, node_info in dbt_nodes.items():
            if node_info["resource_type"] != "test":
                continue
            if node_full_name in task_keys:
                self._index_test(index, task_keys[node_full_name], node_info, dbt_nodes, dbt_sources)

        for unit_test_full_name, unit_test_info in dbt_unit_tests.items():
            if unit_test_full_name in task_keys:
                self._index_test(index, task_keys[unit_test_full_name], unit_test_info, dbt_nodes, dbt_sources)
        return index

    def _index_test(
        self,
        index: dict[str, list[tuple[str, frozenset[str]]]],
        test_task_key: str,
        test_info: dict,
        dbt_nodes: dict,
        dbt_sources: dict,
    ) -> None:
        """Indexes a test (data or unit) under each resource it references, carrying its ref set."""
        refs = self._testable_refs(test_info, dbt_nodes, dbt_sources)
        for resource_full in refs:
            index.setdefault(resource_full, []).append((test_task_key, refs))

    def _testable_refs(self, test_info: dict, dbt_nodes: dict, dbt_sources: dict) -> frozenset[str]:
        """Returns the models/seeds/snapshots/sources a test references, as present in the manifest."""
        refs: set[str] = set()
        for dep in test_info.get("depends_on", {}).get("nodes", []):
            if dep.startswith(self._DBT_TEST_TARGET_PREFIXES) and (dep in dbt_nodes or dep in dbt_sources):
                refs.add(dep)
        return frozenset(refs)

    @staticmethod
    def _unit_test_model(unit_test_info: dict) -> str | None:
        """
        Returns the full name of the model a unit test targets, or None if it can't be resolved.

        Prefers dbt's already-resolved `depends_on.nodes[0]`, which is the authority: dbt resolves
        the `model` field to a node id at parse time and rewrites unit tests on *versioned* models
        to target `model.<pkg>.<name>.v<N>` while leaving `model` as the bare name. Rebuilding
        `model.<pkg>.<model>` from the `model` field would therefore miss versioned models
        entirely (and dbt's `<name> <version>` spelling of the field), silently dropping the unit
        test. Falls back to that reconstruction only when `depends_on` is absent, so manifests
        that predate it keep working.
        """
        for dep in unit_test_info.get("depends_on", {}).get("nodes", []):
            if dep.startswith("model."):
                return dep
        model = unit_test_info.get("model")
        package = unit_test_info.get("package_name")
        if model and package:
            return f"model.{package}.{model}"
        return None

    @classmethod
    def _extend_deps_with_upstream_tests(
        cls,
        node_full_name: str,
        existing_deps: list[str] | None,
        gating: _Gating,
    ) -> list[str]:
        """
        Adds safe test gates at the first downstream frontier.

        A test is eligible for node `N` when all of its refs are strict ancestors of `N`. Tests already
        eligible at an immediate emitted dependency are inherited through that dependency and need not be
        repeated. The remaining tests are the first frontier where the full ref set has become available.
        """
        deps: list[str] = list(existing_deps or [])
        eligible = cls._eligible_test_keys(node_full_name, gating)
        inherited: set[str] = set()
        for dependency_key in deps:
            dependency = gating.resources_by_task_key.get(dependency_key)
            if dependency is not None:
                inherited.update(cls._eligible_test_keys(dependency, gating))
        deps.extend(sorted(eligible - inherited - set(deps)))
        return deps

    @staticmethod
    def _eligible_test_keys(node_full_name: str, gating: _Gating) -> frozenset[str]:
        """Returns and caches tests whose complete ref set is among the node's strict ancestors."""
        cached = gating.eligible_test_keys.get(node_full_name)
        if cached is not None:
            return cached

        ancestors = gating.ancestors.get(node_full_name, set())
        eligible: set[str] = set()
        for ancestor in ancestors:
            for test_key, test_refs in gating.tests.get(ancestor, []):
                if test_refs <= ancestors:
                    eligible.add(test_key)
        result = frozenset(eligible)
        gating.eligible_test_keys[node_full_name] = result
        return result

    def _classify_tests(
        self, dbt_nodes: dict, dbt_sources: dict, dbt_unit_tests: dict
    ) -> tuple[dict[str, list[tuple[str, dict]]], list[tuple[str, dict]]]:
        """
        Classifies test nodes for bundled mode so that no test is silently dropped.

        - Tests with exactly 1 testable dep: added by id to that resource's bundled
          `<resource>_test` task. Each receives its own exact selection plan before the plans are
          unioned by indirect-selection mode.
        - Tests with >1 testable deps (cross-resource, e.g. `relationships`): emitted as their own
          tasks with every available model, seed, or snapshot dependency.
        - Tests with 0 testable deps (singular/custom tests that don't `ref()` or `source()`
          any resource): also emitted as their own tasks, since no bundle would pick them up.

        Unit tests are assigned explicitly to their resolved model bundle. A model with only unit
        tests therefore still gets a bundled task without relying on indirect selection to discover it.

        Returns:
            (bundled_tests, standalone_tests):
                - `bundled_tests`: exact data and unit test nodes grouped by the resource whose
                  bundled task runs them.
                - `standalone_tests`: list of `(test_full_name, test_node_info)` for tests
                  that must run as individual tasks (cross-model or zero-dep).
        """
        bundled_tests: dict[str, list[tuple[str, dict]]] = {}
        standalone_tests: list[tuple[str, dict]] = []
        for node_full_name, node_info in dbt_nodes.items():
            if node_info["resource_type"] != "test":
                continue
            testable_deps = self._testable_refs(node_info, dbt_nodes, dbt_sources)
            if len(testable_deps) == 1:
                resource_id = next(iter(testable_deps))
                bundled_tests.setdefault(resource_id, []).append((node_full_name, node_info))
            else:
                standalone_tests.append((node_full_name, node_info))

        for unit_test_full_name, unit_test_info in dbt_unit_tests.items():
            model_full_name = self._unit_test_model(unit_test_info)
            if model_full_name is not None and model_full_name in dbt_nodes:
                bundled_tests.setdefault(model_full_name, []).append((unit_test_full_name, unit_test_info))
        return bundled_tests, standalone_tests

    def _build_resource_tasks(
        self,
        dbt_nodes: dict,
        bundle: bool,
        task_keys: dict[str, str],
        bundled_test_keys: dict[str, str],
        gating: _Gating,
        peers: dict,
    ) -> list[DbtTask]:
        """Builds tasks for every non-test resource, plus per-test tasks when not bundling."""
        # A tested resource resolves to its bundle; sources gain a scheduled key only through this map.
        dependency_task_keys = {**task_keys, **bundled_test_keys} if bundle else task_keys
        tasks: list[DbtTask] = []
        for node_full_name, node_info in dbt_nodes.items():
            if node_full_name not in task_keys:
                continue
            if bundle and node_info["resource_type"] == "test":
                # Standalone tests are keyed but built by `_build_standalone_test_tasks`, not here.
                continue

            resource_type = node_info["resource_type"]
            task_key = task_keys[node_full_name]
            factory = self.task_factories[resource_type]
            if resource_type == "test":
                plan = self._test_selection_plan(node_info, peers)
                task = cast(TestTaskFactory, factory).create_task(
                    plan.select,
                    node_info["name"],
                    node_info,
                    task_key,
                    task_keys,
                    indirect_selection=plan.indirect_selection,
                )
            else:
                task = factory.create_task(
                    self._node_select(node_info, peers=peers),
                    node_info["name"],
                    node_info,
                    task_key,
                    dependency_task_keys,
                )

            if resource_type in self._GATEABLE_TYPES and not bundle:
                task = self._gate_task(task, node_full_name, gating)
            tasks.append(task)
        return tasks

    def _gate_task(
        self,
        task: DbtTask,
        node_full_name: str,
        gating: _Gating,
    ) -> DbtTask:
        """Adds per-test-mode gates at the first downstream frontier."""
        if not gating.tests:
            return task
        deps = self._extend_deps_with_upstream_tests(node_full_name, task.depends_on, gating)
        return replace(task, depends_on=deps)

    def _build_bundled_test_tasks(
        self,
        dbt_nodes: dict,
        dbt_sources: dict,
        bundled_tests: dict[str, list[tuple[str, dict]]],
        task_keys: dict[str, str],
        bundled_test_keys: dict[str, str],
        peers: dict,
    ) -> list[DbtTask]:
        """Emits one task per tested resource from unions of exact per-test selection plans."""
        test_factory = cast(TestTaskFactory, self.task_factories["test"])
        tasks: list[DbtTask] = []
        for full_name, tests in sorted(bundled_tests.items()):
            is_source = full_name.startswith("source.")
            info = dbt_sources[full_name] if is_source else dbt_nodes[full_name]
            # A source never gets a task of its own, so it has no gate. Any other parent must, or the
            # bundle would run its tests with nothing ordering them after the resource was built. Raise
            # rather than emit the ungated task: `resource_type` having no registered factory is a
            # supported library configuration (see `_node_gets_own_task`), and a `KeyError` here would
            # escape `main`'s handler as a traceback that names no resource.
            if not is_source and full_name not in task_keys:
                raise ValueError(
                    f"Cannot bundle the tests of {full_name!r}: no task was generated for it, so the "
                    f"bundled test task would run unordered against it. Register a task factory for "
                    f"{info.get('resource_type')!r} resources, or generate one task per test instead of "
                    f"bundling."
                )
            tasks.append(
                test_factory.create_bundled_task(
                    task_key=bundled_test_keys[full_name],
                    selects_by_indirect_selection=self._bundled_selects_by_mode(tests, peers),
                    deps_command_name=info["name"],
                    depends_on=[] if is_source else [task_keys[full_name]],
                )
            )
        return tasks

    @classmethod
    def _bundled_selects_by_mode(cls, tests: list[tuple[str, dict]], peers: dict) -> dict[str, list[str]]:
        """Builds and validates the deterministic selector groups for one test bundle."""
        selects_by_mode: dict[str, list[str]] = {}
        test_info_by_mode: dict[str, dict] = {}
        for _, test_info in sorted(tests, key=lambda item: item[0]):
            plan = cls._test_selection_plan(test_info, peers)
            selects_by_mode.setdefault(plan.indirect_selection, []).append(plan.select)
            test_info_by_mode.setdefault(plan.indirect_selection, test_info)
        for mode, selects in selects_by_mode.items():
            cls._assert_no_dynamic_reference(" ".join(sorted(selects)), test_info_by_mode[mode])
        return selects_by_mode

    def _build_standalone_test_tasks(
        self,
        standalone_tests: list[tuple[str, dict]],
        task_keys: dict[str, str],
        peers: dict,
    ) -> list[DbtTask]:
        """
        Emits one task per standalone test — cross-resource tests (e.g. `relationships`) gated on
        every referenced model, seed, or snapshot task, plus zero-dep singular tests that bundles
        cannot cover.
        """
        test_factory = cast(TestTaskFactory, self.task_factories["test"])
        tasks: list[DbtTask] = []
        for test_full_name, test_info in sorted(standalone_tests, key=lambda item: item[0]):
            test_task_key = task_keys[test_full_name]
            plan = self._test_selection_plan(test_info, peers)
            tasks.append(
                test_factory.create_task(
                    plan.select,
                    test_info["name"],
                    test_info,
                    test_task_key,
                    task_keys,
                    indirect_selection=plan.indirect_selection,
                )
            )
        return tasks

    def _build_unit_test_tasks(
        self,
        dbt_unit_tests: dict,
        task_keys: dict[str, str],
        peers: dict,
    ) -> list[DbtTask]:
        """
        Emits one task per unit test, selected by its full FQN and gated on the model it tests.
        Only unit tests that received a task key (see `_emitted_unit_test_ids`) are emitted; unit
        tests whose target model is absent from the manifest were never keyed and are skipped, so
        their task can't gate on a model task that is never created. Used in per-test mode; in
        bundled mode unit tests are assigned explicitly to their model's exact-selector bundle.

        Versioned unit-test clones receive independent parent-scoped selection plans, so each task waits
        only for and runs only against its exact model version.
        """
        test_factory = cast(TestTaskFactory, self.task_factories["test"])

        tasks: list[DbtTask] = []
        for unit_test_full_name, unit_test_info in sorted(dbt_unit_tests.items()):
            if unit_test_full_name not in task_keys:
                continue
            plan = self._test_selection_plan(unit_test_info, peers)
            tasks.append(
                test_factory.create_task(
                    plan.select,
                    unit_test_info["name"],
                    unit_test_info,
                    task_keys[unit_test_full_name],
                    task_keys,
                    indirect_selection=plan.indirect_selection,
                )
            )
        return tasks


class _SelectorIndex(dict):
    """
    The manifest's selectable resources, plus indexes for narrowing an exactness check.

    `_assert_exact` runs once per node, so evaluating each selector against every node makes generation
    quadratic — measured at 90 seconds for a 6,000-node manifest, and real projects are larger. Each
    index maps a term value to the nodes it *could* match, so a check scans a handful of candidates
    instead of the manifest.

    Every bucket is a sound **superset** of the true matches: `_matching_ids` still evaluates the full
    predicate on whatever comes back, so narrowing can only cost time, never change the answer.
    `test_selector_index_narrowing_matches_a_full_scan` pins that equivalence against a full scan.

    Subclasses `dict` so it *is* the peers mapping: callers that only iterate or look up by id need not
    know the indexes exist.
    """

    def __init__(self, peers: dict):
        super().__init__(peers)
        self._by_package: dict[str, dict] = {}
        self._by_file: dict[str, dict] = {}
        self._by_test_name: dict[str, dict] = {}
        self._by_fqn_term: dict[str, dict] = {}
        self._by_version_suffix: dict[str, dict] = {}
        self._tests_by_parent: dict[str, set[str]] = {}
        for full_name, info in peers.items():
            self._add(full_name, info)
            self._index_test_parents(full_name, info, peers)

    def _index_test_parents(self, full_name: str, info: dict, peers: dict) -> None:
        """Indexes a test under each enabled testable parent."""
        if info.get("resource_type") not in {"test", "unit_test"}:
            return
        for parent in info.get("depends_on", {}).get("nodes", []):
            if parent.startswith(_DBT_TEST_TARGET_PREFIXES) and parent in peers:
                self._tests_by_parent.setdefault(parent, set()).add(full_name)

    def _add(self, full_name: str, info: dict) -> None:
        """Files one node under every key a selector term could reach it by."""
        self._by_package.setdefault(info.get("package_name") or "", {})[full_name] = info
        # A path containing a backslash has both POSIX and Windows interpretations. Index every possible
        # base name and stem so narrowing cannot hide a collision under either runtime path flavour.
        for base in _candidate_file_names(info.get("original_file_path") or ""):
            for key in dict.fromkeys((base, base.rsplit(".", 1)[0] if "." in base else base)):
                self._by_file.setdefault(key, {})[full_name] = info
        test_name = (info.get("test_metadata") or {}).get("name") or ""
        if test_name:
            self._by_test_name.setdefault(test_name, {})[full_name] = info
        for term in self._fqn_terms(info):
            self._by_fqn_term.setdefault(term, {})[full_name] = info
        if suffix := self._version_suffix(info):
            self._by_version_suffix.setdefault(suffix, {})[full_name] = info

    def tests_attached_to_any(self, parent_ids: set[str]) -> set[str]:
        """Returns indexed tests having at least one parent in `parent_ids`."""
        tests: set[str] = set()
        for parent_id in parent_ids:
            tests.update(self._tests_by_parent.get(parent_id, ()))
        return tests

    @staticmethod
    def _fqn_terms(info: dict) -> set[str]:
        """
        Every finite fqn term that directly identifies this node under dbt's matching rules.

        The positional matcher accepts every prefix of the flattened fqn, both with and without the
        package. The leaf shortcut additionally accepts the raw leaf (or the model name for a versioned
        model), which can differ from a flattened prefix when it contains a dot. Version suffix matching
        is indexed separately because dbt ignores any earlier selector components in that shortcut.
        """
        fqn = info.get("fqn") or []
        if not fqn:
            # A truncated hand-written manifest can omit fqn; the matcher then falls back to the name.
            name = info.get("name") or ""
            return {name} if name else set()
        terms: set[str] = set()
        for candidate in (fqn, fqn[1:]):
            flat = _flatten_fqn(candidate)
            terms.update(".".join(flat[:length]) for length in range(1, len(flat) + 1))
        if info.get("resource_type") == "model" and info.get("version") is not None and len(fqn) >= 2:
            terms.add(fqn[-2])
        else:
            terms.add(fqn[-1])
        return terms

    @staticmethod
    def _version_suffix(info: dict) -> str:
        """The suffix used by dbt's versioned-model leaf shortcut, if this node has one."""
        fqn = info.get("fqn") or []
        if info.get("resource_type") == "model" and info.get("version") is not None and len(fqn) >= 2:
            return "_".join(fqn[-2:])
        return ""

    def narrow(self, terms: list[str]) -> dict:
        """
        The candidate set for `terms` — a superset of the true matches, so the caller still decides.

        Returns the smallest single bucket rather than intersecting across terms: the intersection is
        also sound (terms are ANDed) but measured slower, because building a set from a bucket the size
        of the manifest costs more than the extra predicate evaluations it saves.
        """
        smallest: dict | None = None
        for term in terms:
            method, _, value = term.partition(":")
            if not _ or method == "fqn":
                bucket = self._fqn_candidates(value if method == "fqn" else term)
            elif method == "package":
                bucket = self._by_package.get(value, {})
            elif method == "file":
                bucket = self._by_file.get(value, {})
            elif method == "test_name":
                bucket = self._by_test_name.get(value, {})
            else:
                continue
            if smallest is None or len(bucket) < len(smallest):
                smallest = bucket
        return self if smallest is None else smallest

    def _fqn_candidates(self, term: str) -> dict:
        """
        The nodes an fqn `term` could match through a positional, leaf, or version-suffix rule.

        Prefixes are indexed as complete terms rather than by their first segment, keeping selectors
        efficient when an ambiguous path makes `file:` unavailable. The version shortcut compares only
        the selector's last two components, so its separate bucket is unioned here.
        """
        candidates = dict(self._by_fqn_term.get(term, {}))
        suffix = "_".join(term.split(".")[-2:])
        candidates.update(self._by_version_suffix.get(suffix, {}))
        return candidates
