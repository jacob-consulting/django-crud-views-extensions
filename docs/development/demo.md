# Deploying the demo

The [live demo](../getting_started/example_app.md#live-demo) runs `examples/bootstrap5` on Render's free plan, as
described by `render.yaml` at the repo root, with `project.settings_demo` (no Django admin, reset banner, per-IP
write rate limit). The workflow `.github/workflows/demo.yml` drives it:

- **pushing a `v*` tag** deploys exactly that commit
- **Run workflow** (manual) deploys the selected ref, which may be unreleased code; tick *reset_only* to just
  wipe the data
- **daily at 03:00 UTC** it restarts the service, which gives it a fresh database

Each run ends with a smoke test: `/login/` must return 200 and `/admin/` 404.

Render installs the package with `pip install .` plus `requirements/demo.txt` (gunicorn, whitenoise,
django-ratelimit), so the demo resolves django-crud-views from PyPI, not from `uv.lock`.

## One-time setup

1. In Render: **New → Blueprint**, select this repository. This creates the `django-crud-views-extensions-demo`
   service. Turn off the Blueprint's auto-sync, so changes to `render.yaml` on the connected branch don't trigger
   deploys of unreleased code.
2. Create an API key (Account settings → API keys).
3. In GitHub (Settings → Secrets and variables → Actions) add the secrets `RENDER_API_KEY` and
   `RENDER_SERVICE_ID` (the `srv-…` id from the service URL) and the variable `DEMO_URL`
   (`https://django-crud-views-extensions-demo.onrender.com`, no trailing slash).
4. Run the `demo` workflow manually once.

## Rehearse locally

```bash
cd examples/bootstrap5
export DJANGO_SETTINGS_MODULE=project.settings_demo SECRET_KEY=x RENDER_EXTERNAL_HOSTNAME=localhost
python manage.py collectstatic --noinput
python manage.py migrate --noinput && python manage.py seed
gunicorn project.wsgi --workers 1 --bind 127.0.0.1:8000
```

Run it in a virtualenv that has `requirements/demo.txt` installed, and against a throwaway database:
`seed` writes into `db.sqlite3`. Delete `staticfiles/` afterwards.
