import shlex
from abc import ABC, abstractmethod
from collections.abc import Sequence

from databricks_dbt_factory.DbtTask import DbtTask, DbtTaskOptions
from databricks_dbt_factory.Utils import DYNAMIC_VALUE_REFERENCE


_RESERVED_DBT_SELECTION_OPTIONS = frozenset(
    {
        "--select",
        "--models",
        "--model",
        "--exclude",
        "--selector",
        "--resource-type",
        "--resource-types",
        "--exclude-resource-type",
        "--exclude-resource-types",
    }
)
_RESERVED_DBT_PARSE_CONTEXT_OPTIONS = frozenset({"--vars", "--profile", "--profiles-dir", "--project-dir"})
_RESERVED_DBT_SHORT_SELECTION_OPTIONS = frozenset({"-s", "-m"})
_RESERVED_DBT_SHORT_TARGET_OPTIONS = frozenset({"-t"})
_DBT_SHORT_OPTIONS_WITH_ATTACHED_VALUES = frozenset({"-r", "-t"})
_DBT_TARGET_OPTIONS_WITH_SEPARATE_VALUES = frozenset({"--target", "-t"})
_DBT_TARGET_VALUE_ERROR = "dbt target requires a nonempty value."
_EXTRA_DBT_PARSE_CONTEXT_REMEDIES = {
    "--target": "--target",
    "-t": "--target",
    "--profiles-dir": "--profiles-directory",
    "--project-dir": "--project-directory",
}


def _reserved_short_option(token: str, reserved_options: frozenset[str]) -> str | None:
    """Returns a reserved option embedded in one dbt short-option token."""
    if not token.startswith("-") or token.startswith("--"):
        return None

    for character in token[1:]:
        option = f"-{character}"
        if option in reserved_options:
            return option
        if option in _DBT_SHORT_OPTIONS_WITH_ATTACHED_VALUES:
            break
    return None


def _reserved_parse_context_option(token: str) -> str | None:
    """Returns a parse-context option that is unsafe at every validation boundary."""
    long_option = token.partition("=")[0]
    if long_option in _RESERVED_DBT_PARSE_CONTEXT_OPTIONS:
        return long_option
    return None


def _target_option(token: str) -> str | None:
    """Returns the target option represented by one token, including its short form."""
    long_option = token.partition("=")[0]
    if long_option == "--target":
        return long_option
    return _reserved_short_option(token, _RESERVED_DBT_SHORT_TARGET_OPTIONS)


def _reserved_selection_option(token: str) -> str | None:
    """Returns a selection option that conflicts with factory-owned selection."""
    if token == "--":
        return token
    long_option = token.partition("=")[0]
    if long_option in _RESERVED_DBT_SELECTION_OPTIONS:
        return long_option
    return _reserved_short_option(token, _RESERVED_DBT_SHORT_SELECTION_OPTIONS)


def _is_supported_leading_target(token: str) -> bool:
    """Returns whether a token is one of the controlled leading target forms."""
    return (
        token in _DBT_TARGET_OPTIONS_WITH_SEPARATE_VALUES
        or token.startswith("--target=")
        or (token.startswith("-t") and not token.startswith("--") and len(token) > 2)
    )


def _raise_parse_context_error(option: str, reject_target: bool) -> None:
    """Raises the boundary-specific error for a runtime parse-context override."""
    if reject_target:
        dedicated_option = _EXTRA_DBT_PARSE_CONTEXT_REMEDIES.get(option)
        remedy = f" Use the dedicated {dedicated_option} argument instead." if dedicated_option else ""
        raise ValueError(
            f"--extra-dbt-command-options cannot include parse-context option {option!r}.{remedy} "
            "The runtime parse context must match the supplied manifest."
        )
    raise ValueError(
        f"dbt command options cannot include parse-context option {option!r}; "
        "the runtime parse context must match the supplied manifest."
    )


