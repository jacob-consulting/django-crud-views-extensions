from django.core.checks import Error, register

from crud_views.lib.vendor import VendorSpec, check_vendored

from .assets import ALL_FILES, APP_LABEL
from .conf import get_config


@register("crud_views")
def check_datetimepicker(app_configs=None, **kwargs):
    cfg = get_config()
    if cfg.source not in ("cdn", "vendored"):
        return [
            Error(
                "CRUD_VIEWS_DATETIMEPICKER['SOURCE'] must be 'cdn' or 'vendored'.",
                hint="Set SOURCE to 'cdn' (default) or 'vendored'.",
                id="crud_views.E333",
            )
        ]
    if cfg.source != "vendored":
        return []
    if cfg.vendor_dir is None:
        return [
            Error(
                "CRUD_VIEWS_DATETIMEPICKER: SOURCE is 'vendored' but VENDOR_DIR is not set.",
                hint="Set VENDOR_DIR to a project directory that is listed in STATICFILES_DIRS.",
                id="crud_views.E332",
            )
        ]
    spec = VendorSpec(
        key="datetimepicker",
        version=cfg.version,
        base_url=cfg.cdn_base,
        files=ALL_FILES,
        target=cfg.vendor_dir / APP_LABEL / cfg.version,
    )
    return check_vendored(spec)
