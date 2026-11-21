# crud_views_allauth: allauth pages in the crud-views theme

Date: 2026-11-21. Status: **postponed by the maintainer, not approved.** No implementation authorized.

## Open problems found in review (read before reviving)

The design below is the first draft and is wrong in two places. Both were confirmed against the code.

1. **Manage pages cannot extend `CRUD_VIEWS_EXTENDS`.** That template is the crud-views shell. It calls
   `{% cv_header %}`, `{% cv_context_actions object %}` and `{% cv_paragraph %}`, which assert that `view` is a
   `CrudView`. On an allauth page they raise, so the manage pages would return 500.
2. **The layouts cannot wrap allauth's content.** allauth pages fill `{% block content %}`, and most project base
   templates also have a `content` block. Django then puts the page straight into the base's block, and whatever
   the layout placed around it (card, account navigation, re-exposed `extra_body`) disappears without an error.

A revised contract was proposed and **not decided**: two settings keys, `ENTRANCE_EXTENDS` and `MANAGE_EXTENDS`,
each naming a project template that only needs `{% block content %}`; one-line layouts that wrap nothing; the
centered card owned by the project's entrance template; messages left to the project's templates; the account
navigation shipped as an include the project places itself; an error check for a missing `content` block and a
warning for a missing `extra_body` block (allauth's passkey-login script lives there). The element overrides,
crispy fields, class-key buttons and the context processor are unaffected.

Also from review: no allauth 65.15 page extends `allauth/layouts/base.html` directly, so that override is only an
alias; `extra_body` is used by `account/login.html` and `account/email.html` only.

## Intent

Projects that use django-crud-views and django-allauth get allauth's pages (sign in, sign up, password, email,
MFA, social connections, sessions) as unstyled HTML today, next to themed crud-views pages. This app makes
allauth's pages render in the project's crud-views theme, with form fields rendered by django-crispy-forms in the
project's template pack. A project installs the app, names one template, and is done.

It is a template-only integration. django-crud-views has no login, signup or account views, and this app adds
none.

## Goals

- Every allauth page that is built from allauth's elements and layouts renders with theme markup, without the
  project writing allauth templates.
- Form fields render through crispy (`{{ form|crispy }}`), so they match the fields on crud-views pages.
- Buttons take their classes from core's class keys, so a downstream theme package (CoreUI, Tabler and the like)
  restyles allauth pages with no allauth templates of its own.
- Pages for logged-in users sit inside the project's normal shell. Pages for anonymous users sit in a bare page
  the project names.
- A wrong installation fails at startup with a system check, not with a silently unstyled page.

## Non-goals

- No views, forms, URLs, models, adapters or settings for allauth's behaviour. The project configures allauth
  itself.
- No ViewSets over allauth's models (email addresses, social accounts, sessions).
- No overrides of allauth's page templates (`account/*.html`, `mfa/*.html`, …). Only elements and layouts.
- No email (mail body) templates, no allauth headless, no identity-provider (`idp`) pages.
- No translations of allauth's strings.
- No JavaScript and no CSS shipped by this app. No asset registry entry.
- No move into django-crud-views core. That is a later, separate decision once the app has proven itself.

## Anti-goals

- Copying allauth's page templates. That would tie the app to every allauth release.
- A bare entrance page that loads CSS on its own (a hard-coded Bootstrap CDN link, for example). The app cannot
  know where a project's CSS lives.
- New class keys, flags or settings beyond the one this design names.

## Constraints

- **Maintainability.** The maintainer must be able to read, explain and debug all of it. The app is about 25 small
  templates, one context processor, one settings reader and one checks module.
- **allauth's customization contract.** allauth builds its page templates from 22 element templates
  (`allauth/elements/*.html`) and 3 layouts (`allauth/layouts/base.html`, `entrance.html`, `manage.html`).
  Overriding these is allauth's documented way to restyle it. Verified against allauth 65.15.0: `fields.html` is
  `{{ attrs.form.as_p }}`; 23 page templates use the `fields` element and 7 use the single `field` element.
- **Template order.** Django's app-directories loader takes the first match, so `crud_views_allauth` must be
  listed before `allauth` in `INSTALLED_APPS`.
- **`{% extends %}` must be the first tag.** A layout cannot load a tag library to work out what to extend. The
  name of the parent template has to be in the template context already.
- **The project owns the page `<head>`.** Bootstrap, icons and `{% cv_css %}`/`{% cv_js %}` are loaded by the
  project's base template (`CRUD_VIEWS_EXTENDS`), and that template exposes `{% block cv_content %}`.
- **Incubator rules of this repo.** Import paths and settings keys are public contract. System-check ids live in
  the `crud_views.*` namespace. A new app adds an example app, docs pages and, at release, a skill update.
- **No downstream project names** in any file of this repo.

## Approaches

The element and layout overrides are the only sensible way to do the theming: allauth designed them for it, and
the alternative (overriding ~75 page templates) is an anti-goal. Likewise `{{ form|crispy }}` in `fields.html` is
the one place crispy plugs in; `{% crispy form %}` does not fit, because it emits its own `<form>` tag and allauth's
`form` element already owns that tag and the buttons.

