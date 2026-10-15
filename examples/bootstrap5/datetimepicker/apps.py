from django.apps import AppConfig


class DatetimepickerExampleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datetimepicker"
    label = "datetimepicker_example"  # distinct from the crud_views_widget_datetimepicker app label
