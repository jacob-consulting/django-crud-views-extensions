"""Registry of example feature cards. Each feature task appends exactly one entry to FEATURES."""

from dataclasses import dataclass

from django.utils.translation import pgettext_lazy

#: GitHub page linked from the footer and the home page
REPO_URL = "https://github.com/jacob-consulting/django-crud-views-extensions"


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


FEATURES: list[Feature] = [
    # example feature apps append their entries here
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
