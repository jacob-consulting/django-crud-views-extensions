from django.apps import apps


def test_app_is_installed():
    config = apps.get_app_config("crud_views_widget_datetimepicker")
    assert config.verbose_name == "CRUD Views Widget: xdsoft DateTimePicker"