def _validate_dbt_option_token(token: str, token_index: int, reject_target: bool) -> bool:
    """Validates one option token and reports whether its next token is a target value."""
    reserved_option = _reserved_selection_option(token)
    if reserved_option is not None:
        raise ValueError(
            f"dbt command options cannot include selection option {reserved_option!r}; "
            f"the factory owns selection so each task addresses only its intended resource."
        )

    target_option = _target_option(token)
    if target_option is not None:
        if reject_target:
            _raise_parse_context_error(target_option, reject_target=True)
        if token_index != 0 or not _is_supported_leading_target(token):
            raise ValueError(
                "dbt command options can include at most one target, only as the leading "
                f"factory-controlled option; found {target_option!r} elsewhere."
            )
        if token == "--target=":
            raise ValueError(_DBT_TARGET_VALUE_ERROR)
        return token in _DBT_TARGET_OPTIONS_WITH_SEPARATE_VALUES

    parse_context_option = _reserved_parse_context_option(token)
    if parse_context_option is not None:
        _raise_parse_context_error(parse_context_option, reject_target)
    return False


def _validate_dbt_options(dbt_options: str, reject_target: bool) -> None:
    """Rejects options that can invalidate the factory's manifest-derived task guarantees."""
    if DYNAMIC_VALUE_REFERENCE.search(dbt_options):
        raise ValueError(
            "dbt command options cannot contain a Databricks dynamic value reference; "
            "its runtime value could change the resource selection owned by the factory."
        )
    try:
        tokens = shlex.split(dbt_options)
    except ValueError as error:
        raise ValueError(f"Cannot parse dbt command options: {error}.") from error

    option_value_expected = False
    for token_index, token in enumerate(tokens):
        if option_value_expected:
            if not token:
                raise ValueError(_DBT_TARGET_VALUE_ERROR)
            option_value_expected = False
            continue
        option_value_expected = _validate_dbt_option_token(token, token_index, reject_target)
    if option_value_expected:
        raise ValueError(_DBT_TARGET_VALUE_ERROR)


def validate_dbt_options(dbt_options: str) -> None:
    """Validates options supplied to a task factory, where its leading target remains allowed."""
    _validate_dbt_options(dbt_options, reject_target=False)


def validate_extra_dbt_options(dbt_options: str) -> None:
    """Validates CLI extra options, including parse context managed by dedicated arguments."""
    _validate_dbt_options(dbt_options, reject_target=True)


class DbtDependencyResolver:
    @staticmethod
    def resolve(node_info: dict, task_keys: dict[str, str]) -> list[str]:
        """
        Resolves every scheduled direct dbt dependency to its Databricks task key.

        Args:
            node_info (dict): The dbt manifest entry for the node.
            task_keys (dict[str, str]): Effective task key per scheduled dbt dependency.

        Returns:
            list[str]: Resolved upstream task keys.
        """
        deps = node_info.get("depends_on", {}).get("nodes", [])
        resolved_deps = []
        for node_full_name in deps:
            task_key = task_keys.get(node_full_name)
            if task_key is not None:
                resolved_deps.append(task_key)
        return resolved_deps


