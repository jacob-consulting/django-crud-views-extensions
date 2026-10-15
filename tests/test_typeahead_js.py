from pathlib import Path

import crud_views_widget_typeahead as pkg

STATIC = Path(pkg.__file__).parent / "static" / "crud_views_widget_typeahead"


def test_js_contract():
    js = (STATIC / "typeahead.js").read_text()
    assert "[data-cv-typeahead]" in js
    assert "cv:modal:loaded" in js
    assert "window.cvTypeahead" in js
    assert "AbortController" in js
    assert "requestSubmit" in js
    assert "aria-activedescendant" in js


def test_js_is_csp_and_xss_safe():
    js = (STATIC / "typeahead.js").read_text()
    assert "innerHTML" not in js
    assert "insertAdjacentHTML" not in js
    assert ".style." not in js
    assert "eval(" not in js
    assert "console.log" not in js
    assert "jQuery" not in js and "$(" not in js


def test_css_exists():
    css = (STATIC / "typeahead.css").read_text()
    assert ".cv-typeahead-menu" in css
