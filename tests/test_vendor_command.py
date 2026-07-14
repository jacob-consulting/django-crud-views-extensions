import json

import pytest
from django.core.management import CommandError, call_command

from crud_views.lib.vendor import STAMP_NAME


def test_command_requires_vendor_dir(settings):
    settings.CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored"}
    with pytest.raises(CommandError, match="VENDOR_DIR"):
        call_command("cv_vendor_datetimepicker")


def test_command_vendors_all_files(settings, tmp_path, mocker):
    settings.CRUD_VIEWS_DATETIMEPICKER = {
        "SOURCE": "vendored",
        "VERSION": "2.5.21",
        "VENDOR_DIR": str(tmp_path),
    }
    fake = mocker.patch("crud_views.lib.vendor.urllib.request.urlopen")
    fake.return_value.__enter__.return_value.read.return_value = b"content"

    call_command("cv_vendor_datetimepicker")

    target = tmp_path / "crud_views_widget_datetimepicker" / "2.5.21"
    names = sorted(p.name for p in target.iterdir())
    assert names == sorted(
        [
            STAMP_NAME,
            "jquery.datetimepicker.css",
            "jquery.datetimepicker.full.js",
            "jquery.datetimepicker.full.min.js",
            "jquery.datetimepicker.min.css",
        ]
    )
    assert json.loads((target / STAMP_NAME).read_text())["version"] == "2.5.21"


def test_vendored_paths_match_source_files(settings, tmp_path, mocker):
    """Guard: what the command writes is exactly what source_files() points at."""
    from crud_views_widget_datetimepicker.assets import source_files

    settings.CRUD_VIEWS_DATETIMEPICKER = {
        "SOURCE": "vendored",
        "VERSION": "2.5.21",
        "VENDOR_DIR": str(tmp_path),
    }
    fake = mocker.patch("crud_views.lib.vendor.urllib.request.urlopen")
    fake.return_value.__enter__.return_value.read.return_value = b"content"

    call_command("cv_vendor_datetimepicker")

    for minified in (True, False):
        files = source_files("2.5.21", minified=minified)
        for static_path in [*files["js"], *files["css"]]:
            if static_path.endswith("init.js"):
                continue  # init.js ships inside the app's static/, not VENDOR_DIR
            assert (tmp_path / static_path).exists(), static_path
