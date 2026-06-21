import pytest

from hyperrules import field, FieldSpec, Leaf


def test_select_creates_field_spec():
    spec = field.select(["NICU", "ER"], name="station")
    assert spec.type == "select"
    assert spec.name == "station"
    assert spec.options == ("NICU", "ER")
    assert "=" in spec.operators
    assert "!=" in spec.operators


def test_multi_select_creates_field_spec():
    spec = field.multi_select(["drug", "formulary"], name="document_tag")
    assert spec.type == "multi_select"
    assert "in" in spec.operators


def test_bool_creates_field_spec():
    spec = field.bool(name="has_diagram")
    assert spec.type == "bool"
    assert "is" in spec.operators


def test_multi_bool_creates_field_spec():
    spec = field.multi_bool(name="flags")
    assert spec.type == "multi_bool"
    assert "in" in spec.operators


def test_int_creates_field_spec():
    spec = field.int(name="page_count")
    assert spec.type == "int"
    assert set(spec.operators) == {">", "<", "=", "!="}


def test_multi_int_creates_field_spec():
    spec = field.multi_int(name="scores")
    assert spec.type == "multi_int"
    assert "in" in spec.operators
    assert "contains" in spec.operators


def test_float_creates_field_spec():
    spec = field.float(name="confidence")
    assert spec.type == "float"
    assert ">" in spec.operators


def test_multi_float_creates_field_spec():
    spec = field.multi_float(name="weights")
    assert spec.type == "multi_float"


def test_text_creates_field_spec():
    spec = field.text(name="author")
    assert spec.type == "text"
    assert "=" in spec.operators
    assert "contains" in spec.operators


def test_text_multiline_flag():
    spec = field.text(name="body", multiline=True)
    assert spec.multiline is True
    plain = field.text(name="title")
    assert plain.multiline is False


def test_multi_text_creates_field_spec():
    spec = field.multi_text(name="tags")
    assert spec.type == "multi_text"
    assert "in" in spec.operators


def test_name_optional_for_then_usage():
    spec = field.text(multiline=True)
    assert spec.name is None
    assert spec.type == "text"


def test_builder_requires_name():
    spec = field.text()
    with pytest.raises(ValueError, match="must have a name"):
        spec.eq("hello")


def test_eq_creates_leaf():
    spec = field.select(["NICU", "ER"], name="station")
    leaf = spec.eq("NICU")
    assert leaf == Leaf("station", "=", "NICU")


def test_neq_creates_leaf():
    leaf = field.select(["A", "B"], name="x").neq("A")
    assert leaf == Leaf("x", "!=", "A")


def test_is_in_creates_leaf():
    leaf = field.multi_select(["a", "b", "c"], name="tags").is_in(["a", "b"])
    assert leaf == Leaf("tags", "in", ["a", "b"])


def test_is_true_creates_leaf():
    leaf = field.bool(name="active").is_true()
    assert leaf == Leaf("active", "is", True)


def test_is_false_creates_leaf():
    leaf = field.bool(name="active").is_false()
    assert leaf == Leaf("active", "is", False)


def test_gt_creates_leaf():
    leaf = field.int(name="count").gt(5)
    assert leaf == Leaf("count", ">", 5)


def test_lt_creates_leaf():
    leaf = field.float(name="score").lt(0.5)
    assert leaf == Leaf("score", "<", 0.5)


def test_contains_creates_leaf():
    leaf = field.text(name="title").contains("drug")
    assert leaf == Leaf("title", "contains", "drug")


def test_to_dict():
    spec = field.multi_select(["a", "b"], name="tags", description="Document tags")
    d = spec.to_dict()
    assert d["type"] == "multi_select"
    assert d["name"] == "tags"
    assert d["description"] == "Document tags"
    assert d["options"] == ["a", "b"]
    assert d["operators"] == ["in", "not_in"]


def test_to_dict_omits_none_fields():
    spec = field.bool(name="active")
    d = spec.to_dict()
    assert "description" not in d
    assert "options" not in d
    assert "multiline" not in d


def test_description_carried():
    spec = field.bool(name="diag", description="Has diagram page")
    assert spec.description == "Has diagram page"
