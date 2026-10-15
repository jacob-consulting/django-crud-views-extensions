from django.apps import AppConfig


class TypeaheadExampleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "typeahead"
    label = "typeahead_example"  # distinct from the crud_views_widget_typeahead app label
