"""Tiny zero-dependency predicate->payload rule engine.

A rule is a plain dict with a ``when`` key holding a nestable boolean condition
tree (leaf = ``field``/``operator``/``value``; group = ``combinator`` of
``and``/``or``/``not`` over child nodes), plus opaque payload keys the engine
never inspects. See ``evaluate``.
"""

from rules.engine import evaluate
from rules.ruleset import RuleSet, load_dir
from rules.schema import DEFAULT_OPERATORS, Field, Schema
from rules.validation import validate

__all__ = ["evaluate", "load_dir", "validate", "RuleSet", "Field", "Schema", "DEFAULT_OPERATORS"]
