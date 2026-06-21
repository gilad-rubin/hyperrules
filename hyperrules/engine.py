from __future__ import annotations

import warnings
from collections.abc import Mapping
from typing import Any


def _op_eq(actual: Any, value: Any) -> bool:
    return actual == value


def _op_ne(actual: Any, value: Any) -> bool:
    return actual != value


def _op_in(actual: Any, value: Any) -> bool:
    # ``value`` is the allowed set. When the context field is itself a collection
    # (e.g. document_tag: list[str]), "in" means the sets intersect.
    allowed = value if isinstance(value, (list, tuple, set)) else [value]
    if isinstance(actual, (list, tuple, set)):
        return bool(set(actual) & set(allowed))
    return actual in allowed


def _op_is(actual: Any, value: Any) -> bool:
    return bool(actual) is bool(value)


def _op_gt(actual: Any, value: Any) -> bool:
    return actual is not None and actual > value


def _op_lt(actual: Any, value: Any) -> bool:
    return actual is not None and actual < value


def _op_not_in(actual: Any, value: Any) -> bool:
    if actual is None:
        return False
    return not _op_in(actual, value)


def _op_contains(actual: Any, value: Any) -> bool:
    if actual is None:
        return False
    return value in actual


OPERATORS = {
    "=": _op_eq,
    "!=": _op_ne,
    "in": _op_in,
    "not_in": _op_not_in,
    "is": _op_is,
    ">": _op_gt,
    "<": _op_lt,
    "contains": _op_contains,
}


def _get_children(tree: Mapping[str, Any]) -> list:
    has_conditions = "conditions" in tree
    has_rules = "rules" in tree
    if has_conditions and has_rules:
        raise ValueError("group node has both 'conditions' and 'rules' keys — ambiguous")
    if has_conditions:
        children = tree["conditions"]
    elif has_rules:
        warnings.warn(
            "The 'rules' key for group children is deprecated — use 'conditions' instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        children = tree["rules"]
    else:
        raise ValueError("group node is missing a 'conditions' key")
    if not isinstance(children, list):
        raise TypeError(f"group children must be a list, got {type(children).__name__}")
    return children


def evaluate(tree: Mapping[str, Any] | Any, context: Mapping[str, Any]) -> bool:
    """True if ``context`` satisfies the condition ``tree``.

    Accepts raw dicts (parsed JSON) or structured ``Leaf``/``Group`` types.
    """
    from hyperrules.types import Group, Leaf

    if isinstance(tree, Leaf):
        op = OPERATORS.get(tree.operator)
        if op is None:
            raise ValueError(f"unknown operator: {tree.operator!r}")
        return op(context.get(tree.field), tree.value)

    if isinstance(tree, Group):
        if tree.combinator == "and":
            return all(evaluate(child, context) for child in tree.conditions)
        if tree.combinator == "or":
            return any(evaluate(child, context) for child in tree.conditions)
        if tree.combinator == "not":
            if len(tree.conditions) != 1:
                raise ValueError(f"NOT group must have exactly one child, got {len(tree.conditions)}")
            return not evaluate(tree.conditions[0], context)
        raise ValueError(f"unknown combinator: {tree.combinator!r}")

    if "combinator" in tree:
        children = _get_children(tree)
        combinator = tree["combinator"]
        if combinator == "and":
            return all(evaluate(child, context) for child in children)
        if combinator == "or":
            return any(evaluate(child, context) for child in children)
        if combinator == "not":
            if len(children) != 1:
                raise ValueError(f"NOT group must have exactly one child, got {len(children)}")
            return not evaluate(children[0], context)
        raise ValueError(f"unknown combinator: {combinator!r}")

    op = OPERATORS.get(tree["operator"])
    if op is None:
        raise ValueError(f"unknown operator: {tree['operator']!r}")
    return op(context.get(tree["field"]), tree["value"])
