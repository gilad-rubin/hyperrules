"""References: rules that name any declared field and the requesting user's context, checked when saved.

`district = user.district` matches by the requester's own district, a missing value never satisfies a leaf, and an
unknown field, reference or operator, or a value of the wrong type, refuses the rule set by name instead of dropping
the condition. Ported from Panda's tests, where these were first built (Panda's ticket 0069).
"""

from __future__ import annotations

import pytest
from hyperrules import Leaf, Not, field, matches, ref, validate, validate_rules
from hyperrules.codecs import condition_to_simple_dict, load_rule, save_rule
from hyperrules.types import Rule

DISTRICTS = ["North", "South", "ארצי"]
SOURCES = ["procedures", "services", "labs"]

district = field.select(DISTRICTS, name="district")
source = field.select(SOURCES, name="source")
pages = field.int(name="pages")
wards = field.multi_select(["NICU", "Hem/Onc"], name="wards")
user_district = field.select(DISTRICTS, name="user.district")
user_ward = field.select(["NICU", "Hem/Onc"], name="user.ward")
user_wards = field.multi_select(["NICU", "Hem/Onc"], name="user.wards")
FIELDS = [district, source, pages, wards, user_district, user_ward, user_wards]

OWN_DISTRICT = {"field": "district", "operator": "=", "value": {"ref": "user.district"}}


def doc(**fields):
    return {
        "district": "North",
        "source": "procedures",
        "pages": 3,
        "wards": ["NICU"],
        **fields,
    }


# --- the user's own context -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("context", "expected"),
    [
        ({**doc(), "user": {"district": "North"}}, True),
        ({**doc(), "user": {"district": "South"}}, False),
        ({**doc(), "user.district": "North"}, True),  # a flat dotted key reads the same
        ({**doc(), "user": {"district": None}}, False),  # a user with no district
        ({**doc(), "user": {}}, False),
        (doc(), False),
        (
            {**doc(district=None), "user": {"district": "North"}},
            False,
        ),  # a document with no district
    ],
)
def test_a_rule_on_the_users_own_district_matches_by_the_requesters_context(
    context, expected
):
    assert matches(OWN_DISTRICT, context) is expected


def test_a_missing_reference_never_satisfies_a_leaf_and_not_inverts_it_as_any_leaf():
    no_district = {**doc(), "user": {}}
    assert matches(OWN_DISTRICT, no_district) is False
    assert (
        matches(
            {"field": "district", "operator": "!=", "value": ref("user.district")},
            no_district,
        )
        is False
    )
    assert matches(Not(Leaf(**OWN_DISTRICT)), no_district) is True


def test_a_typed_field_spec_given_as_a_value_is_a_reference_to_it():
    assert district.eq(user_district) == Leaf("district", "=", {"ref": "user.district"})
    assert wards.contains(user_ward) == Leaf("wards", "contains", {"ref": "user.ward"})
    assert district.is_in(user_wards).value == {"ref": "user.wards"}
    rule = (district.eq(user_district) | district.eq("ארצי")).then("include")
    assert matches(rule.when, {**doc(district="ארצי"), "user": {"district": "South"}})
    assert matches(rule.when, {**doc(district="North"), "user": {"district": "North"}})
    assert not matches(
        rule.when, {**doc(district="North"), "user": {"district": "South"}}
    )


# --- any declared field ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("condition", "context", "expected"),
    [
        (source.eq("labs"), doc(source="labs"), True),
        (source.neq("labs"), doc(source="labs"), False),
        (pages.gt(2), doc(pages=3), True),
        (pages.lt(2), doc(pages=3), False),
        (wards.is_in(["Hem/Onc"]), doc(wards=["NICU", "Hem/Onc"]), True),
        (wards.is_in(["Hem/Onc"]), doc(wards=["NICU"]), False),
        (
            wards.is_in(user_wards),
            {**doc(wards=["Hem/Onc"]), "user": {"wards": ["NICU", "Hem/Onc"]}},
            True,
        ),
        (
            wards.is_in(user_wards),
            {**doc(wards=["Hem/Onc"]), "user": {"wards": ["NICU"]}},
            False,
        ),
        (
            source.neq("labs") & district.eq(user_district),
            {**doc(), "user": {"district": "North"}},
            True,
        ),
    ],
)
def test_a_rule_on_any_declared_field_works(condition, context, expected):
    assert validate(condition, fields=FIELDS) == []
    assert matches(condition, context) is expected


