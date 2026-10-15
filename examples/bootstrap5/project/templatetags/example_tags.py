from pathlib import Path

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

register = template.Library()


def feature_for(view):
    """The Feature card a view belongs to (matched by its ViewSet name, then its parents'), or None."""
    from project.features import FEATURES

    viewset = getattr(view, "cv_viewset", None)
    while viewset is not None:
        feature = next((f for f in FEATURES if f.viewset == viewset.name), None)
        if feature:
            return feature
        viewset = viewset.parent.viewset if viewset.parent else None
    return None


@register.simple_tag(takes_context=True)
def get_feature_groups(context):
    """Navbar data: the feature groups plus the current page's card (or None)."""
    from project.features import feature_groups

    feature = feature_for(context.get("view"))
    return {
        "groups": feature_groups(),
        "active_group": feature.group if feature else None,
        "active_title": feature.title if feature else None,
    }


@register.inclusion_tag("project/example_about.html", takes_context=True)
def example_about(context):
    return {"feature": feature_for(context.get("view"))}


#: files of the feature's app rendered under "The code behind this page", in this order (missing ones are skipped)
SNIPPET_FILES = ["models.py", "typeahead.py", "forms.py", "views.py"]


@register.inclusion_tag("project/snippet_panels.html", takes_context=True)
def snippet_panels(context):
    """Highlighted source of the current page's example app, plus the feature's documentation references."""
    feature = feature_for(context.get("view"))
    if feature is None:
        return {"panels": [], "docs": ()}
    app_dir = Path(settings.BASE_DIR) / feature.app
    formatter = HtmlFormatter(noclasses=True, style="friendly")
    panels = [
        {
            "id": f"snippet-{feature.app}-{name.replace('.', '-')}",
            "title": f"{feature.app}/{name}",
            "html": mark_safe(highlight((app_dir / name).read_text(), PythonLexer(), formatter)),  # noqa: S308
        }
        for name in SNIPPET_FILES
        if (app_dir / name).exists()
    ]
    return {"panels": panels, "docs": feature.docs}
