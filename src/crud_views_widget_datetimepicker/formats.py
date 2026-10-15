"""Conversion between Python strftime formats and the PHP-style formats the xdsoft picker uses.

Django-free on purpose (like assets.py). Only the numeric tokens that both sides share are
supported; any other token makes the conversion return None, so callers can skip formats the
picker cannot reproduce exactly (e.g. ``%f``, ``%b``, ``%p``).
"""

import re

_STRFTIME_TO_PHP = {"d": "d", "m": "m", "Y": "Y", "y": "y", "H": "H", "M": "i", "S": "s"}
_PHP_TO_STRFTIME = {php: strftime for strftime, php in _STRFTIME_TO_PHP.items()}


def strftime_to_php(fmt: str) -> str | None:
    """``"%d.%m.%Y"`` -> ``"d.m.Y"``; None if the format uses an unsupported token."""
    out = []
    for literal, token in re.findall(r"([^%]*)(?:%(.))?", fmt):
        if re.search(r"[A-Za-z\\]", literal):
            return None  # letters are format codes in PHP formats; we don't escape them
        out.append(literal)
        if token:
            if token not in _STRFTIME_TO_PHP:
                return None
            out.append(_STRFTIME_TO_PHP[token])
    return "".join(out)


def php_to_strftime(fmt: str) -> str | None:
    """``"d.m.Y"`` -> ``"%d.%m.%Y"``; None if the format uses an unsupported token or escape."""
    out = []
    for ch in fmt:
        if ch in _PHP_TO_STRFTIME:
            out.append("%" + _PHP_TO_STRFTIME[ch])
        elif ch.isalpha() or ch in "\\%":
            return None
        else:
            out.append(ch)
    return "".join(out)