# --- refused when saved, by name ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("condition", "problem"),
    [
        (
            {"field": "distrct", "operator": "=", "value": "North"},
            "when: unknown field 'distrct'",
        ),
        (
            {"field": "district", "operator": "=", "value": {"ref": "user.distrct"}},
            "when: 'district' refers to an unknown field 'user.distrct'",
        ),
        (
            {"field": "district", "operator": "~", "value": "North"},
            "when: unknown operator '~'",
        ),
        (
            {"field": "district", "operator": ">", "value": "North"},
            "when: operator '>' does not apply to 'district' (select); use =, !=, in, not_in",
        ),
        (
            {"field": "pages", "operator": ">", "value": "3"},
            "when: 'pages' (int) cannot take '3'",
        ),
        (
            {"field": "district", "operator": "=", "value": "East"},
            "when: 'East' is not one of 'district''s options (North, South, ארצי)",
        ),
        (
            {"field": "district", "operator": "in", "value": ["North", "East"]},
            "when: 'East' is not one of 'district''s options (North, South, ארצי)",
        ),
        (
            {"field": "pages", "operator": "=", "value": {"ref": "user.district"}},
            "when: 'pages' (int) cannot be compared with 'user.district' (select)",
        ),
        (
            {"field": "district", "operator": "=", "value": {"ref": "user.wards"}},
            "when: 'district' (select) cannot be compared with 'user.wards' (multi_select)",
        ),
    ],
)
def test_a_rule_naming_an_unknown_field_operator_or_a_mismatched_type_is_refused_by_name(
    condition, problem
):
    assert validate(condition, fields=FIELDS) == [problem]


def test_every_problem_in_a_rule_set_is_named_by_its_place_and_none_is_dropped():
    rules = [
        Rule(when=district.eq(user_district), then="include"),
        {
            "when": {
                "combinator": "or",
                "conditions": [
                    {"field": "sorce", "operator": "=", "value": "labs"},
                    {
                        "field": "district",
                        "operator": "=",
                        "value": {"ref": "user.wards"},
                    },
                ],
            },
            "then": "include",
        },
        {"then": "include"},
    ]
    assert validate_rules(rules, fields=FIELDS) == [
        "rules[1].when.conditions[0]: unknown field 'sorce'",
        "rules[1].when.conditions[1]: 'district' (select) cannot be compared with 'user.wards' (multi_select)",
        "rules[2]: has no 'when'",
    ]


def test_without_a_vocabulary_only_the_shape_is_checked_as_before():
    assert validate({"field": "anything", "operator": "=", "value": 1}) == []
    assert validate({"field": "anything", "operator": "~", "value": 1}) == [
        "when: unknown operator '~'"
    ]
    assert validate({"combinator": "xor", "conditions": []}) == [
        "when: unknown combinator 'xor'"
    ]


# --- codecs keep a reference whole ----------------------------------------------------------------


def test_a_reference_never_collapses_into_the_in_shorthand(tmp_path):
    leaf = Leaf("district", "in", ref("user.districts"))
    assert condition_to_simple_dict(leaf) is None
    path = tmp_path / "own.md"
    save_rule(Rule(when=leaf, then="show", name="own"), path)
    assert load_rule(path).when == leaf


# --- the two gaps Panda's copy left: lookup exported, a reference inside a list of values -----------


