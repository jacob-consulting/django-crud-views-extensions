from pathlib import Path

import crud_views_widget_typeahead as pkg

STATIC = Path(pkg.__file__).parent / "static" / "crud_views_widget_typeahead"


def test_js_contract():
    js = (STATIC / "typeahead-select.js").read_text()
    assert "[data-cv-typeahead-select]" in js
    assert "cv:modal:loaded" in js
    assert "cv:formset:row-added" in js
    assert "window.cvTypeaheadSelect" in js
    assert "AbortController" in js
    assert "requestSubmit" in js
    assert "aria-activedescendant" in js
    assert "stopPropagation" in js  # Escape must not close a surrounding Bootstrap modal
    assert "page=" in js


def test_js_ignores_ime_composition_keys():
    js = (STATIC / "typeahead-select.js").read_text()
    assert "isComposing" in js


def test_js_does_not_toggle_show_class_on_the_popup():
    js = (STATIC / "typeahead-select.js").read_text()
    assert '"show"' not in js


def test_js_is_csp_and_xss_safe():
    js = (STATIC / "typeahead-select.js").read_text()
    assert "innerHTML" not in js
    assert "insertAdjacentHTML" not in js
    assert ".style." not in js
    assert "eval(" not in js
    assert "console.log" not in js
    assert "jQuery" not in js and "$(" not in js


def test_js_does_not_touch_the_text_typeahead():
    js = (STATIC / "typeahead-select.js").read_text()
    assert "window.cvTypeahead " not in js and "window.cvTypeahead=" not in js
    assert "[data-cv-typeahead]" not in js


def test_css():
    css = (STATIC / "typeahead-select.css").read_text()
    for selector in (
        ".cv-typeahead-select",
        ".cv-typeahead-select-popup",
        ".cv-typeahead-select-list",
        ".cv-typeahead-select-placeholder",
        ".cv-typeahead-select-clear",
    ):
        assert selector in css, selector
