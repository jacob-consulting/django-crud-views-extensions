# Development

## Requirements

- [uv](https://docs.astral.sh/uv/)
- optionally [Task](https://taskfile.dev), for the example app

## Setup

```bash
git clone git@github.com:jacob-consulting/django-crud-views-extensions.git
cd django-crud-views-extensions
uv sync --extra dev
```

django-crud-views is installed from PyPI as pinned in `uv.lock`. To test against an unreleased checkout of
django-crud-views next to this repository, install it editable for the time being:

```bash
uv pip install -e ../django-crud-views
```

## Tests and lint

```bash
uv run pytest                          # full suite
uv run pytest tests/test_widgets.py    # one file
uv run pytest -k pipeline              # by keyword
uv run ruff check . && uv run ruff format .   # lint + format (line length 120, double quotes)
```

The tests need no `DJANGO_SETTINGS_MODULE`: `tests/conftest.py` calls `settings.configure()` directly (with
`LANGUAGE_CODE="de-de"` and `PIPELINE={}`).

The [example app](../getting_started/example_app.md) has its own tests, which the root run does not collect
(`testpaths = ["tests"]`); CI runs them as a separate step:

```bash
cd examples/bootstrap5 && uv run pytest
```

## Documentation

The documentation is built with [MkDocs](https://www.mkdocs.org/) and hosted on Read the Docs. Preview it
locally on <http://localhost:8001>:

```bash
uv run --no-project --with-requirements docs/requirements.txt mkdocs serve -a localhost:8001
```

CI builds it with `mkdocs build --strict`, which fails on broken links and missing navigation entries:

```bash
uv run --no-project --with-requirements docs/requirements.txt mkdocs build --strict
```

The navigation order is set by the `.pages` files in each directory
([awesome-pages](https://github.com/lukasgeiter/mkdocs-awesome-pages-plugin)). Build dependencies are
hash-locked in `docs/requirements.txt`; to change them, edit `docs/requirements.in` and run:

```bash
uv pip compile --universal --generate-hashes --python-version 3.12 docs/requirements.in -o docs/requirements.txt
```

`docs/superpowers/` holds design specs and implementation plans; it is excluded from the site.
