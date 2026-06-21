import pytest

from hyperrules import Leaf, Group, Rule, And, Or, Not, field


def test_leaf_to_dict_roundtrip():
    leaf = Leaf("station", "=", "NICU")
    d = leaf.to_dict()
    assert d == {"field": "station", "operator": "=", "value": "NICU"}
    assert Leaf.from_dict(d) == leaf


def test_group_to_dict_roundtrip():
    group = And(Leaf("a", "=", 1), Leaf("b", ">", 2))
    d = group.to_dict()
    assert d["combinator"] == "and"
    assert len(d["conditions"]) == 2
    assert Group.from_dict(d) == group


def test_rule_to_dict_roundtrip():
    rule = Rule(when=Leaf("tag", "in", ["x"]), then="text", name="my_rule")
    d = rule.to_dict()
    assert d == {"when": {"field": "tag", "operator": "in", "value": ["x"]}, "then": "text", "name": "my_rule"}
    assert Rule.from_dict(d) == rule


def test_rule_name_omitted_from_dict_when_none():
    rule = Rule(when=Leaf("a", "=", 1), then="x")
    assert "name" not in rule.to_dict()


def test_and_combines_conditions():
    a = Leaf("x", "=", 1)
    b = Leaf("y", "=", 2)
    group = And(a, b)
    assert group.combinator == "and"
    assert group.conditions == (a, b)


def test_or_combines_conditions():
    a = Leaf("x", "=", 1)
    b = Leaf("y", "=", 2)
    group = Or(a, b)
    assert group.combinator == "or"
    assert group.conditions == (a, b)


def test_not_is_unary():
    a = Leaf("x", "=", 1)
    group = Not(a)
    assert group.combinator == "not"
    assert group.conditions == (a,)


def test_not_rejects_non_condition():
    with pytest.raises(TypeError):
        Not("not a condition")


def test_leaf_and_operator():
    a = Leaf("x", "=", 1)
    b = Leaf("y", "=", 2)
    result = a & b
    assert isinstance(result, Group)
    assert result.combinator == "and"


def test_leaf_or_operator():
    a = Leaf("x", "=", 1)
    b = Leaf("y", "=", 2)
    result = a | b
    assert isinstance(result, Group)
    assert result.combinator == "or"


def test_leaf_invert_operator():
    a = Leaf("x", "=", 1)
    result = ~a
    assert isinstance(result, Group)
    assert result.combinator == "not"
    assert result.conditions == (a,)


def test_group_and_operator():
    a = And(Leaf("x", "=", 1))
    b = Leaf("y", "=", 2)
    result = a & b
    assert result.combinator == "and"


def test_leaf_then_creates_rule():
    leaf = Leaf("tag", "in", ["drug"])
    rule = leaf.then("כאשר...")
    assert isinstance(rule, Rule)
    assert rule.when == leaf
    assert rule.then == "כאשר..."


def test_group_then_creates_rule():
    condition = And(Leaf("a", "=", 1), Leaf("b", "=", 2))
    rule = condition.then("payload")
    assert isinstance(rule, Rule)
    assert rule.when == condition


def test_combined_builder_expression():
    tag = field.multi_select(["drug", "formulary"], name="document_tag")
    station = field.select(["NICU", "ER"], name="document_station")
    has_diagram = field.bool(name="vision_page_presence")

    condition = tag.is_in(["drug"]) & (station.eq("NICU") | has_diagram.is_true())
    rule = condition.then("כאשר...")

    assert isinstance(rule, Rule)
    assert rule.when.combinator == "and"
    assert len(rule.when.conditions) == 2


def test_group_from_dict_reads_legacy_rules_key():
    data = {"combinator": "and", "rules": [{"field": "x", "operator": "=", "value": 1}]}
    group = Group.from_dict(data)
    assert len(group.conditions) == 1
    assert group.conditions[0] == Leaf("x", "=", 1)


def test_group_from_dict_missing_conditions_raises():
    with pytest.raises(ValueError, match="missing"):
        Group.from_dict({"combinator": "and"})


def test_frozen_types_are_hashable():
    leaf = Leaf("a", "=", 1)
    group = And(leaf)
    rule = Rule(when=leaf, then="x")
    assert hash(leaf)
    assert hash(group)
    assert hash(rule)
