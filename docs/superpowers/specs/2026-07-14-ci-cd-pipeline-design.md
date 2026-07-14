# CI/CD Pipeline Design

Date: 2026-07-14

## Purpose

Add GitHub Actions CI (tests + lint) and a tag-triggered PyPI publish pipeline to
`django-crud-views-extensions`, modeled on the sibling `django-crud-views` repo's
pipeline, adapted for the differences between the two repos (no `nox`, no `docs/`,
uv-native tooling, a local-path dev dependency override that must not leak into CI).

## Context gathered

- Sibling repo (`../django-crud-views`) has four workflows: `tests.yml`, `lint.yml`,
  `docs.yml`, `publish.yml`. It uses `nox` to run a Python × Django version matrix,
  `mkdocs` for docs, `bump-my-version` for releases, and PyPI trusted publishing
  (OIDC via a `pypi` GitHub environment, `pypa/gh-action-pypi-publish@release/v1`,
  no stored token).
- This repo has none of that: tests run directly via `pytest` (28 tests, ~0.05s, no
  coverage config), no `docs/` directory, no `nox`, no `__version__` string or
  README "Current version:" line to keep in sync.
- **Critical finding**: `pyproject.toml` has
  ```toml
  [tool.uv.sources]
  django-crud-views = { path = "../django-crud-views", editable = true }
  ```
  which only exists for local dev convenience (per this repo's `CLAUDE.md`: "During
  local dev, `[tool.uv.sources]` points at a sibling editable checkout... released
  builds use the PyPI pin"). A GitHub Actions runner won't have that sibling repo
  checked out, so a plain `uv run pytest` would fail. Verified locally that
  `uv run --no-sources --extra dev pytest` correctly ignores the local-path override
  and resolves `django-crud-views` from PyPI (0.11.0) instead — this is the command
  CI must use. `uv build` for packaging is unaffected either way, since build
  metadata comes from `[project.dependencies]`, not `[tool.uv.sources]`.
- GitHub remote already exists: `jacob-consulting/django-crud-views-extensions`.

## Decisions

| Question | Decision | Why |
|---|---|---|
| PyPI auth | Trusted publishing (OIDC), `pypi` environment, `id-token: write` | Matches sibling repo; no secret to manage/rotate |
| Test matrix | Python 3.12, 3.13, 3.14 | Matches `requires-python >=3.12`; matches sibling's Python range (no Django matrix needed — this repo doesn't depend on Django directly, only via `django-crud-views`) |
| Codecov | Add it, report-only (no `fail_under` gate) | Useful signal; a hard gate is premature for a young incubator repo with fluctuating coverage |
| Version bumping | Add `bump-my-version`, config only touches `pyproject.toml` | Matches sibling tooling; no other version strings exist here to sync |
| Build tool | `uv build` (not sibling's `pip install build && python -m build`) | Repo is already uv-native with no `nox`/pip-based tooling elsewhere; same job structure and triggers as sibling, different literal command |
| Python setup in CI | `astral-sh/setup-uv@v8` (installs uv + the matrix Python in one step) | Avoids a redundant `actions/setup-python` step; idiomatic for uv-based repos |

## Workflows

### `.github/workflows/tests.yml`
- Triggers: `push` to `main`, `pull_request` to `main`.
- Matrix: `python-version: ["3.12", "3.13", "3.14"]`.
- Steps: checkout → `astral-sh/setup-uv@v8` (with `python-version: ${{ matrix.python-version }}`, `enable-cache: true`) → `uv run --no-sources --extra dev pytest --cov=crud_views_widget_datetimepicker --cov-report=xml` → upload to Codecov (`codecov/codecov-action@v5`) only when `matrix.python-version == '3.13'`, using `secrets.CODECOV_TOKEN`.

### `.github/workflows/lint.yml`
- Triggers: same as tests.
- Single Python 3.13. Steps: checkout → `astral-sh/setup-uv@v8` → `uv run --no-sources ruff format --check .` → `uv run --no-sources ruff check .`.

### `.github/workflows/publish.yml`
- Trigger: `push` tags matching `v*`.
- Jobs:
  - `tests` — same matrix/steps as `tests.yml`.
  - `lint` — same steps as `lint.yml`.
  - `publish` — `needs: [tests, lint]`, `environment: pypi`, `permissions: id-token: write`. Steps: checkout → `astral-sh/setup-uv@v8` → `uv build` → `pypa/gh-action-pypi-publish@release/v1`.

## `pyproject.toml` changes

- Add `pytest-cov` to the `dev` optional-dependencies group.
- Add:
  ```toml
  [tool.coverage.run]
  source = ["crud_views_widget_datetimepicker"]
  ```
  (no `[tool.coverage.report] fail_under` — report-only per decision above).
- Add `bump-my-version` to `dev`, plus:
  ```toml
  [tool.bumpversion]
  current_version = "0.1.0"
  commit = true
  tag = true
  tag_name = "v{new_version}"

  [[tool.bumpversion.files]]
  filename = "pyproject.toml"
  search = 'version = "{current_version}"'
  replace = 'version = "{new_version}"'
  ```

## Manual steps required outside this repo (not automatable by this change)

- **PyPI trusted publisher**: register a trusted publisher for the
  `django-crud-views-extensions` project pointing at repo
  `jacob-consulting/django-crud-views-extensions`, workflow `publish.yml`,
  environment `pypi`. PyPI's project-scoped trusted publisher UI requires the
  project to already exist, so the very first release will need either a one-time
  manual `twine upload` of v0.1.0, or PyPI's "pending publisher" flow (pre-register
  a trusted publisher for a project name that doesn't exist yet, which PyPI creates
  on first successful publish via that workflow). Recommend the pending-publisher
  route so no token ever needs to exist.
- **GitHub `pypi` environment**: auto-created on first workflow run referencing it;
  optionally add protection rules (e.g. required reviewers) afterward.
- **`CODECOV_TOKEN` repo secret**: add via the Codecov app/dashboard for this repo.

## Testing / verification plan

- Push a branch with the new workflows and open a PR to trigger `tests.yml` and
  `lint.yml`, confirm all matrix legs pass and Codecov receives a report.
- Verify locally (already done) that `uv run --no-sources --extra dev pytest`
  passes all 28 tests before relying on it in CI.
- Verify `uv build` produces a valid sdist + wheel locally (`uv build` then inspect
  `dist/`) before the first real tag push.
- The actual tag-triggered publish to PyPI can only be verified end-to-end once the
  trusted publisher is registered — flag this as a follow-up manual test the user
  runs after merging.

## Out of scope

- No `docs.yml` / `mkdocs` workflow — this repo has no `docs/` source to build.
- No Django version matrix in tests — this repo doesn't depend on Django directly.
- No coverage `fail_under` gate for now.
