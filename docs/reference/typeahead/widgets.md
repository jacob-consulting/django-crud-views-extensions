# Widgets

Two widgets in `crud_views_widget_typeahead.widgets` work with the same fields, filters, lookups and
endpoint. Choose one per field; both can appear on one page.

| Widget | Looks like | Use when |
|---|---|---|
| `TypeaheadInput` (default) | a text input with a suggestion list | users know what they're looking for |
| `TypeaheadSelect` | a Bootstrap `<select>` opening a popup with a search field and a scroll-paged list | users want to browse |

```python
from crud_views_widget_typeahead.widgets import TypeaheadSelect

assignee = TypeaheadField(lookup="projects.members", widget=TypeaheadSelect())
assignee = TypeaheadFilter(lookup="projects.members", widget=TypeaheadSelect(submit_on_clear=True))
```

Both take the same arguments:

| Argument | Default | Meaning |
|---|---|---|
| `attrs` | `None` | HTML attributes for the visible input (text typeahead) or the trigger button (select popup) |
| `submit_on_clear` | `False` | submit the form when the selection is cleared; `TypeaheadFilter` uses `True` |
| `template_name` | `None` | overrides the template from the [settings](settings.md) for this widget |

## Rendering

- The visible input (or trigger button) has **no `name`**. A hidden input carries the field's name and the
  primary key, so the form submits the pk.
- The `required` attribute is never rendered: a required visible input would accept typed text without a pk.
  `required=True` on the field still validates on the server.
- `aria-describedby` is merged with the ids Django adds for help text and errors.

## Text typeahead

The visible text is the label of the selected object, except while you are typing.

- Typing searches after the debounce (`DEBOUNCE_MS`) once `min_chars` are typed. Matches are highlighted.
- **↓** opens the list (searching for the current text); **↑ / ↓** move through it and preview the label.
- **Enter** selects the highlighted option. Enter never submits the form while the list is open, nor while
  the typed text is not yet a selection — then it searches instead.
- **Escape** closes the list and restores the selected label. **Tab** closes the list.
- Leaving the field (or submitting) restores the selected label. Clearing the selection takes the clear button
  or fully emptied text.
- When there are more matches than `max_results`, the list ends with "N more results – keep typing".

## Select popup

`TypeaheadSelect` renders a trigger button with the selected label (or "Select…") and a clear button.

- **Enter**, **Space**, **↑ / ↓**, or typing a character opens the popup and focuses its search field.
- With `min_chars = 0` the popup lists the first page as soon as it opens; otherwise it asks for `min_chars`
  characters first.
- Scrolling to the end of the list loads the next page (page size = the lookup's `max_results`).
- **↑ / ↓** move, **Enter** selects. Enter never submits while the popup is open.
- **Escape** closes only the popup: a surrounding crud_views modal stays open.

## Modals and dynamic content

Both widgets activate on `DOMContentLoaded` and again on the `cv:modal:loaded` event that crud_views
dispatches after injecting modal content. For other dynamically added content (e.g. new formset rows) call:

```javascript
window.cvTypeahead.init(container);        // text typeahead
window.cvTypeaheadSelect.init(container);  // select popup
```

!!! note "Clipping"
    The popup is rendered inside the widget, not at the end of `<body>`, so it works inside crud_views'
    Bootstrap 5 modals. It can therefore be clipped by an ancestor with `overflow: hidden`; inside
    `modal-dialog-scrollable` modals it scrolls within the modal body.
