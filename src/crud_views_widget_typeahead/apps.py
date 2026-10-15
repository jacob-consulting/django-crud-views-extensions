from django.apps import AppConfig


class CrudViewsWidgetTypeaheadConfig(AppConfig):
    name = "crud_views_widget_typeahead"
    verbose_name = "CRUD Views Widget: Typeahead"

    def ready(self):
        from crud_views.lib.assets import register_assets
        from django.utils.module_loading import autodiscover_modules

        from .assets import bundle, select_bundle
        from .conf import get_config

        cfg = get_config()
        b = bundle()
        register_assets(key="typeahead", js=b["js"], css=b["css"], emit=cfg.emit)
        sb = select_bundle()
        register_assets(key="typeahead_select", js=sb["js"], css=sb["css"], emit=cfg.select_emit)
        # admin-style: import every installed app's typeahead.py so its lookups register
        autodiscover_modules("typeahead")
