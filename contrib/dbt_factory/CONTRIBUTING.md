# Contributing to dbt-factory

Thanks for contributing! This guide covers the **dbt-factory** template
([`contrib/templates/dbt-factory`](../templates/dbt-factory)) and this ready-to-run example
([`contrib/dbt_factory`](.)). Most development happens from this example directory — it has the
`Makefile`, the unit tests, and the end-to-end test.

## First principles

- Keep a generated project **self-contained and dependency-light** — it should run with just `uv`
  and the Databricks CLI, with no per-model YAML to maintain.
- The factory core under `src/databricks_dbt_factory/` is **vendored**, not developed here — see
  [Vendored factory](#vendored-factory).
- **Serverless is the default** compute and the **job cluster** path is opt-in; keep both working.

## Local setup

Requirements:

- Python (`>=3.10,<3.13`, per `pyproject.toml`)
- The [`uv`](https://docs.astral.sh/uv/) package manager
- The [Databricks CLI](https://docs.databricks.com/dev-tools/cli/databricks-cli.html)

Install the development environment:

```
$ make setup      # == uv sync --dev  (into .venv, from the frozen uv.lock)
```

Prefer the `make` targets over calling `uv`/`dbt`/`databricks` directly where one exists:
`make manifest`, `make validate`, `make deploy`, `make run`, `make test`, `make test-e2e`.

## Before you open a PR (Definition of Done)

Run these locally — they mirror the CI gates plus the manual checks:

1. **Format** — `uv run ruff format .` The `fmt` CI runs `ruff format --check`, so unformatted code
   fails the build.
2. **Unit tests** — `make test` (offline; no workspace needed). This is the fast gate.
3. **End-to-end** — `make test-e2e` deploys, runs, verifies, and tears down a real job for **both**
   compute modes (serverless and job cluster). It is **not** a CI gate, so run it locally before
   merging any change to the factory or template. It needs `DATABRICKS_*` / `DBT_FACTORY_*`
   environment variables — see [`tests/e2e/README.md`](tests/e2e/README.md).
4. **Snapshot** — if you intentionally changed the generated task output, refresh the saved snapshot
   with `make test-update-expected-tasks` and commit the result.
5. **Docs** — update the relevant README(s) for any user-facing change.

## Testing

- **`make test`** — runs the vendored factory's unit tests plus an offline test of the PyDABs
  integration against the committed manifest; no workspace is required. One test compares the
  generated tasks with `tests/test_data/expected_tasks.json`, so unintended changes to the generated
  job fail the suite.
- **`make test-e2e`** — the real end-to-end check (generate → deploy → run → verify → destroy) for
  both compute modes. See [`tests/e2e/README.md`](tests/e2e/README.md) for the required environment
  and details.

### Scaffolding check

The unit tests run against the committed (pre-rendered) example, so they do **not** exercise the
template's prompts or rendering. When you change the template, scaffold a throwaway project with
`databricks bundle init` to confirm it still scaffolds correctly — do it once per compute mode
(`use_serverless = yes` and `= no`):

```
# from a neutral directory (not inside a bundle), pointing at the template:
$ databricks bundle init <repo-root>/contrib/templates/dbt-factory --output-dir /tmp/dbt-factory-check
$ cd /tmp/dbt-factory-check/<project_name>
$ make setup && make manifest && make test
```

This needs a configured Databricks CLI profile — the template resolves workspace values (such as
`smallest_node_type` and `workspace_host`) at init time. `make test-e2e` already runs `bundle init`
for both modes end-to-end, but this quick check catches rendering/prompt errors without a full
deploy.

## Keeping the template and example in sync

The template ([`contrib/templates/dbt-factory`](../templates/dbt-factory)) and this example are two
copies of the same project (the template's files are `*.tmpl`; this example is a rendered, serverless
copy). When you change a shared file — the factory core, `resources/__init__.py`, the tests, the
`Makefile`, `dbt_profiles/profiles.yml` — update **both** so the template's serverless rendering
still matches this example.

### Vendored factory

`src/databricks_dbt_factory/` is vendored from
[databricks-dbt-factory](https://github.com/mwojtyczka/databricks-dbt-factory) and pinned to the
commit recorded in [`NOTICE`](NOTICE). The `dbt-factory vendor-sync` CI check enforces that:

- each vendored file is byte-identical to that upstream commit, and
- the example and template copies are byte-identical to each other.

So **don't edit the factory here** — make the change upstream (see the factory's
[contributing guide](https://github.com/mwojtyczka/databricks-dbt-factory/blob/main/CONTRIBUTING.md),
which uses its own Hatch-based `make dev`/`fmt`/`lint`/`test`/`integration` workflow), then re-vendor
into both copies and update the commit/version in both `NOTICE` files.

## Opening the PR

Unless you have write access to
[`databricks/bundle-examples`](https://github.com/databricks/bundle-examples), work from a **fork**:

1. Fork the repo and clone your fork (keep its `main` in sync with upstream). If you have write
   access, you can branch directly in the upstream repo instead.
2. Create a feature branch from `main`, make your change, and run the Definition-of-Done checks
   above.
3. Push the branch (to your fork, or upstream if you have access) and open a PR against
   `databricks/bundle-examples` `main`, with a clear description and `Resolves #NNN` if it fixes an
   issue.
