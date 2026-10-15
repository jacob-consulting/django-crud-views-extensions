# Formats & language

## How the format is chosen

Unless you pin a format, the picker format follows the **active request language**. The widget resolves it
in this order, highest first:

1. an explicit picker `format`, from settings `DEFAULTS` or the per-field `config`;
2. Django's `format=` widget argument;
3. the first of the active locale's `DATETIME_INPUT_FORMATS` / `DATE_INPUT_FORMATS` /
   `TIME_INPUT_FORMATS` that the picker can reproduce (see the [token table](#token-table));
4. a fallback every Django locale accepts: `%Y-%m-%d %H:%M` (datetime), `%Y-%m-%d` (date), `%H:%M` (time).

Datetime and time widgets prefer a locale format **without seconds**: the picker offers hours and minutes
only and would fill in the current seconds.

The widget renders the value with that same format and parses submitted values with it, so whatever the
picker writes is accepted on submit, in every locale — for example `2026-10-15 19:00` under `en` and
`15.10.2026 19:00` under `de`. A submitted value that doesn't match is passed on to the field's own
validation unchanged.

## Pinning a format

Pin it on the picker side (PHP-style tokens) or the Django side (strftime tokens):

```python
DatePickerInput(config={"format": "d.m.Y"})
DatePickerInput(format="%d.%m.%Y")
```

or for every widget with `CRUD_VIEWS_DATETIMEPICKER = {"DEFAULTS": {"format": "d.m.Y"}}`. The widget renders
and parses a pinned format itself, so it works in every locale.

## Token table

The picker uses PHP-style format tokens. Only the tokens both sides share are supported:

| strftime (Django) | PHP (picker) | Meaning |
|---|---|---|
| `%d` | `d` | day, 2 digits |
| `%m` | `m` | month, 2 digits |
| `%Y` | `Y` | year, 4 digits |
| `%y` | `y` | year, 2 digits |
| `%H` | `H` | hour 00–23 |
| `%M` | `i` | minute |
| `%S` | `s` | second |

A format using any other token (e.g. `%f`, `%b`, `%p`), or a letter in its literal text, cannot be reproduced:

- a locale format like that is skipped;
- a pinned picker `format` with other tokens is passed to the picker unchanged — the field's
  `input_formats` must then accept what the picker writes;
- a Django `format=` the picker cannot reproduce leaves the picker on its own default format, while Django
  renders with `format`, but submitted values are parsed by the field's `input_formats`, which must then accept
  that format (and whatever the picker writes).

## Language

The picker language is the active request language (its first segment: `de-at` → `de`) unless one is set
explicitly:

- for every widget with settings `LANG`, e.g. `CRUD_VIEWS_DATETIMEPICKER = {"LANG": "de"}`;
- per field with `config={"lang": "de"}`.

Without an active language, the first segment of `LANGUAGE_CODE` is used.

!!! warning
    The plugin's language is page-global (`jQuery.datetimepicker.setLocale`): one field with its own `lang`
    switches every picker on that page.
