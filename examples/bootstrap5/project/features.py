"""Registry of example feature cards. Each feature task appends exactly one entry to FEATURES."""

from dataclasses import dataclass

from django.utils.translation import pgettext_lazy

#: GitHub page linked from the footer and the home page
REPO_URL = "https://github.com/jacob-consulting/django-crud-views-extensions"

#: public demo on Render (render.yaml), linked from the footer
DEMO_URL = "https://django-crud-views-extensions-demo.onrender.com/"

#: Read the Docs version linked from the example pages and the footer. "stable" is the newest release tag,
#: which is what the demo runs.
DOCS_BASE = "https://django-crud-views-extensions.readthedocs.io/en/stable"

#: the core package the extensions build on, linked from the home page and the footer
CRUD_VIEWS_DOCS_URL = "https://django-crud-views.readthedocs.io/en/stable/"
CRUD_VIEWS_REPO_URL = "https://github.com/jacob-consulting/django-crud-views"
CRUD_VIEWS_DEMO_URL = "https://django-crud-views-demo.onrender.com/"


@dataclass(frozen=True)
class DocRef:
    page: str  # path under docs/, e.g. "reference/typeahead/lookups.md"
    label: str  # English link text, deliberately not translated (like Feature.title / look_at)
    anchor: str = ""  # heading slug on that page, e.g. "config-merge-order"

    @property
    def url(self) -> str:
        """Read the Docs URL, following mkdocs' use_directory_urls: x/y.md -> x/y/, x/index.md -> x/."""
        path = self.page.removesuffix(".md")
        if path == "index" or path.endswith("/index"):
            path = path.removesuffix("index")
        else:
            path += "/"
        url = f"{DOCS_BASE}/{path}"
        return f"{url}#{self.anchor}" if self.anchor else url


@dataclass(frozen=True)
class FeatureGroup:
    key: str  # referenced by Feature.group
    title: str  # navbar dropdown and home page heading
    icon: str  # font-awesome classes


#: navbar dropdowns and home page sections, in display order
GROUPS: list[FeatureGroup] = [
    FeatureGroup(key="widgets", title=pgettext_lazy("feature group", "Widgets"), icon="fa-solid fa-puzzle-piece"),
]


@dataclass(frozen=True)
class Feature:
    app: str  # python package of the example app, e.g. "datetimepicker"; seed.py lives there
    viewset: str  # crud_views ViewSet name whose pages belong to this card, e.g. "event"
    group: str  # FeatureGroup.key
    title: str  # card / nav title (English, names a package feature)
    description: str  # one-liner on the home page card
    about: str  # 2-4 sentence teaching paragraph shown on every page of the card
    look_at: str  # one-sentence code pointer shown under the about paragraph
    url_name: str  # landing page URL name, e.g. "event-list"
    icon: str  # font-awesome classes
    docs: tuple[DocRef, ...] = ()  # documentation sections listed under "References to documentation"


