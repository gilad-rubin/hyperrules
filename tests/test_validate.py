from rules import validate


def test_valid_tree_has_no_errors():
    tree = {"combinator": "and", "rules": [
        {"field": "document_tag", "operator": "in", "value": ["drug_leaflet"]},
    ]}
    assert validate(tree) == []


def test_unknown_operator_is_reported():
    errors = validate({"field": "x", "operator": "wat", "value": 1})
    assert errors and any("operator" in e for e in errors)


def test_leaf_missing_field_is_reported():
    assert any("field" in e for e in validate({"operator": "=", "value": 1}))


def test_group_with_unknown_combinator_is_reported():
    assert any("combinator" in e for e in validate({"combinator": "xor", "rules": []}))


def test_group_missing_rules_list_is_reported():
    assert any("rules" in e for e in validate({"combinator": "and"}))


def test_errors_surface_from_nested_children_with_path():
    tree = {"combinator": "and", "rules": [
        {"field": "ok", "operator": "=", "value": 1},
        {"combinator": "or", "rules": [{"field": "n", "operator": "wat", "value": 2}]},
    ]}
    assert any("rules[1].rules[0]" in e for e in validate(tree))
