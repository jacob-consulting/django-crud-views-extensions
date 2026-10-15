"""Lookups for the package tests. Imported by autodiscovery (CrudViewsWidgetTypeaheadConfig.ready)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from crud_views_widget_typeahead.lookups import TypeaheadLookup, register_lookup, register_user_lookup


@register_user_lookup("testapp.group_members")
def group_members(request, group):
    if group == "forbidden":
        raise PermissionDenied
    return get_object_or_404(Group, pk=group).user_set.all()


@register_user_lookup("testapp.all_users")
def all_users(request):
    return get_user_model().objects.all()


@register_lookup("testapp.groups")
class GroupLookup(TypeaheadLookup):
    search_fields = ["name"]
    ordering = ["name"]
    max_results = 2
    login_required = False

    def get_queryset(self, request, **params):
        return Group.objects.all()


@register_lookup("testapp.groups_browse")
class GroupBrowseLookup(GroupLookup):
    """Like testapp.groups, but lists entries with an empty query (the select popup's browse-on-open)."""

    min_chars = 0


@register_user_lookup("testapp.users_in_g_groups")
def users_in_g_groups(request):
    # deliberately un-distinct: a user in two matching groups appears twice
    return get_user_model().objects.filter(groups__name__startswith="g")
