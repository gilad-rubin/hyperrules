# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-11-09

### Added

- References: a leaf's value may name another field of the context, `{"ref": "user.district"}` (`ref()`, `ref_path()`), so a rule can compare a document with the requesting user's own values. A field spec given as a value is a reference to it (`district.eq(user_district)`).
- A reference may stand inside a list of values (`district.is_in(["National", user_district])`). Inside an `in` list a missing reference is one value fewer; a reference to a list adds each of its values; inside a `not_in` list a missing reference makes the leaf false.
- Field names and references are paths: `user.district` reads the context's `"user.district"` key, else `context["user"]["district"]`. `lookup(context, path)` and its `MISSING` marker are exported.
- Typed save-time checks: `validate(tree, fields=...)` and `validate_rules(rules, fields=...)` take the declared fields (field specs or their dicts) and name, by place, an unknown field or reference, an operator the field's type does not offer, a value or reference of the wrong type, and a value outside a select's options. They accept hypster's leaves and groups too.

### Changed

- The `{field: [values]}` shorthand is never used for a condition holding a reference, so a saved rule keeps it whole; a one-field shorthand loads as an `and` group.

These were first built in Panda's vendored copy (its 0.2.0) and come home here.

## [0.3.0] - 2026-06-21

### Added

- `matches(condition, context)` — renamed from `evaluate()` for readability (`if matches(rule.when, document)`)
- Duck-typed condition dispatch: `matches()` accepts any object with leaf attributes (`.field`, `.operator`, `.value`) or group attributes (`.combinator`, `.conditions`), not just hyperrules' own Leaf/Group classes. This removes the need to import types from hyperrules.
- Guard-first evaluation: missing or None context values return `False` for ALL operators (including `!=` and `is`), before operator dispatch. Previously `!=` on a missing field returned `True` and `is False` on a missing field returned `True`.

### Removed

- `evaluate()` — replaced by `matches()`.
- Legacy `rules` key for group children — use `conditions` instead.

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
