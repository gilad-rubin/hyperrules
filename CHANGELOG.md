# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-21

### Added

- FieldSpec builder API (`field.select()`, `field.multi_select()`, `field.bool()`, `field.text()`, `field.int()`, `field.float()`) for typed field declarations with operator-aware condition builders
- Builder methods on FieldSpec: `.eq()`, `.neq()`, `.is_in()`, `.not_in()`, `.is_true()`, `.is_false()`, `.gt()`, `.lt()`, `.contains()` that produce Leaf conditions
- `not_in` operator for exclusion matching on both scalar and collection fields
- `to_dict()` serialization on FieldSpec for schema transport
- `field` module namespace (`from hyperrules import field`)

### Fixed

- `not_in` operator returns False for missing fields instead of incorrectly matching
- `rule_from_dict()` in codecs now handles simple condition dicts (e.g. `{"document_tag": ["drug_leaflet"]}`) via `_condition_from_dict`
- `_get_children()` raises ValueError on missing conditions key instead of silently returning empty list
- NOT groups now enforce single-child constraint in `evaluate()`

### Changed

- Validation now checks for required leaf keys (`field`, `operator`, `value`) and detects ambiguous groups with both `conditions` and `rules`
- `condition_to_simple_dict()` returns None on duplicate fields instead of silently overwriting

## [0.1.0] - 2026-06-21

### Added

- Zero-dependency predicate-to-payload rule engine with AND/OR/NOT group evaluation
- Schema and Field declaration API for defining rule schemas
- Package renamed from `rules` to `hyperrules`
