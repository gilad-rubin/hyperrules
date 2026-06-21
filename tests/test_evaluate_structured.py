"""Tests for matches() with structured Leaf/Group types and the 'conditions' key."""

from dataclasses import dataclass
from typing import Any

import pytest

from hyperrules import And, Group, Leaf, Not, Or, field, matches


def test_matches_leaf():
    leaf = Leaf("station", "=", "NICU")
    assert matches(leaf, {"station": "NICU"}) is True
    assert matches(leaf, {"station": "ER"}) is False


def test_matches_and_group():
    group = And(Leaf("a", "=", 1), Leaf("b", "=", 2))
    assert matches(group, {"a": 1, "b": 2}) is True
    assert matches(group, {"a": 1, "b": 9}) is False


def test_matches_or_group():
    group = Or(Leaf("a", "=", 1), Leaf("b", "=", 2))
    assert matches(group, {"a": 1, "b": 9}) is True
    assert matches(group, {"a": 9, "b": 9}) is False


def test_matches_not_group():
    group = Not(Leaf("a", "=", 1))
    assert matches(group, {"a": 2}) is True
    assert matches(group, {"a": 1}) is False


def test_matches_nested_structured():
    condition = And(
        Leaf("document_tag", "in", ["drug_leaflet"]),
        Or(Leaf("document_station", "=", "NICU"), Leaf("vision_page_presence", "is", True)),
    )
    assert matches(condition, {"document_tag": ["drug_leaflet"], "document_station": "NICU"}) is True
    assert matches(condition, {"document_tag": ["drug_leaflet"], "document_station": "ER", "vision_page_presence": True}) is True
    assert matches(condition, {"document_tag": ["drug_leaflet"], "document_station": "ER", "vision_page_presence": False}) is False


def test_matches_dict_with_conditions_key():
    tree = {"combinator": "and", "conditions": [
        {"field": "a", "operator": "=", "value": 1},
    ]}
    assert matches(tree, {"a": 1}) is True


def test_matches_dict_missing_conditions_key_raises():
    with pytest.raises(ValueError, match="missing"):
        matches({"combinator": "and"}, {})


def test_matches_dict_missing_field_key_raises():
    tree = {"combinator_typo": "and", "conditions": []}
    with pytest.raises(TypeError, match="'combinator' or 'field'"):
        matches(tree, {})


def test_matches_contains_operator():
    assert matches(Leaf("title", "contains", "drug"), {"title": "drug leaflet info"}) is True
    assert matches(Leaf("title", "contains", "drug"), {"title": "formulary"}) is False


def test_matches_contains_missing_field():
    assert matches(Leaf("title", "contains", "drug"), {}) is False


def test_builder_to_matches_roundtrip():
    tag = field.multi_select(["drug", "formulary"], name="document_tag")
    station = field.select(["NICU", "ER"], name="document_station")

    condition = tag.is_in(["drug"]) & station.eq("NICU")
    assert matches(condition, {"document_tag": ["drug"], "document_station": "NICU"}) is True
    assert matches(condition, {"document_tag": ["drug"], "document_station": "ER"}) is False


def test_guard_first_missing_field_returns_false_for_all_operators():
    """Guard-first: missing/absent field -> False for ALL operators, including != and is."""
    assert matches(Leaf("x", "=", 5), {}) is False
    assert matches(Leaf("x", "!=", 5), {}) is False
    assert matches(Leaf("x", "is", True), {}) is False
    assert matches(Leaf("x", "is", False), {}) is False
    assert matches(Leaf("x", ">", 5), {}) is False
    assert matches(Leaf("x", "<", 5), {}) is False
    assert matches(Leaf("x", "in", [1, 2]), {}) is False
    assert matches(Leaf("x", "not_in", [1, 2]), {}) is False
    assert matches(Leaf("x", "contains", "a"), {}) is False


def test_guard_first_none_field_returns_false_for_all_operators():
    """Guard-first: None value -> False for ALL operators."""
    ctx = {"x": None}
    assert matches(Leaf("x", "=", 5), ctx) is False
    assert matches(Leaf("x", "!=", 5), ctx) is False
    assert matches(Leaf("x", "is", True), ctx) is False
    assert matches(Leaf("x", "is", False), ctx) is False
    assert matches(Leaf("x", ">", 5), ctx) is False
    assert matches(Leaf("x", "<", 5), ctx) is False
    assert matches(Leaf("x", "in", [1, 2]), ctx) is False
    assert matches(Leaf("x", "not_in", [1, 2]), ctx) is False
    assert matches(Leaf("x", "contains", "a"), ctx) is False


@dataclass
class CustomLeaf:
    field: str
    operator: str
    value: Any


@dataclass
class CustomGroup:
    combinator: str
    conditions: tuple


def test_matches_duck_typed_leaf():
    """matches() accepts any object with field/operator/value attributes."""
    leaf = CustomLeaf("station", "=", "NICU")
    assert matches(leaf, {"station": "NICU"}) is True
    assert matches(leaf, {"station": "ER"}) is False


def test_matches_duck_typed_group():
    """matches() accepts any object with combinator/conditions attributes."""
    group = CustomGroup("and", (CustomLeaf("a", "=", 1), CustomLeaf("b", "=", 2)))
    assert matches(group, {"a": 1, "b": 2}) is True
    assert matches(group, {"a": 1, "b": 9}) is False


def test_matches_rejects_unknown_type():
    with pytest.raises(TypeError, match="expected a condition"):
        matches("not a condition", {})