FEATURES: list[Feature] = [
    # example feature apps append their entries here
    Feature(
        app="datetimepicker",
        viewset="event",
        group="widgets",
        title="Datetimepicker: forms, modals & filters",
        description="Date, time and datetime pickers on create/update forms, in a modal, and as list filters.",
        about=(
            "The everyday use of crud_views_widget_datetimepicker. The event form uses DatePickerInput, "
            "TimePickerInput and DateTimePickerInput; nothing else is configured — the plugin and init.js reach "
            "every page through {% cv_js %} / {% cv_css %}. Open “Quick edit” on a row to see the same form in a "
            "crud_views modal, and use the day range above the table to filter with the same widgets."
        ),
        look_at=(
            "EventForm.Meta.widgets and EventFilter in forms.py; EventQuickEditView (cv_modal = True) in views.py; "
            "CRUD_VIEWS_DATETIMEPICKER in project/settings.py."
        ),
        url_name="event-list",
        icon="fa-regular fa-calendar",
        docs=(
            DocRef(page="getting_started/datetimepicker.md", label="Your first datetimepicker"),
            DocRef(page="reference/datetimepicker/widgets.md", label="Datetimepicker widgets"),
            DocRef(
                page="reference/datetimepicker/widgets.md",
                label="Datetimepicker widgets — how it works (modals, init.js)",
                anchor="how-it-works",
            ),
            DocRef(page="reference/datetimepicker/settings.md", label="Datetimepicker settings"),
        ),
    ),
    Feature(
        app="datetimepicker",
        viewset="variant",
        group="widgets",
        title="Datetimepicker: per-field config",
        description="Per-field picker options: one year only, 15-minute steps, no past dates, inline, fixed times.",
        about=(
            "Each field passes its own xdsoft options through the widget's config argument. Options merge from "
            "lowest to highest: the widget class defaults, LANG, CRUD_VIEWS_DATETIMEPICKER['DEFAULTS'] (here "
            "dayOfWeekStart=1, so every week starts on Monday), then the per-field config. fix_year is a shortcut "
            "that sets minDate, maxDate, yearStart and yearEnd."
        ),
        look_at="PickerVariantForm.Meta.widgets in forms.py; CRUD_VIEWS_DATETIMEPICKER in project/settings.py.",
        url_name="variant-list",
        icon="fa-solid fa-sliders",
        docs=(
            DocRef(
                page="reference/datetimepicker/widgets.md",
                label="Datetimepicker widgets — options (config, fix_year, format)",
                anchor="options",
            ),
            DocRef(
                page="reference/datetimepicker/widgets.md",
                label="Datetimepicker widgets — config merge order",
                anchor="config-merge-order",
            ),
            DocRef(
                page="getting_started/datetimepicker.md",
                label="Your first datetimepicker — per-field options",
                anchor="per-field-options",
            ),
            DocRef(page="reference/datetimepicker/settings.md", label="Datetimepicker settings (DEFAULTS)"),
        ),
    ),
    Feature(
        app="typeahead",
        viewset="team",
        group="widgets",
        title="Typeahead: thousands of users",
        description="Server-backed type-ahead and select popup, scoped per team, in forms, modals and a list filter.",
        about=(
            "Each team has about 500 of 3,000 seeded users: too many for a <select>. The task form's assignee is a "
            "TypeaheadField bound to the 'typeahead.team_members' lookup with the team from the URL, so the "
            "suggestions and the save-time validation are the same set. “Quick assign” shows the text typeahead "
            "in a crud_views modal; “Pick assignee” shows the TypeaheadSelect popup, which browses the team on "
            "open and loads more on scroll. The task list filter uses the popup over any team member."
        ),
        look_at=(
            "typeahead.py (the lookups); TaskForm, TaskPickForm and TaskFilter (bind in __init__) in forms.py; the "
            "'_typeahead/' include in project/urls.py."
        ),
        url_name="team-list",
        icon="fa-solid fa-magnifying-glass",
        docs=(
            DocRef(page="getting_started/typeahead.md", label="Your first typeahead"),
            DocRef(page="reference/typeahead/lookups.md", label="Typeahead lookups"),
            DocRef(
                page="reference/typeahead/fields_filters.md", label="Typeahead fields & filters — bind()", anchor="bind"
            ),
            DocRef(page="reference/typeahead/fields_filters.md", label="Typeahead filters", anchor="filters"),
            DocRef(
                page="reference/typeahead/widgets.md", label="Typeahead widgets — select popup", anchor="select-popup"
            ),
            DocRef(
                page="reference/typeahead/widgets.md",
                label="Typeahead widgets — modals and dynamic content",
                anchor="modals-and-dynamic-content",
            ),
            DocRef(page="reference/typeahead/security.md", label="Typeahead security"),
        ),
    ),
]


def feature_groups() -> list[tuple[FeatureGroup, list[Feature]]]:
    """FEATURES bucketed by GROUPS, in GROUPS order. Raises ValueError for an unknown group key."""
    buckets: dict[str, list[Feature]] = {group.key: [] for group in GROUPS}
    for feature in FEATURES:
        if feature.group not in buckets:
            raise ValueError(f"Feature {feature.title!r} names unknown group {feature.group!r}")
        buckets[feature.group].append(feature)
    return [(group, buckets[group.key]) for group in GROUPS]


# validate group keys at import time (the URLconf imports this via project.views)
feature_groups()
