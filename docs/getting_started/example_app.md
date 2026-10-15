# Example app

`examples/bootstrap5/` in the repository is a local Django project with one page per use case. It runs
against the code in `src/`, so it doubles as a playground while developing.

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

Each feature has a card on the home page and a short explanation on every page, naming the code to look at.

### Datetimepicker: forms, modals & filters

Date, time and datetime pickers on create/update forms, in a crud_views modal ("Quick edit"), and as
list filters.

### Datetimepicker: per-field config

Per-field picker options: one year only, 15-minute steps, no past dates, weekdays only, inline, fixed
times — plus settings `DEFAULTS` making every week start on Monday.

### Typeahead: thousands of users

3,000 seeded users, about 500 per team. The task form's assignee is a text typeahead scoped to the team;
"Quick assign" shows it in a modal; "Pick assignee" shows the select popup, which browses the team on open
and loads more on scroll; the task list filter uses the popup over any team member.
