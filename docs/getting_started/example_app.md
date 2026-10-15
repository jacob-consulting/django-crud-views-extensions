# Example app

`examples/bootstrap5/` in the repository is a local Django project with one page per use case. It runs
against the code in `src/`, so it doubles as a playground while developing.

## Live demo

The example app runs as a public demo at
**[django-crud-views-extensions-demo.onrender.com](https://django-crud-views-extensions-demo.onrender.com/)**. Log in as `admin` / `admin`.

Things to know:

- **The data resets.** Every day at 03:00 UTC, and whenever the demo has been idle for about 15 minutes, it starts
  again from freshly seeded data. Feel free to change and delete things.
- **The first request after a pause can take about a minute** while the free instance wakes up.
- **Saving is rate-limited** to 30 changes per minute and 300 per day per visitor.
- **The Django admin is not available** on the demo.

The demo normally runs the latest release.

## Run it

```bash
cd examples/bootstrap5
task run        # migrate, seed, runserver on 127.0.0.1:8000 — log in as admin/admin
task seed       # migrate and (re)seed the demo data
task test       # the example's own tests
```

Without [Task](https://taskfile.dev):

```bash
uv run manage.py migrate && uv run manage.py seed && uv run manage.py runserver
```

!!! warning
    The example runs with `DEBUG` on and a published `admin`/`admin` login. Keep it on your machine.

## What it shows

Each feature has a card on the home page. Every page of a feature explains what it shows and names the code to
look at; below the page, **The code behind this page** shows the app's source files and **References to
documentation** links the sections of these docs that explain it.

### Datetimepicker: forms, modals & filters

[Open in the live demo](https://django-crud-views-extensions-demo.onrender.com/datetimepicker/event/) · `examples/bootstrap5/datetimepicker/`

Date, time and datetime pickers on create/update forms, in a crud_views modal ("Quick edit"), and as
list filters.

### Datetimepicker: per-field config

[Open in the live demo](https://django-crud-views-extensions-demo.onrender.com/datetimepicker/variant/) · `examples/bootstrap5/datetimepicker/`

Per-field picker options: one year only, 15-minute steps, no past dates, weekdays only, inline, fixed
times — plus settings `DEFAULTS` making every week start on Monday.

### Typeahead: thousands of users

[Open in the live demo](https://django-crud-views-extensions-demo.onrender.com/typeahead/team/) · `examples/bootstrap5/typeahead/`

3,000 seeded users, about 500 per team. The task form's assignee is a text typeahead scoped to the team;
"Quick assign" shows it in a modal; "Pick assignee" shows the select popup, which browses the team on open
and loads more on scroll; the task list filter uses the popup over any team member.
