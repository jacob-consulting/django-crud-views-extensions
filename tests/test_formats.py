import pytest

from crud_views_widget_datetimepicker.formats import php_to_strftime, strftime_to_php


@pytest.mark.parametrize(
    "strftime, php",
    [
        ("%Y-%m-%d", "Y-m-d"),
        ("%d.%m.%Y", "d.m.Y"),
        ("%d/%m/%y", "d/m/y"),
        ("%H:%M", "H:i"),
        ("%d.%m.%Y %H:%M:%S", "d.m.Y H:i:s"),
    ],
)
def test_round_trip(strftime, php):
    assert strftime_to_php(strftime) == php
    assert php_to_strftime(php) == strftime


@pytest.mark.parametrize("strftime", ["%H:%M:%S.%f", "%b %d %Y", "%I:%M %p", "100%%"])
def test_strftime_with_unsupported_tokens(strftime):
    assert strftime_to_php(strftime) is None


@pytest.mark.parametrize("php", ["D, d M Y", "j.n.Y", r"d\.m\.Y"])
def test_php_with_unsupported_tokens(php):
    assert php_to_strftime(php) is None
