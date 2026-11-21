# Typeahead CSS Tokens Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The two typeahead skins read five `--cv-*` tokens through `var(--cv-x, var(--bs-x, <hard fallback>))`,
enforced by a test, documented in `skins.md`, recorded in a new root `CHANGELOG.md`, and mirrored in the skill.

**Architecture:** CSS-only change in `crud_views_widget_typeahead/static/`. A test scans both CSS files with a
small balanced-parenthesis `var()` scanner (no new dependency) and cross-checks the token table in
`docs/reference/typeahead/skins.md`.

**Tech Stack:** CSS custom properties, pytest, MkDocs, Keep a Changelog 1.1.0.

**Spec:** `docs/superpowers/specs/2026-11-21-typeahead-css-tokens-design.md` (source: GitHub issue #6)

## Global Constraints

- Exactly these five chains, values verbatim:
  - `var(--cv-secondary-color, var(--bs-secondary-color, #6c757d))`
  - `var(--cv-body-bg, var(--bs-body-bg, #fff))`
  - `var(--cv-border-radius, var(--bs-border-radius, .375rem))`
  - `var(--cv-border-color-translucent, var(--bs-border-color-translucent, rgba(0, 0, 0, .175)))`
  - `var(--cv-highlight-bg, var(--bs-highlight-bg, #fff3cd))`
- The skins never declare a `--cv-*` (or any) custom property.
- No changes to templates, JS, Python, or the datetimepicker app.
- Ruff: line-length 120, double quotes. `mkdocs build --strict` must pass.
- Next package version is assumed **0.4.0** (new public tokens → minor) for "Available since" markers.

## Review Focus

1. A whitespace/formatting variant of a chain (e.g. `var( --cv-body-bg ,var(--bs-body-bg,#fff) )`) must still be
   recognised — the scanner normalises whitespace before comparing (test: `test_scanner_normalises_whitespace`).
2. A `var(--bs-x)` hidden inside some other function (e.g. `calc(var(--bs-border-radius) - 1px)`) must be caught,
   not skipped (test: `test_scanner_finds_nested_bare_bs`).
3. A CSS comment mentioning `var(--bs-…)` must not trip the test — strip `/* … */` before scanning
   (test: `test_scanner_ignores_comments`).
4. A chain whose middle names a different `--bs-*` than its token (`var(--cv-body-bg, var(--bs-secondary-color, #fff))`)
   must fail — covered by exact comparison against the canonical chains.
5. The docs table drifting from the CSS (token renamed in one place only) must fail — `test_tokens_documented`.

---

### Task 1: Token test and CSS chains

**Files:**
- Create: `tests/test_typeahead_css_tokens.py`
- Modify: `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead.css` (lines 26, 37)
- Modify: `src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.css` (lines 22, 42–44, 73, 84)

**Interfaces:**
- Produces (module-level in the test file, used by Task 2's docs test in the same file):
  - `CHAINS: dict[str, str]` — token name (`"--cv-body-bg"`) → canonical chain string, values from Global Constraints.
  - `SKINS: list[Path]` — the two CSS files, resolved via `Path(crud_views_widget_typeahead.__file__).parent / "static" / "crud_views_widget_typeahead"`.
  - `iter_vars(css: str) -> list[str]` — every outermost `var(...)` expression, comments stripped, whitespace
    normalised (collapse runs to nothing around `(`, `)`, `,`; single space after `,` as in the canonical form —
    normalise canonical strings the same way before comparing).
  - `inner_vars(expr: str) -> list[str]` — all `var(...)` expressions at any depth, including inside `calc()`.

- [ ] **Step 1: Write the failing tests**

  - `test_scanner_normalises_whitespace` — `iter_vars("a{b:var( --cv-body-bg ,var(--bs-body-bg,#fff) )}")` normalises equal to `CHAINS["--cv-body-bg"]`.
  - `test_scanner_finds_nested_bare_bs` — on `"a{b:calc(var(--bs-border-radius) - 1px)}"` the bare `--bs-` check reports one offender.
  - `test_scanner_ignores_comments` — `iter_vars("/* var(--bs-body-bg) */ a{}") == []`.
  - `test_every_var_is_a_known_chain[<skin>]` (parametrised over `SKINS`) — every outermost `var()` that references `--cv-` or `--bs-` equals a value of `CHAINS`; any `var(--bs-…)` not inside such a chain fails with the file and expression in the message.
  - `test_chains_have_hard_fallback` — for each value of `CHAINS`, the innermost fallback does not start with `var(` (guards future edits of `CHAINS`).
  - `test_no_custom_property_declarations[<skin>]` — no match of `r"(^|[;{\s])--[\w-]+\s*:"` in the comment-stripped CSS.
  - `test_all_tokens_used` — the union of tokens used across both skins equals `set(CHAINS)` (so `CHAINS` holds no dead tokens).

- [ ] **Step 2: Run to verify failure**

  Run: `uv run pytest tests/test_typeahead_css_tokens.py -v`
  Expected: scanner tests PASS; `test_every_var_is_a_known_chain` FAILS for both skins (bare `var(--bs-…)`);
  `test_all_tokens_used` FAILS.

- [ ] **Step 3: Rewrite the 8 references** in the two CSS files to the canonical chains. Change nothing else.

- [ ] **Step 4: Run to verify pass**

  Run: `uv run pytest tests/test_typeahead_css_tokens.py -v && uv run pytest`
  Expected: all PASS (full suite: 223 + new tests).

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check . && uv run ruff format .
git add tests/test_typeahead_css_tokens.py src/crud_views_widget_typeahead/static/
git commit -m "fix(typeahead): read --cv-* tokens with hard fallbacks in the skins (#6)"
```

### Task 2: Docs, changelog, releasing step

**Files:**
- Modify: `docs/reference/typeahead/skins.md` (new `## CSS tokens` section, between "Select popup" and "JavaScript API")
- Modify: `tests/test_typeahead_css_tokens.py` (add docs test)
- Create: `CHANGELOG.md`
- Modify: `docs/development/releasing.md` (Steps block)

**Interfaces:**
- Consumes: `CHAINS` from Task 1.

- [ ] **Step 1: Write the failing test** `test_tokens_documented` — parse the `## CSS tokens` section of
  `docs/reference/typeahead/skins.md` (path from repo root via `Path(__file__).parents[1]`), collect the
  backticked `--cv-*` names in the first table column; assert the set equals `set(CHAINS)`.

- [ ] **Step 2: Run** `uv run pytest tests/test_typeahead_css_tokens.py::test_tokens_documented -v` — Expected: FAIL (section missing).

- [ ] **Step 3: Write the docs section.** Content:
  - One-paragraph intro: the stock skins read crud_views-owned `--cv-*` tokens, each falling back to the
    Bootstrap property of the same name and then to a fixed value, so they render under Bootstrap forks
    (e.g. CoreUI's `--cui-*`) and with no Bootstrap variables at all. Set the tokens on your theme roots; the skins
    never declare them.
  - Table, columns `Token | Falls back to | ` with rows for the five tokens; the last column says
    "shared with crud_views" for `--cv-secondary-color`, `--cv-body-bg`, `--cv-border-radius` and "typeahead only"
    for `--cv-border-color-translucent`, `--cv-highlight-bg`. Fallback column: `--bs-x`, then the hard value.
  - Naming rule and theme-root mapping: link to django-crud-views#394
    (`https://github.com/jacob-consulting/django-crud-views/issues/394`). Its docs section does not exist yet; link
    the issue, and note in the commit message that the link should move to the docs section once #394 ships.
  - Note: themes that re-define `--bs-*` on `.cv-typeahead, .cv-typeahead-select` keep working.
  - Note: a custom skin may read the same tokens.
  - No definition lists (extension not enabled).

- [ ] **Step 4: Create `CHANGELOG.md`** — Keep a Changelog 1.1.0 header (same wording style as
  `../skills/plugins/django-crud-views-extensions/CHANGELOG.md`, minus the plugin-specific paragraph) and:

  ```markdown
  ## [Unreleased]

  ### Added
  - Typeahead skins read `--cv-*` CSS tokens (`--cv-secondary-color`, `--cv-body-bg`, `--cv-border-radius`,
    `--cv-border-color-translucent`, `--cv-highlight-bg`), so a theme maps one token set for crud_views and these
    extensions. See docs/reference/typeahead/skins.md#css-tokens.

  ### Fixed
  - Every `--bs-*` reference in the typeahead skins now has a hard fallback: under Bootstrap forks that rename their
    properties (CoreUI) the select popup is no longer transparent and the match highlight follows the theme.
  ```
  No back-filled history.

- [ ] **Step 5: Releasing step** — in `docs/development/releasing.md` Steps, before the bump: a comment line
  `# CHANGELOG.md: rename "## [Unreleased]" to "## [0.4.0] — YYYY-MM-DD", add a fresh "## [Unreleased]"`, and a
  sentence after the code block saying the changelog edit goes into the same bump commit.

- [ ] **Step 6: Verify**

  Run: `uv run pytest && uv run --no-project --with-requirements docs/requirements.txt mkdocs build --strict`
  Expected: all tests PASS; mkdocs builds with no warnings.

- [ ] **Step 7: Commit**

```bash
git add docs/reference/typeahead/skins.md docs/development/releasing.md CHANGELOG.md tests/test_typeahead_css_tokens.py
git commit -m "docs: document typeahead CSS tokens, start CHANGELOG.md (#6)"
```

### Task 3: Skill update (sibling repo, not released)

**Files:**
- Modify: `../skills/plugins/django-crud-views-extensions/skills/django-crud-views-extensions/references/typeahead.md` ("Skins" section, after the select-popup paragraph)
- Modify: `../skills/plugins/django-crud-views-extensions/CHANGELOG.md` (`## [Unreleased]`)

- [ ] **Step 1:** Add a short "CSS tokens" paragraph to the Skins section, marked `*Available since 0.4.0*`: the five
  tokens with their chains (compact list), "set them on theme roots, never declare them in a skin", custom skins
  may read them, older themes re-defining `--bs-*` on `.cv-typeahead, .cv-typeahead-select` still work.
- [ ] **Step 2:** Under the plugin's `## [Unreleased]` add `### Added` — "Package 0.4.0: typeahead skins read
  `--cv-*` CSS tokens with hard fallbacks; Skins reference lists them."
- [ ] **Step 3:** Show the diff (`git -C ../skills diff`) to the maintainer. Do **not** commit or release in the
  sibling repo unless asked.
