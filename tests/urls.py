from django.urls import include, path

urlpatterns = [path("typeahead/", include("crud_views_widget_typeahead.urls"))]
