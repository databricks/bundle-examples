import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from fnmatch import fnmatchcase
from graphlib import CycleError, TopologicalSorter

from databricks_dbt_factory.dbt_task import DbtTask
from databricks_dbt_factory.utils import MAX_JOB_TASKS, MAX_TASK_KEY_LENGTH

DEFAULT_JOB = "default"


@dataclass(frozen=True)
class JobPartition:
    """One job of a split project: its tasks, and the jobs that must succeed before it runs."""

    name: str
    tasks: list[dict]
    depends_on: list[str]


@dataclass(frozen=True)
class TaskPlacement:
    """The resource a task runs, its tags, and whether the task follows its dependencies instead of its tags."""

    resource: str
    tags: frozenset[str]
    follows_dependencies: bool


def partition_tasks(
    tasks: list[DbtTask], placements: dict[str, TaskPlacement], patterns: Sequence[str]
) -> list[JobPartition]:
    """
    Splits tasks into one job per tag matching `patterns`, ordered so each job runs after those it depends on.

    A task joins the job of the one matching tag it carries, or the default job. A task that follows its
    dependencies joins the last of their jobs, so tests run after every resource they test.

    Raises:
        ValueError: when a resource carries several matching tags, a pattern matches no tag, two tags name the
            same job, jobs would depend on each other, or a job exceeds Databricks' task limit.
    """
    dependencies = {task.task_key: list(task.depends_on or []) for task in tasks}
    tags = {
        task.task_key: _split_tag(placements[task.task_key], patterns)
        for task in tasks
        if not (placements[task.task_key].follows_dependencies and dependencies[task.task_key])
    }
    owner = _job_names(tags, patterns)
    anchors = _anchors(dependencies, owner)
    order = _job_order(owner, dependencies, anchors)
    rank = {job: index for index, job in enumerate(order)}
    for key in dependencies.keys() - owner.keys():
        owner[key] = max((owner[anchor] for anchor in anchors[key]), key=rank.__getitem__)

    jobs: dict[str, list[DbtTask]] = {job: [] for job in order}
    upstream: dict[str, set[str]] = {job: set() for job in order}
    for task in tasks:
        job = owner[task.task_key]
        jobs[job].append(replace(task, depends_on=[d for d in dependencies[task.task_key] if owner[d] == job]))
        upstream[job].update(owner[d] for d in dependencies[task.task_key] if owner[d] != job)
    for job, job_tasks in jobs.items():
        if len(job_tasks) > MAX_JOB_TASKS:
            raise ValueError(
                f"Databricks jobs support at most {MAX_JOB_TASKS:,} tasks; the {job!r} job generates "
                f"{len(job_tasks):,}. Split it further by tag."
            )
    if len(order) > MAX_JOB_TASKS:
        raise ValueError(
            f"Databricks jobs support at most {MAX_JOB_TASKS:,} tasks; the tags split into {len(order):,} jobs. "
            f"Split by fewer tags."
        )
    return [JobPartition(job, [task.to_dict() for task in jobs[job]], sorted(upstream[job])) for job in order]


def _split_tag(placement: TaskPlacement, patterns: Sequence[str]) -> str | None:
    matched = sorted(tag for tag in placement.tags if any(fnmatchcase(tag, pattern) for pattern in patterns))
    if len(matched) > 1:
        raise ValueError(
            f"Cannot split by tag: {placement.resource} carries the split tags {', '.join(matched)}. "
            f"Keep one, so it belongs to one job."
        )
    return matched[0] if matched else None


def _job_names(tags: dict[str, str | None], patterns: Sequence[str]) -> dict[str, str]:
    used = set(tags.values())
    for pattern in patterns:
        if not any(tag is not None and fnmatchcase(tag, pattern) for tag in used):
            raise ValueError(
                f"--split-by-tag {pattern!r} matches no tag of a resource to split; tests run in the job of the "
                f"resources they test, whatever their own tags."
            )
    names = {tag: DEFAULT_JOB if tag is None else re.sub(r"[^A-Za-z0-9_]", "_", tag) for tag in used}
    owners: dict[str, str | None] = {}
    for tag in sorted(used, key=str):
        if len(names[tag]) > MAX_TASK_KEY_LENGTH:
            raise ValueError(
                f"Cannot split by tag: tag {tag!r} is longer than the {MAX_TASK_KEY_LENGTH} characters Databricks "
                f"allows in a task key. Use a shorter tag."
            )
        if owners.setdefault(names[tag], tag) != tag:
            labels = [f"tag {t!r}" if t is not None else "untagged resources" for t in (owners[names[tag]], tag)]
            raise ValueError(f"Cannot split by tag: {' and '.join(labels)} would both run as job {names[tag]!r}.")
    return {key: names[tag] for key, tag in tags.items()}


def _anchors(dependencies: dict[str, list[str]], placed: dict[str, str]) -> dict[str, set[str]]:
    anchors: dict[str, set[str]] = {}
    for key in TopologicalSorter(dependencies).static_order():
        anchors[key] = {key} if key in placed else set().union(*(anchors[d] for d in dependencies[key]))
    return anchors


def _job_order(owner: dict[str, str], dependencies: dict[str, list[str]], anchors: dict[str, set[str]]) -> list[str]:
    upstream: dict[str, set[str]] = {job: set() for job in owner.values()}
    witness: dict[tuple[str, str], tuple[str, str]] = {}
    for key, job in owner.items():
        for source in (anchor for d in dependencies[key] for anchor in anchors[d]):
            if owner[source] != job:
                upstream[job].add(owner[source])
                witness.setdefault((owner[source], job), (key, source))
    try:
        return list(TopologicalSorter({job: sorted(upstream[job]) for job in sorted(upstream)}).static_order())
    except CycleError as error:
        cycle = error.args[1]
        needs = "; ".join(f"{key} needs {source}" for key, source in (witness[p] for p in zip(cycle, cycle[1:])))
        raise ValueError(
            f"Cannot split by tag: jobs {' -> '.join(cycle)} would depend on each other ({needs}). "
            f"Retag the resources so dependencies between jobs flow one way."
        ) from error
