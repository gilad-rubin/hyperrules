"""Predicate→payload rule engine with typed conditions and a builder API.

Core types: ``Leaf`` (one comparison), ``Group`` (combined conditions),
``Rule`` (when + then). Use ``field.*`` constructors to declare queryable
properties and build conditions with ``.eq()``, ``.is_in()``, ``&``, ``|``,
``~``. Evaluate at runtime with ``matches(condition, context)``.
"""

from hyperrules.codecs import load_rule, save_rule
from hyperrules.engine import evaluate, matches
from hyperrules.field_spec import DEFAULT_OPERATORS, FieldSpec
from hyperrules.ruleset import RuleSet, load_dir
from hyperrules.schema import Field, Schema
from hyperrules.types import And, Group, Leaf, Not, Or, Rule
from hyperrules.validation import validate
from hyperrules import field

__all__ = [
    "matches",
    "evaluate",
    "validate",
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
    # kept for backward compat
    "RuleSet",
    "load_dir",
    "Field",
    "Schema",
]
