"""Predicate→payload rule engine with typed conditions and a builder API.

Core types: ``Leaf`` (one comparison), ``Group`` (combined conditions),
``Rule`` (when + then). Use ``field.*`` constructors to declare queryable
properties and build conditions with ``.eq()``, ``.is_in()``, ``&``, ``|``,
``~``. A value may refer to another field of the context, such as the
requesting user's own (``district.eq(ref("user.district"))``). Evaluate at
runtime with ``matches(condition, context)``; check rules when they are saved
with ``validate(condition, fields=...)`` or ``validate_rules(rules, fields=...)``.
"""

from hyperrules.codecs import load_rule, save_rule
from hyperrules.engine import matches
from hyperrules.field_spec import DEFAULT_OPERATORS, FieldSpec
from hyperrules.refs import MISSING, lookup, ref, ref_path
from hyperrules.ruleset import RuleSet, load_dir
from hyperrules.schema import Field, Schema
from hyperrules.types import And, Group, Leaf, Not, Or, Rule
from hyperrules.validation import validate, validate_rules
from hyperrules import field

__all__ = [
    "matches",
    "validate",
    "validate_rules",
    "ref",
    "ref_path",
    "lookup",
    "MISSING",
    "Leaf",
    "Group",
    "Rule",
    "And",
    "Or",
    "Not",
    "FieldSpec",
    "field",
    "load_rule",
    "save_rule",
    "DEFAULT_OPERATORS",
    "RuleSet",
    "load_dir",
    "Field",
    "Schema",
]
