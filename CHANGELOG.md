# Changelog

All notable changes to `django-crud-views-extensions` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Typeahead skins read `--cv-*` CSS tokens (`--cv-secondary-color`, `--cv-body-bg`, `--cv-border-radius`,
  `--cv-border-color-translucent`, `--cv-highlight-bg`), so a theme maps one token set for crud_views and these
  extensions. See [CSS tokens](docs/reference/typeahead/skins.md#css-tokens).

### Fixed
- Every `--bs-*` reference in the typeahead skins now has a hard fallback: under Bootstrap forks that rename their
  properties (CoreUI) the select popup is no longer transparent and the match highlight follows the theme.
