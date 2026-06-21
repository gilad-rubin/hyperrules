"""Tests for evaluate() with structured Leaf/Group types and the 'conditions' key."""

import warnings

import pytest

from hyperrules import And, Group, Leaf, Not, Or, evaluate, field


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


def test_missing_field_is_falsy():
    assert evaluate(Leaf("x", "is", True), {}) is False
    assert evaluate(Leaf("x", "is", False), {}) is True
    assert evaluate(Leaf("x", ">", 5), {}) is False
    assert evaluate(Leaf("x", "<", 5), {}) is False
    assert evaluate(Leaf("x", "=", 5), {}) is False