The real choice was where the page around an entrance (anonymous) page comes from. The maintainer first chose a
bare layout over reusing the app shell, because a login page should not show a navbar and sidebar that assume a
logged-in user. Then, for how that bare page gets its `<head>`:

- **A. The project names its bare template (chosen).** A setting points at a project template with the `<head>`
  and a `cv_content` block. A system check fails if it is unset or missing. Costs one extra file per project. It
  is the same contract as `CRUD_VIEWS_EXTENDS` and works for any theme.
- **B. Same setting, optional, falling back to `CRUD_VIEWS_EXTENDS`.** Works on install, but the default is the
  navbar-on-login look that was ruled out, and it is two behaviours to document and test.
- **C. The app ships a complete bare page with Bootstrap from a CDN.** Zero configuration, but it hard-codes a
  Bootstrap version and a CDN. Wrong for non-Bootstrap-file themes and for projects that vendor assets, which
  would replace the file anyway.

The maintainer picked A: smallest thing to own, no guessing about assets.

## Design

### Package

- New app `src/crud_views_allauth/` in django-crud-views-extensions, added to the wheel's `packages`.
- Name `crud_views_allauth`, not `crud_views_widget_*`: it is not a widget, and core's own extension apps are
  named `crud_views_guardian`, `crud_views_workflow` and so on. *(Designer's call.)*
- allauth is an optional extra, `django-crud-views-extensions[allauth]`, so projects that only use the widgets do
  not install it. *(Designer's call.)*
- The package description in `pyproject.toml` and the README stop saying "widgets, fields" only.

### What the project does

```python
INSTALLED_APPS = [
    ...,
    "crud_views",
    "crud_views_allauth",   # before allauth
    "allauth",
    "allauth.account",
    ...,
]

TEMPLATES[0]["OPTIONS"]["context_processors"] += ["crud_views_allauth.context_processors.layouts"]

CRUD_VIEWS_ALLAUTH = {"ENTRANCE_EXTENDS": "project/entrance.html"}
```

and writes `project/entrance.html`: a full HTML page with its own `<head>` (the same CSS and JS its base template
loads), no navigation, and `{% block cv_content %}{% endblock %}` in the body. The docs and the example app carry
one to copy.

### Setting

One settings dict, following the `CRUD_VIEWS_TYPEAHEAD` / `CRUD_VIEWS_DATETIMEPICKER` convention of this repo
(the flat name `CRUD_VIEWS_ALLAUTH_ENTRANCE_EXTENDS` used in the discussion becomes a key). *(Designer's call.)*

- `CRUD_VIEWS_ALLAUTH["ENTRANCE_EXTENDS"]`: required. Template name of the project's bare page.

`conf.py` reads it into a frozen dataclass, like the other apps. It is the only module that touches
`django.conf.settings`.

### Context processor

`crud_views_allauth.context_processors.layouts` adds two template names to every context:

- `cv_allauth_entrance_extends`: the `ENTRANCE_EXTENDS` setting.
- `cv_allauth_manage_extends`: core's `CRUD_VIEWS_EXTENDS` (read through `crud_views.lib.settings`).

It exists because of the first-tag rule above: allauth's views do not put these names in the context, and a layout
cannot compute them. *(Designer's call; the alternative, a fixed template name the project must provide, cannot
serve the manage layout, whose parent is whatever `CRUD_VIEWS_EXTENDS` says.)*

### Layouts

`templates/allauth/layouts/`:

- `entrance.html`: `{% extends cv_allauth_entrance_extends %}`. Fills `cv_content` with a centered card that
  contains `{% cv_messages %}`, then allauth's `{% block content %}`, then `{% block extra_body %}`.
- `manage.html`: `{% extends cv_allauth_manage_extends %}`. Fills `cv_content` with the account navigation (below),
  `{% cv_messages %}`, allauth's `{% block content %}`, then `{% block extra_body %}`.
- `base.html`: the same as `manage.html` in effect, for the few allauth pages that extend the base layout
  directly. Builder decides whether it extends `manage.html`'s parent or shares an include.

`extra_body` is re-exposed inside `cv_content` because allauth puts its passkey/WebAuthn scripts there, and a
project base template has no block of that name. Without this, passkey pages would break silently. No allauth
65.15 page uses `extra_head`, so it is not re-exposed.

Page titles: allauth pages set `{% block head_title %}`. The layouts cannot place it, because the name of a
project's title block is not part of core's contract. A project that wants allauth's titles puts
`{% block head_title %}{% endblock %}` inside its `<title>` in the entrance template and, if it likes, in its base
template. The docs say so. This is a documented limitation, not something to solve with a setting.

The layout names must stay `allauth/layouts/entrance.html` and `manage.html`: allauth reads the layout name from
the extends chain to pick `element__layout.html` variants.

### Account navigation on manage pages

allauth's default base layout carries a menu (change email, change password, connections, two-factor, sessions,
sign out). The project's shell does not link to these pages, so the manage layout includes
`crud_views_allauth/includes/manage_nav.html`: the same links, each guarded with `{% url ... as %}` exactly as
allauth does so absent allauth apps drop out, rendered as a Bootstrap nav. A project overrides that one include to
change or remove it. Sign out is left out of it: the project's shell already has one. *(Designer's call: without
this menu the manage pages are unreachable from each other.)*

### Elements

`templates/allauth/elements/`, one file per allauth element, each kept as close to allauth's original as theme
markup allows and reading the same `attrs` and slots:

- `fields.html`: `{{ attrs.form|crispy }}`. allauth's `unlabeled=True` hint is ignored; crispy's labels are kept
  so fields look like the ones on crud-views pages. *(Designer's call.)*
- `form.html`: allauth's `<form>` with the body slot, then the actions slot wrapped in the `form:actions` class
  key.
- `field.html`: hand-written Bootstrap 5 form markup (`form-label`, `form-control`, `form-check`, …), the same
  class names crispy-bootstrap5 emits. Crispy cannot render it: this element receives loose attributes, not a
  Django form field.
- `button.html`: allauth's button or link, with classes from core's existing keys, chosen from `attrs.tags` in the
  template itself:
    - tags contain `danger` or `delete` → `{% cv_button_class "form" "delete" %}`
    - tags contain `cancel`, `secondary`, `link` or `outline` → `{% cv_button_class "form" "cancel" %}`
    - otherwise → `{% cv_button_class "form" "submit" %}`
- `button_group.html`, `alert.html`, `badge.html`, `h1.html`, `h2.html`, `hr.html`, `p.html`, `img.html`,
  `panel.html`, `details.html`, `table.html` and its row/cell elements, `provider.html`, `provider_list.html`:
  plain theme markup. Headings use core's `heading:size-*` keys. Where core already has a tag for the job
  (`cv_alert` for alerts), use it if the element's slot content fits; otherwise write the markup. Builder decides
  per element.

No new class keys are registered. If a downstream theme later needs to tell an allauth button from a form button,
that is a new request.

### System checks

Registered under `crud_views`, in `checks.py`. Ids E334, E335 and E336 are unused in both repos today; the builder
confirms that before using them.

- **E334**: `CRUD_VIEWS_ALLAUTH["ENTRANCE_EXTENDS"]` is not set, or the template cannot be loaded. Hint: create
  the bare page; link to the docs.
- **E335**: `crud_views_allauth` is listed after `allauth` in `INSTALLED_APPS`, or `allauth` is not installed.
  Hint: move it before `allauth`.
- **E336**: `crud_views_allauth.context_processors.layouts` is missing from the Django template engine's context
  processors.

### Versions

- allauth floor: the builder sets it to the oldest 65.x release whose element and layout set matches what the app
  overrides, tests against the newest, and records both in `pyproject.toml` and the docs. An element allauth adds
  later falls back to allauth's own unstyled template, which is acceptable and is how the app degrades.
- django-crud-views floor: raised from 0.29 only if a tag or class key this app uses needs it (`cv_alert`,
  `form:actions`, `heading:size-*`). The builder checks and bumps the dependency for the whole distribution if so.
- crispy: no new dependency; core already requires django-crispy-forms and crispy-bootstrap5.

### Tests

In `tests/`, with allauth's apps and middleware added to `settings.configure()` in `conftest.py` (or a guarded
block, builder's choice) and a test entrance template in `tests/testapp`:

- The three checks, each in its failing and passing state.
- Rendered through the Django test client: sign in, sign up, password reset (entrance); change password and email
  (manage). Assert the entrance page extends the project's bare template and has no manage navigation, the manage
  page sits in the `CRUD_VIEWS_EXTENDS` shell with the navigation, fields carry crispy's markup, and buttons carry
  the class-key classes.
- A changed `form:submit` class key shows up on the sign-in button (the downstream-theme promise).
- One MFA page and the social connections page render without error when those allauth apps are installed.
- Each of the 22 elements renders in isolation with representative `attrs`.

### Example app, docs, release

Following this repo's convention for a new app:

- `examples/bootstrap5/`: allauth installed, the example's login replaced by allauth's, an entrance template, and
  `Feature` entries with `DocRef`s. Builder decides how many pages the feature list needs.
- `docs/getting_started/allauth.md` (install, the three settings lines, the entrance template to copy, the title
  note) and `docs/reference/allauth/` (setting, checks, element-to-class-key table, how to override the manage
  navigation, what is not covered). `!!! example "Try it live"` boxes as on the other pages.
- README section, CHANGELOG entry, CLAUDE.md architecture section for the new app.
- The Claude Code skill in the sibling marketplace repo is updated at release, per
  `docs/development/releasing.md`.

## Left to the builder

- Exact markup of each element and of the entrance card (width, spacing), within Bootstrap 5 classes.
- Whether `base.html` shares code with `manage.html` through an include or an extends.
- Which elements use a core tag and which carry their own markup.
- The allauth and django-crud-views version floors, as described above.
- Test file layout and how allauth settings are added to the test configuration.
- Example app page structure.
