from django.core.management.base import BaseCommand, CommandError

from crud_views.lib.vendor import VendorSpec, vendor

from ...assets import ALL_FILES, APP_LABEL
from ...conf import get_config


class Command(BaseCommand):
    help = (
        "Download the pinned jquery-datetimepicker version (all four file variants) "
        "into CRUD_VIEWS_DATETIMEPICKER['VENDOR_DIR']."
    )

    def handle(self, *args, **options):
        cfg = get_config()
        if cfg.vendor_dir is None:
            raise CommandError("CRUD_VIEWS_DATETIMEPICKER['VENDOR_DIR'] must be set.")
        spec = VendorSpec(
            key="datetimepicker",
            version=cfg.version,
            base_url=cfg.cdn_base,
            files=ALL_FILES,
            target=cfg.vendor_dir / APP_LABEL / cfg.version,
        )
        for path in vendor(spec):
            self.stdout.write(f"vendored {path}")
        self.stdout.write(
            self.style.SUCCESS(
                f"Vendored jquery-datetimepicker {cfg.version}. "
                f"Make sure {cfg.vendor_dir} is listed in STATICFILES_DIRS."
            )
        )
