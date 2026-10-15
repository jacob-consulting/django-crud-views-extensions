from django import template

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
