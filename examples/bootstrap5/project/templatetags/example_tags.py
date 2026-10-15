from django import template

register = template.Library()


def feature_for(view):
    """The Feature card a view belongs to (matched by its ViewSet name), or None."""
    from project.features import FEATURES

    viewset = getattr(view, "cv_viewset", None)
    name = getattr(viewset, "name", None)
    return next((f for f in FEATURES if f.viewset == name), None) if name else None


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
