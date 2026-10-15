# Skins

A design-system package can replace the whole frontend of either widget and keep the server core (lookups,
fields, endpoint). A skin consists of a template, its own JS/CSS, and the behaviours below.

The default templates are a good starting point:
[`typeahead.html` and `typeahead_select.html`](https://github.com/jacob-consulting/django-crud-views-extensions/tree/main/src/crud_views_widget_typeahead/templates/crud_views_widget_typeahead).

## Text typeahead

### 1. Template

Set `CRUD_VIEWS_TYPEAHEAD["TEMPLATE"]`, or a widget's `template_name`. The template gets:

- `widget.attrs` — the visible input's attributes: `id`, `class` (including `form-control`), `autocomplete="off"`,
  `role="combobox"`, `aria-autocomplete="list"`, `aria-expanded`, `aria-controls` and the merged
  `aria-describedby`.
- `widget.typeahead`:

| Key | Meaning |
|---|---|
| `url` | endpoint URL including the token; append `&q=…` |
| `label`, `value` | label and pk of the selected object (empty when nothing is selected) |
| `hidden_name`, `hidden_id` | `name` and `id` of the hidden input |
| `listbox_id`, `hint_id` | ids for the listbox and the screen-reader hint |
| `min_chars`, `debounce` | from the lookup and the settings |
| `submit_on_clear` | the widget argument |
| `i18n` | translated strings: `hint`, `more`, `none`, `count`, `error`, `clear`, `listbox`; `{n}` is the number placeholder |

### 2. Assets

Register your own JS/CSS and switch off ours:

```python
# your_skin/apps.py
from django.apps import AppConfig


class YourSkinConfig(AppConfig):
    name = "your_skin"

    def ready(self):
        from crud_views.lib.assets import register_assets

        register_assets(key="your_skin_typeahead", js=["your_skin/typeahead.js"], css=["your_skin/typeahead.css"])
```

```python
CRUD_VIEWS_TYPEAHEAD = {"TEMPLATE": "your_skin/typeahead.html", "EMIT": False}
```

### 3. Contract

The hidden input:

- carries the field's `name` and the pk, with `autocomplete="off"`;
- is empty when nothing is selected.

Behaviours:

- The visible text is the label of the stored pk, except while typing. Restore it on blur and on submit.
- Clear the selection only via a clear button or fully emptied text.
- Arrow keys preview text only; they don't select.
- Enter never submits while the list is open, nor while the typed text is not yet a selection.
- Escape and highlight labels yourself — never insert server text as HTML.
- Show "N more" from the response's `count`.
- Use the ARIA combobox/listbox pattern with a live result count.
- Re-initialise on `cv:modal:loaded`.

## Select popup

The same three steps, with these differences:

- Template: `CRUD_VIEWS_TYPEAHEAD["SELECT_TEMPLATE"]` (or `template_name`). `widget.attrs` land on the
  **trigger button**: `class` (including `form-select text-start`), `aria-haspopup="listbox"`, `aria-expanded`,
  `aria-controls` and `aria-labelledby="<id> <id>_label"`.
- `widget.typeahead` has every key above plus `popup_id`, `label_id`, `search_id` and `page_size`, and
  `i18n` also has `placeholder`, `search`, `loading` and `type_more`.
- Switch off our assets with `SELECT_EMIT = False`.
- Keep the hidden-input contract and the behaviours of the [select popup](widgets.md#select-popup): paging on
  scroll, Enter never submits while open, Escape closes only the popup.

## JavaScript API

The default frontends expose an `init(root)` function for content added after page load:

```javascript
window.cvTypeahead.init(container);
window.cvTypeaheadSelect.init(container);
```

A skin should offer the same and re-initialise on `cv:modal:loaded`.
