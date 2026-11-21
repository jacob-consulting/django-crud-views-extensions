# Typeahead skins: `--cv-*` CSS tokens with hard fallbacks (issue #6, U12)

**Date:** 2026-11-21 · **Size:** small change · **Source:** GitHub issue #6 (design approved by the maintainer)

## Intent

The stock typeahead skins read five `--bs-*` custom properties, six of the eight references without a fallback.
Under a Bootstrap fork that renames its properties (CoreUI: `--cui-*`) the select popup turns transparent and the
dark-mode highlight stays light. The skins should read crud_views-owned `--cv-*` tokens, the same scheme as
django-crud-views#394, so that one theme-root mapping covers crud_views and these extensions, and they should
render correctly with no Bootstrap variables defined at all. Plain Bootstrap rendering stays unchanged.

## Goals / non-goals

- Goal: every `--bs-*` reference in `typeahead.css` and `typeahead-select.css` becomes
  `var(--cv-x, var(--bs-x, <hard fallback>))`.
- Goal: docs and a test that enforce the contract; release notes kept from now on in a root `CHANGELOG.md`.
- Non-goals: datetimepicker, templates, JavaScript, Python, tokens beyond the five below.
- Anti-goal: the skins declare a token (a `:root` declaration freezes the value and breaks nested colour modes).

## Tokens (as decided in #6, D-02)

| Token | Reads | |
|---|---|---|
| `--cv-secondary-color` | `var(--cv-secondary-color, var(--bs-secondary-color, #6c757d))` | shared with #394 |
| `--cv-body-bg` | `var(--cv-body-bg, var(--bs-body-bg, #fff))` | shared with #394 |
| `--cv-border-radius` | `var(--cv-border-radius, var(--bs-border-radius, .375rem))` | shared with #394 |
| `--cv-border-color-translucent` | `var(--cv-border-color-translucent, var(--bs-border-color-translucent, rgba(0, 0, 0, .175)))` | new |
| `--cv-highlight-bg` | `var(--cv-highlight-bg, var(--bs-highlight-bg, #fff3cd))` | new |

Themes that still re-define `--bs-*` on `.cv-typeahead, .cv-typeahead-select` keep working through the middle of
the chain. There is no ordering dependency on #394; only the names have to match.

## Approaches

### Token scheme (from the issue)

1. **#394 token pattern (picked by the maintainer):** one scheme across crud_views and its extensions.
2. Document the `--bs-*` names as the contract: rejected, because themes re-define Bootstrap names on upstream
   selectors and new rules then break silently.
3. One central token list in crud_views' docs: rejected, because it ties crud_views' docs to this package's CSS.

### Release notes (decided 2026-11-21)

1. **`CHANGELOG.md` at the repo root, Keep a Changelog format (picked by the maintainer):** it matches the skill
   plugin's changelog and the `## [Unreleased]` flow.
2. `docs/changelog.md` on Read the Docs: not picked.
3. GitHub release notes at tag time only: not picked.

## The work

- **CSS:** rewrite the 8 references to the chains above. Nothing else in the files changes.
- **Test** (new, `tests/test_typeahead_css_tokens.py`), over both skins:
  - fails on any `var(--bs-…)` that is not the fallback inside one of the five chains;
  - fails on any `--cv-*` chain without a hard (non-`var`) fallback, or with a mismatched `--bs-*` middle;
  - fails on any `--cv-*` declaration (`--cv-x:`);
  - fails on any token used in the skins that is missing from the docs table in `skins.md`.
- **Docs:** a "CSS tokens" section in `docs/reference/typeahead/skins.md`: the five tokens marked shared/new,
  a link to crud_views' "CSS tokens" section (#394) for the naming rule and the theme-root mapping, and a note
  that a custom skin may read the same tokens.
- **`CHANGELOG.md`** (new): Keep a Changelog header and `## [Unreleased]` with `Added` (the five tokens) and
  `Fixed` (missing fallbacks; select popup transparent, highlight wrong under non-Bootstrap themes).
- **`docs/development/releasing.md`:** one step: rename `## [Unreleased]` to the new version and date before the
  bump commit.
- **Skill** (sibling repo `../skills/plugins/django-crud-views-extensions/`): add the tokens to the "Skins"
  section of `references/typeahead.md` (*Available since* the next version) and a line under `## [Unreleased]` in
  the plugin's `CHANGELOG.md`. Releasing the plugin stays with the maintainer.

## Calls made by the designer (correct if wrong)

- The test parses with a small balanced-parenthesis scanner in the test itself, no new dependency (tinycss2 is
  not in the env).
- The changelog starts at `[Unreleased]`; earlier versions are not back-filled.
- "With no Bootstrap variables the popup is opaque" is covered by the hard-fallback rule in the test, not by a
  browser test.

## Left to the builder

Formatting of the CSS chains and the exact docs wording.
