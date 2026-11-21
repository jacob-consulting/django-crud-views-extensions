"""The typeahead skins read ``--cv-*`` tokens with Bootstrap and hard fallbacks, and never declare them."""

import re
from pathlib import Path

import pytest

import crud_views_widget_typeahead

STATIC = Path(crud_views_widget_typeahead.__file__).parent / "static" / "crud_views_widget_typeahead"
SKINS = [STATIC / "typeahead.css", STATIC / "typeahead-select.css"]
SKINS_DOC = Path(__file__).parents[1] / "docs" / "reference" / "typeahead" / "skins.md"

CHAINS = {
    "--cv-secondary-color": "var(--cv-secondary-color, var(--bs-secondary-color, #6c757d))",
    "--cv-body-bg": "var(--cv-body-bg, var(--bs-body-bg, #fff))",
    "--cv-border-radius": "var(--cv-border-radius, var(--bs-border-radius, .375rem))",
    "--cv-border-color-translucent": (
        "var(--cv-border-color-translucent, var(--bs-border-color-translucent, rgba(0, 0, 0, .175)))"
    ),
    "--cv-highlight-bg": "var(--cv-highlight-bg, var(--bs-highlight-bg, #fff3cd))",
}

_VAR = re.compile(r"(?<![\w-])var\(")
_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_DECLARATION = re.compile(r"(^|[;{\s])--[\w-]+\s*:")


def _normalise(expr: str) -> str:
    return re.sub(r"\s+", "", expr)


def _strip_comments(css: str) -> str:
    return _COMMENT.sub("", css)


def _balanced(text: str, start: int) -> int:
    """Index just past the ``)`` closing the ``(`` that ends the ``var(`` match starting at ``start``."""
    depth = 0
    for i in range(text.index("(", start), len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError(f"unbalanced var() at {start}")


def iter_vars(css: str) -> list[str]:
    """Every outermost ``var(...)``, comments stripped, whitespace removed."""
    css = _strip_comments(css)
    found, pos = [], 0
    while match := _VAR.search(css, pos):
        end = _balanced(css, match.start())
        found.append(_normalise(css[match.start() : end]))
        pos = end
    return found


def offenders(css: str) -> list[str]:
    """Outermost ``var()`` expressions touching ``--cv-``/``--bs-`` that are not one of the canonical chains."""
    canonical = {_normalise(chain) for chain in CHAINS.values()}
    return [expr for expr in iter_vars(css) if ("--cv-" in expr or "--bs-" in expr) and expr not in canonical]


def _tokens_used(css: str) -> set[str]:
    return {re.match(r"var\((--cv-[\w-]+)", expr).group(1) for expr in iter_vars(css) if expr.startswith("var(--cv-")}


def test_scanner_normalises_whitespace():
    assert iter_vars("a{b:var( --cv-body-bg ,var(--bs-body-bg,#fff) )}") == [_normalise(CHAINS["--cv-body-bg"])]


def test_scanner_finds_nested_bare_bs():
    assert offenders("a{b:calc(var(--bs-border-radius) - 1px)}") == ["var(--bs-border-radius)"]


def test_scanner_ignores_comments():
    assert iter_vars("/* var(--bs-body-bg) */ a{}") == []


def test_scanner_rejects_mismatched_middle():
    assert offenders("a{b:var(--cv-body-bg, var(--bs-secondary-color, #fff))}") != []


@pytest.mark.parametrize("skin", SKINS, ids=lambda p: p.name)
def test_every_var_is_a_known_chain(skin):
    assert offenders(skin.read_text()) == [], f"{skin.name} reads --bs-*/--cv-* outside the token chains"


def test_chains_have_hard_fallback():
    for token, chain in CHAINS.items():
        assert chain.startswith(f"var({token}, var(--bs-{token[len('--cv-') :]}, "), token
        innermost = chain.split(", ", 2)[2]
        assert not innermost.startswith("var("), token


@pytest.mark.parametrize("skin", SKINS, ids=lambda p: p.name)
def test_no_custom_property_declarations(skin):
    assert not _DECLARATION.search(_strip_comments(skin.read_text())), f"{skin.name} declares a custom property"


def test_all_tokens_used():
    used = set().union(*(_tokens_used(skin.read_text()) for skin in SKINS))
    assert used == set(CHAINS)