def test_lookup_is_exported_with_its_missing_marker():
    import hyperrules

    assert {"lookup", "MISSING"} <= set(hyperrules.__all__)
    context = {"user.district": "North", "user": {"ward": "NICU"}}
    assert hyperrules.lookup(context, "user.district") == "North"
    assert hyperrules.lookup(context, "user.ward") == "NICU"
    assert hyperrules.lookup(context, "user.station") is hyperrules.MISSING


NATIONAL_OR_OWN = {"field": "district", "operator": "in", "value": ["ארצי", {"ref": "user.district"}]}


@pytest.mark.parametrize(
    ("context", "expected"),
    [
        ({**doc(district="North"), "user": {"district": "North"}}, True),  # the user's own district
        ({**doc(district="ארצי"), "user": {"district": "North"}}, True),  # the national one
        ({**doc(district="South"), "user": {"district": "North"}}, False),
        ({**doc(district="ארצי"), "user": {}}, True),  # no district of their own: only the national one
        ({**doc(district="North"), "user": {}}, False),
        ({**doc(district="North"), "user": {"district": None}}, False),
    ],
)
def test_a_reference_inside_a_list_of_values_is_read_from_the_context(context, expected):
    assert matches(NATIONAL_OR_OWN, context) is expected


def test_a_reference_to_a_list_inside_a_list_adds_each_of_its_values():
    rule = {"field": "wards", "operator": "in", "value": ["Labs", {"ref": "user.wards"}]}
    assert matches(rule, {**doc(wards=["Hem/Onc"]), "user": {"wards": ["NICU", "Hem/Onc"]}})
    assert not matches(rule, {**doc(wards=["Hem/Onc"]), "user": {"wards": ["NICU"]}})
    assert matches(rule, {**doc(wards=["Labs"]), "user": {}})


def test_not_in_a_list_holding_a_missing_reference_never_holds():
    rule = {"field": "district", "operator": "not_in", "value": ["South", {"ref": "user.district"}]}
    assert matches(rule, {**doc(district="North"), "user": {"district": "ארצי"}})
    assert not matches(rule, {**doc(district="North"), "user": {"district": "North"}})
    assert not matches(rule, {**doc(district="North"), "user": {}})  # unknown: the user's district might be North


def test_a_field_spec_inside_a_list_of_values_is_a_reference_to_it():
    assert district.is_in(["ארצי", user_district]).to_dict() == NATIONAL_OR_OWN
    assert district.not_in(["ארצי", user_district]).value == ["ארצי", {"ref": "user.district"}]


@pytest.mark.parametrize(
    ("condition", "problems"),
    [
        (NATIONAL_OR_OWN, []),
        (wards.is_in(["NICU", user_wards]), []),
        (
            {"field": "district", "operator": "in", "value": ["ארצי", {"ref": "user.distrct"}]},
            ["when: 'district' refers to an unknown field 'user.distrct'"],
        ),
        (
            {"field": "district", "operator": "in", "value": ["Nowhere", {"ref": "user.ward"}]},
            [
                "when: 'Nowhere' is not one of 'district''s options (North, South, ארצי)",
            ],
        ),
        (
            {"field": "pages", "operator": "=", "value": {"ref": "user.district"}},
            ["when: 'pages' (int) cannot be compared with 'user.district' (select)"],
        ),
        (
            {"field": "district", "operator": "in", "value": [{"ref": "user.ward"}, {"ref": "pages"}]},
            ["when: 'district' (select) cannot be compared with 'pages' (int)"],
        ),
    ],
)
def test_each_reference_inside_a_list_is_checked_like_one_alone(condition, problems):
    assert validate(condition, fields=FIELDS) == problems


def test_a_list_holding_a_reference_never_collapses_into_the_in_shorthand(tmp_path):
    leaf = Leaf("district", "in", ["ארצי", ref("user.district")])
    assert condition_to_simple_dict(leaf) is None
    path = tmp_path / "national-or-own.md"
    save_rule(Rule(when=leaf, then="show", name="national-or-own"), path)
    assert load_rule(path).when == leaf
