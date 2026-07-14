from django.apps import AppConfig


class CrudViewsWidgetDatetimepickerConfig(AppConfig):
    name = "crud_views_widget_datetimepicker"
    verbose_name = "CRUD Views Widget: xdsoft DateTimePicker"

    def ready(self):
        from crud_views.lib.assets import register_assets

        from . import checks  # noqa: F401  (import registers the system check)
        from .assets import bundle
        from .conf import get_config

        cfg = get_config()
        b = bundle(cfg.source, cfg.version, cfg.cdn_base)
        register_assets(key="datetimepicker", js=b["js"], css=b["css"], emit=cfg.emit)
