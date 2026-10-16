# Releasing

Releases are cut from `main` with green CI. A `v*` tag triggers the `Publish` workflow, which publishes to PyPI.

## Steps

```bash
git checkout main && git pull
uv run bump-my-version bump minor --no-commit --no-tag   # or patch / major
uv lock                                                  # pick up the new version in uv.lock
uv run pytest
git commit -am "Bump version: 0.3.0 → 0.4.0"             # pyproject.toml and uv.lock in one commit
git tag -a v0.4.0 -m "Bump version: 0.3.0 → 0.4.0"
git push origin main v0.4.0
```

`--no-commit --no-tag` overrides the `commit`/`tag` defaults in `[tool.bumpversion]`, so that `uv.lock` can be
updated first and land in the same commit.

## What the tag triggers

`.github/workflows/publish.yml` runs on `v*` tags:

1. `tests` — the test suite on Python 3.12, 3.13, 3.14 and 3.15,
2. `docs` — `mkdocs build --strict`,
3. `lint` — `ruff format --check` and `ruff check`,
4. `publish` — only when all three pass: `uv build`, then upload to PyPI via trusted publishing (OIDC, no API
   token), including provenance attestations.

The same tag also deploys the [live demo](demo.md) (`.github/workflows/demo.yml`).

## Claude Code skill

The [`django-crud-views-extensions` plugin](https://github.com/jacob-consulting/skills/tree/main/plugins/django-crud-views-extensions)
in the `jacob-consulting/skills` marketplace documents this package for Claude Code. When a release changes the
public API, settings, system checks or recommended usage, update its `SKILL.md` and `references/` (mark new
features `*Available since X.Y.Z*`), note it under `## [Unreleased]` in the plugin's `CHANGELOG.md`, and release the
plugin from that repo:

```bash
scripts/release.sh django-crud-views-extensions <version> --dry-run
scripts/release.sh django-crud-views-extensions <version>
git push origin main --follow-tags
```

The plugin is versioned independently of this package. Bug-fix releases with no user-visible API change need no
plugin release.

## Documentation

Read the Docs builds `latest` from `main`. Tagged versions can be activated in the Read the Docs project
settings if you want versioned documentation.
