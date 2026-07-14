from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from django.conf import settings

DEFAULT_VERSION = "2.5.21"
DEFAULT_CDN_BASE = "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/"


@dataclass(frozen=True)
class DatetimepickerConfig:
    source: str = "cdn"
    version: str = DEFAULT_VERSION
    cdn_base: str = DEFAULT_CDN_BASE
    vendor_dir: Optional[Path] = None
    emit: bool = True
    lang: str = "en"
    defaults: dict = field(default_factory=dict)


def get_config() -> DatetimepickerConfig:
    raw = getattr(settings, "CRUD_VIEWS_DATETIMEPICKER", {}) or {}
    vendor_dir = raw.get("VENDOR_DIR")
    lang = raw.get("LANG") or settings.LANGUAGE_CODE.split("-")[0]
    return DatetimepickerConfig(
        source=raw.get("SOURCE", "cdn"),
        version=raw.get("VERSION", DEFAULT_VERSION),
        cdn_base=raw.get("CDN_BASE", DEFAULT_CDN_BASE),
        vendor_dir=Path(vendor_dir) if vendor_dir else None,
        emit=raw.get("EMIT", True),
        lang=lang,
        defaults=dict(raw.get("DEFAULTS", {})),
    )
