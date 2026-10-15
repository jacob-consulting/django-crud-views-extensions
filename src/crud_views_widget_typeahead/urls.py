from django.urls import path

from . import views

app_name = "crud_views_typeahead"

urlpatterns = [path("", views.lookup_view, name="lookup")]