class TaskFactory(ABC):
    """Abstract base class for creating tasks."""

    def __init__(self, resolver: DbtDependencyResolver, task_options: DbtTaskOptions, dbt_options: str = ""):
        """
        Initializes the TaskFactory.

        Args:
            resolver (DbtDependencyResolver): An instance of DbtDependencyResolver to resolve dependencies.
            task_options (DbtTaskOptions): Options for the task.
            dbt_options (str, optional): Additional DBT options. Defaults to "".
        """
        self.resolver = resolver
        self.task_options = task_options
        self.dbt_options = dbt_options

    @property
    def dbt_options(self) -> str:
        """The validated dbt options appended to every command emitted by this factory."""
        return self._dbt_options

    @dbt_options.setter
    def dbt_options(self, value: str) -> None:
        validate_dbt_options(value)
        self._dbt_options = value

    @abstractmethod
    def create_task(
        self, select: str, deps_command_name: str, dbt_node_info: dict, task_key: str, task_keys: dict[str, str]
    ) -> DbtTask:
        """
        Abstract method to create a task.

        Args:
            select (str): dbt `--select` argument identifying the node (its full dot-joined FQN).
            deps_command_name (str): Bare node name used by `get_dbt_deps_command` to decide whether
                to prepend `dbt deps` (matched against `--dbt-tasks-deps`).
            dbt_node_info (dict): Information about the DBT node.
            task_key (str): Key for the task.
            task_keys (dict[str, str]): Task key per dbt node, for resolving dependencies.

        Returns:
            DbtTask: An instance of Task.
        """

    def get_dbt_deps_command(self, dbt_task_name: str) -> str | None:
        """Adds the dbt deps command if enabled and applicable.
        Only return the command if enabled, and available in the task deps or not specific tasks provided.

        Args:
            dbt_task_name (str): Name of the DBT task.
        """
        if self.task_options.dbt_deps_enabled and (
            not self.task_options.dbt_tasks_deps or dbt_task_name in self.task_options.dbt_tasks_deps
        ):
            return self._build_dbt_command("deps")
        return None

    def _build_dbt_command(
        self,
        subcommand: str,
        *,
        select: str | Sequence[str] | None = None,
        indirect_selection: str | None = None,
    ) -> str:
        """
        Builds and validates one complete dbt command.

        Several selectors are passed as repeated `--select` arguments rather than joined into one, so
        the union does not depend on the consumer preserving shell quoting. dbt unions repeated
        occurrences; confirmed on dbt 1.12.0 under both `empty` and `cautious` indirect selection.
        """
        parts = ["dbt", subcommand]
        if select is not None:
            selectors = [select] if isinstance(select, str) else list(select)
            for selector in selectors:
                parts.extend(("--select", shlex.quote(selector)))
        if self.dbt_options:
            parts.append(self.dbt_options)
        if indirect_selection is not None:
            parts.extend(("--indirect-selection", shlex.quote(indirect_selection)))

        command = " ".join(parts)
        if DYNAMIC_VALUE_REFERENCE.search(command):
            raise ValueError(
                "The final dbt command contains a Databricks dynamic value reference; rename the "
                "selected resource or change the dbt command options so no `{{...}}` reference is formed."
            )
        return command


class ModelTaskFactory(TaskFactory):
    """Factory for creating model tasks."""

    def create_task(
        self, select: str, deps_command_name: str, dbt_node_info: dict, task_key: str, task_keys: dict[str, str]
    ) -> DbtTask:
        """
        Creates a model task.

        Args:
            select (str): dbt `--select` argument identifying the node (its full dot-joined FQN).
            deps_command_name (str): Bare node name used to decide whether to prepend `dbt deps`.
            dbt_node_info (dict): Information about the DBT node.
            task_key (str): Key for the task.
            task_keys (dict[str, str]): Task key per dbt node, for resolving dependencies.

        Returns:
            DbtTask: An instance of Task.
        """
        depends_on = self.resolver.resolve(dbt_node_info, task_keys)

        dbt_deps = self.get_dbt_deps_command(deps_command_name)
        commands = [dbt_deps] if dbt_deps else []
        commands.append(self._build_dbt_command("run", select=select))

        return DbtTask(task_key, commands, self.task_options, depends_on)


class SnapshotTaskFactory(TaskFactory):
    """Factory for creating snapshot tasks."""

    def create_task(
        self, select: str, deps_command_name: str, dbt_node_info: dict, task_key: str, task_keys: dict[str, str]
    ) -> DbtTask:
        """
        Creates a snapshot task.

        Args:
            select (str): dbt `--select` argument identifying the node (its full dot-joined FQN).
            deps_command_name (str): Bare node name used to decide whether to prepend `dbt deps`.
            dbt_node_info (dict): Information about the DBT node.
            task_key (str): Key for the task.
            task_keys (dict[str, str]): Task key per dbt node, for resolving dependencies.

        Returns:
            DbtTask: An instance of Task.
        """
        depends_on = self.resolver.resolve(dbt_node_info, task_keys)

        dbt_deps = self.get_dbt_deps_command(deps_command_name)
        commands = [dbt_deps] if dbt_deps else []
        commands.append(self._build_dbt_command("snapshot", select=select))

        return DbtTask(task_key, commands, self.task_options, depends_on)


