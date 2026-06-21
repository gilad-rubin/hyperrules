"""Tests for matches() with structured Leaf/Group types and the 'conditions' key."""

import warnings
from dataclasses import dataclass
from typing import Any

import pytest

from hyperrules import And, Group, Leaf, Not, Or, evaluate, field, matches


def test_evaluate_leaf():
    leaf = Leaf("station", "=", "NICU")
    assert evaluate(leaf, {"station": "NICU"}) is True
    assert evaluate(leaf, {"station": "ER"}) is False


def test_evaluate_and_group():
    group = And(Leaf("a", "=", 1), Leaf("b", "=", 2))
    assert evaluate(group, {"a": 1, "b": 2}) is True
    assert evaluate(group, {"a": 1, "b": 9}) is False


def test_evaluate_or_group():
    group = Or(Leaf("a", "=", 1), Leaf("b", "=", 2))
    assert evaluate(group, {"a": 1, "b": 9}) is True
    assert evaluate(group, {"a": 9, "b": 9}) is False


def test_evaluate_not_group():
    group = Not(Leaf("a", "=", 1))
    assert evaluate(group, {"a": 2}) is True
    assert evaluate(group, {"a": 1}) is False


def test_evaluate_nested_structured():
    condition = And(
        Leaf("document_tag", "in", ["drug_leaflet"]),
        Or(Leaf("document_station", "=", "NICU"), Leaf("vision_page_presence", "is", True)),
    )
    assert evaluate(condition, {"document_tag": ["drug_leaflet"], "document_station": "NICU"}) is True
    assert evaluate(condition, {"document_tag": ["drug_leaflet"], "document_station": "ER", "vision_page_presence": True}) is True
    assert evaluate(condition, {"document_tag": ["drug_leaflet"], "document_station": "ER", "vision_page_presence": False}) is False


def test_evaluate_dict_with_conditions_key():
    tree = {"combinator": "and", "conditions": [
        {"field": "a", "operator": "=", "value": 1},
    ]}
    assert evaluate(tree, {"a": 1}) is True


def test_evaluate_dict_with_rules_key_emits_deprecation():
    tree = {"combinator": "and", "rules": [
        {"field": "a", "operator": "=", "value": 1},
    ]}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert evaluate(tree, {"a": 1}) is True
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)


def test_evaluate_dict_with_both_keys_raises():
    tree = {"combinator": "and", "conditions": [], "rules": []}
    with pytest.raises(ValueError, match="ambiguous"):
        evaluate(tree, {})


def test_evaluate_contains_operator():
    assert evaluate(Leaf("title", "contains", "drug"), {"title": "drug leaflet info"}) is True
    assert evaluate(Leaf("title", "contains", "drug"), {"title": "formulary"}) is False


def test_evaluate_contains_missing_field():
    assert evaluate(Leaf("title", "contains", "drug"), {}) is False


def test_builder_to_evaluate_roundtrip():
    tag = field.multi_select(["drug", "formulary"], name="document_tag")
    station = field.select(["NICU", "ER"], name="document_station")

    condition = tag.is_in(["drug"]) & station.eq("NICU")
    assert evaluate(condition, {"document_tag": ["drug"], "document_station": "NICU"}) is True
    assert evaluate(condition, {"document_tag": ["drug"], "document_station": "ER"}) is False


def test_guard_first_missing_field_returns_false_for_all_operators():
    """Guard-first: missing/absent field → False for ALL operators, including != and is."""
    assert evaluate(Leaf("x", "=", 5), {}) is False
    assert evaluate(Leaf("x", "!=", 5), {}) is False
    assert evaluate(Leaf("x", "is", True), {}) is False
    assert evaluate(Leaf("x", "is", False), {}) is False
    assert evaluate(Leaf("x", ">", 5), {}) is False
    assert evaluate(Leaf("x", "<", 5), {}) is False
    assert evaluate(Leaf("x", "in", [1, 2]), {}) is False
    assert evaluate(Leaf("x", "not_in", [1, 2]), {}) is False
    assert evaluate(Leaf("x", "contains", "a"), {}) is False


def test_guard_first_none_field_returns_false_for_all_operators():
    """Guard-first: None value → False for ALL operators."""
    ctx = {"x": None}
    assert evaluate(Leaf("x", "=", 5), ctx) is False
    assert evaluate(Leaf("x", "!=", 5), ctx) is False
    assert evaluate(Leaf("x", "is", True), ctx) is False
    assert evaluate(Leaf("x", "is", False), ctx) is False
    assert evaluate(Leaf("x", ">", 5), ctx) is False
    assert evaluate(Leaf("x", "<", 5), ctx) is False
    assert evaluate(Leaf("x", "in", [1, 2]), ctx) is False
    assert evaluate(Leaf("x", "not_in", [1, 2]), ctx) is False
    assert evaluate(Leaf("x", "contains", "a"), ctx) is False


def test_matches_duck_typed_leaf():
    """matches() accepts any object with field/operator/value attributes."""

    @dataclass
    class CustomLeaf:
        field: str
        operator: str
        value: Any

    leaf = CustomLeaf("station", "=", "NICU")
    assert matches(leaf, {"station": "NICU"}) is True
    assert matches(leaf, {"station": "ER"}) is False


def test_matches_duck_typed_group():
    """matches() accepts any object with combinator/conditions attributes."""

    @dataclass
    class CustomLeaf:
        field: str
        operator: str
        value: Any

    @dataclass
    class CustomGroup:
        combinator: str
        conditions: tuple

    group = CustomGroup("and", (CustomLeaf("a", "=", 1), CustomLeaf("b", "=", 2)))
    assert matches(group, {"a": 1, "b": 2}) is True
    assert matches(group, {"a": 1, "b": 9}) is False


def test_matches_rejects_unknown_type():
    with pytest.raises(TypeError, match="expected a condition"):
        matches("not a condition", {})


def test_evaluate_is_deprecated_alias():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = evaluate(Leaf("x", "=", 1), {"x": 1})
        assert result is True
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
        assert any("matches" in str(warning.message) for warning in w)
