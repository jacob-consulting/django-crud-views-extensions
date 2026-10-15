"""Lookups for the example. CrudViewsWidgetTypeaheadConfig.ready() imports every app's typeahead.py."""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from crud_views_widget_typeahead.lookups import UserLookup, register_user_lookup
from typeahead.models import Team


class DemoUserLookup(UserLookup):
    """Thousands of seeded users share names: show the username too."""

    def label(self, obj) -> str:
        return f"{obj.get_full_name() or obj.get_username()} ({obj.get_username()})"


def _check(request):
    # the endpoint must never reveal more than the pages do: same permission as the team pages
    if not request.user.has_perm("typeahead_example.view_team"):
        raise PermissionDenied


@register_user_lookup("typeahead.team_members", base=DemoUserLookup)
def team_members(request, team):
    _check(request)
    return get_object_or_404(Team, pk=team).members.all()


@register_user_lookup("typeahead.any_member", base=DemoUserLookup)
def any_member(request):
    _check(request)
    return get_user_model().objects.filter(teams__isnull=False).distinct()


class DemoBrowseLookup(DemoUserLookup):
    """The select popup lists the first members on open (min_chars = 0) and loads more on scroll."""

    min_chars = 0


@register_user_lookup("typeahead.team_members_browse", base=DemoBrowseLookup)
def team_members_browse(request, team):
    _check(request)
    return get_object_or_404(Team, pk=team).members.all()