class SeedTaskFactory(TaskFactory):
    """Factory for creating seed tasks."""

    def create_task(
        self, select: str, deps_command_name: str, dbt_node_info: dict, task_key: str, task_keys: dict[str, str]
    ) -> DbtTask:
        """
        Creates a seed task.

        Args:
            select (str): dbt `--select` argument identifying the node (its full dot-joined FQN).
            deps_command_name (str): Bare node name used to decide whether to prepend `dbt deps`.
            dbt_node_info (dict): Information about the DBT node.
            task_key (str): Key for the task.
            task_keys (dict[str, str]): Task key per dbt node, for resolving dependencies.

        Returns:
            DbtTask: An instance of Task.
        """
        depends_on = self.resolver.resolve(dbt_node_info, task_keys)

        dbt_deps = self.get_dbt_deps_command(deps_command_name)
        commands = [dbt_deps] if dbt_deps else []
        commands.append(self._build_dbt_command("seed", select=select))

        return DbtTask(task_key, commands, self.task_options, depends_on)


class TestTaskFactory(TaskFactory):
    """Factory for creating test tasks."""

    def create_task(
        self,
        select: str,
        deps_command_name: str,
        dbt_node_info: dict,
        task_key: str,
        task_keys: dict[str, str],
        indirect_selection: str = "empty",
    ) -> DbtTask:
        """
        Creates a test task for a single dbt test node.

        Args:
            select (str): dbt `--select` argument identifying the node (its full dot-joined FQN).
            deps_command_name (str): Bare node name used to decide whether to prepend `dbt deps`.
            dbt_node_info (dict): Information about the DBT node.
            task_key (str): Key for the task.
            task_keys (dict[str, str]): Task key per dbt node, for resolving dependencies.
            indirect_selection (str): dbt indirect-selection mode required by the selection plan.

        Returns:
            DbtTask: An instance of Task.
        """
        depends_on = self.resolver.resolve(dbt_node_info, task_keys)

        dbt_deps = self.get_dbt_deps_command(deps_command_name)
        commands = [dbt_deps] if dbt_deps else []
        # The plan's mode is appended after user options so the command cannot override the selector's
        # correctness contract. Direct test selectors use `empty`; parent-scoped selectors use `cautious`.
        commands.append(self._build_dbt_command("test", select=select, indirect_selection=indirect_selection))

        return DbtTask(task_key, commands, self.task_options, depends_on)

    def create_bundled_task(
        self,
        task_key: str,
        selects_by_indirect_selection: dict[str, list[str]],
        deps_command_name: str,
        depends_on: list[str],
    ) -> DbtTask:
        """
        Creates one Databricks task that runs an exact set of single-resource tests.

        Test selectors with the same indirect-selection mode are joined as one dbt union. Keeping
        modes separate preserves each selector plan's exactness while limiting a bundle to at most
        two test commands (`empty` and `cautious`).

        Args:
            task_key (str): Key for the bundled task.
            selects_by_indirect_selection (dict[str, list[str]]): Exact test selectors grouped by
                the indirect-selection mode required by their selection plans.
            deps_command_name (str): Name used by `get_dbt_deps_command` to decide whether to prepend `dbt deps`.
            depends_on (list[str]): Upstream task keys this bundled task should gate on.

        Returns:
            DbtTask: An instance of Task.
        """
        dbt_deps = self.get_dbt_deps_command(deps_command_name)
        commands = [dbt_deps] if dbt_deps else []
        unsupported_modes = set(selects_by_indirect_selection) - {"empty", "cautious"}
        if unsupported_modes:
            raise ValueError(f"Unsupported dbt indirect-selection modes: {', '.join(sorted(unsupported_modes))}.")
        for indirect_selection in ("empty", "cautious"):
            if indirect_selection not in selects_by_indirect_selection:
                continue
            selects = sorted(selects_by_indirect_selection[indirect_selection])
            commands.append(self._build_dbt_command("test", select=selects, indirect_selection=indirect_selection))

        return DbtTask(task_key, commands, self.task_options, depends_on)
