import pytest

from hyperrules import evaluate


def test_leaf_equality_matches_context():
    tree = {"field": "station", "operator": "=", "value": "NICU"}
    assert evaluate(tree, {"station": "NICU"}) is True
    assert evaluate(tree, {"station": "ER"}) is False


def test_leaf_in_membership_scalar_context():
    tree = {"field": "station", "operator": "in", "value": ["NICU", "ER"]}
    assert evaluate(tree, {"station": "NICU"}) is True
    assert evaluate(tree, {"station": "PICU"}) is False


def test_leaf_in_membership_list_context_is_set_intersection():
    # document_tag is a list in the context; "in" means the sets intersect.
    tree = {"field": "document_tag", "operator": "in", "value": ["drug_leaflet", "formulary"]}
    assert evaluate(tree, {"document_tag": ["drug_leaflet"]}) is True
    assert evaluate(tree, {"document_tag": ["other"]}) is False


def test_leaf_is_boolean_coerces_truthiness():
    tree = {"field": "vision_page_presence", "operator": "is", "value": True}
    assert evaluate(tree, {"vision_page_presence": True}) is True
    assert evaluate(tree, {"vision_page_presence": False}) is False
    assert evaluate(tree, {}) is False  # missing field is falsey


def test_and_group_requires_all_children():
    tree = {"combinator": "and", "rules": [
        {"field": "document_tag", "operator": "in", "value": ["drug_leaflet"]},
        {"field": "document_station", "operator": "=", "value": "NICU"},
    ]}
    assert evaluate(tree, {"document_tag": ["drug_leaflet"], "document_station": "NICU"}) is True
    assert evaluate(tree, {"document_tag": ["drug_leaflet"], "document_station": "ER"}) is False


def test_or_group_requires_any_child():
    tree = {"combinator": "or", "rules": [
        {"field": "document_station", "operator": "=", "value": "NICU"},
        {"field": "vision_page_presence", "operator": "is", "value": True},
    ]}
    assert evaluate(tree, {"document_station": "ER", "vision_page_presence": True}) is True
    assert evaluate(tree, {"document_station": "ER", "vision_page_presence": False}) is False


def test_not_group_negates_children():
    tree = {"combinator": "not", "rules": [
        {"field": "document_station", "operator": "=", "value": "NICU"},
    ]}
    assert evaluate(tree, {"document_station": "ER"}) is True
    assert evaluate(tree, {"document_station": "NICU"}) is False


def test_nested_groups_compose_the_real_drug_leaflet_shape():
    # tag in [drug_leaflet, formulary] AND (station = NICU OR has-diagram)
    tree = {"combinator": "and", "rules": [
        {"field": "document_tag", "operator": "in", "value": ["drug_leaflet", "formulary"]},
        {"combinator": "or", "rules": [
            {"field": "document_station", "operator": "=", "value": "NICU"},
            {"field": "vision_page_presence", "operator": "is", "value": True},
        ]},
    ]}
    nicu = {"document_tag": ["drug_leaflet"], "document_station": "NICU", "vision_page_presence": False}
    diagram = {"document_tag": ["drug_leaflet"], "document_station": "ER", "vision_page_presence": True}
    neither = {"document_tag": ["drug_leaflet"], "document_station": "ER", "vision_page_presence": False}
    wrong_tag = {"document_tag": ["other"], "document_station": "NICU", "vision_page_presence": True}
    assert evaluate(tree, nicu) is True
    assert evaluate(tree, diagram) is True
    assert evaluate(tree, neither) is False
    assert evaluate(tree, wrong_tag) is False


def test_empty_group_is_true():
    assert evaluate({"combinator": "and", "rules": []}, {}) is True


def test_comparison_operators_and_none_safety():
    assert evaluate({"field": "n", "operator": "!=", "value": 5}, {"n": 4}) is True
    assert evaluate({"field": "n", "operator": "!=", "value": 5}, {"n": 5}) is False
    assert evaluate({"field": "n", "operator": ">", "value": 10}, {"n": 11}) is True
    assert evaluate({"field": "n", "operator": "<", "value": 10}, {"n": 9}) is True
    assert evaluate({"field": "n", "operator": ">", "value": 10}, {}) is False  # missing → False, not a crash


def test_unknown_operator_raises_value_error():
    with pytest.raises(ValueError):
        evaluate({"field": "x", "operator": "wat", "value": 1}, {"x": 1})
