from __future__ import annotations

import warnings
from collections.abc import Mapping
from typing import Any

_MISSING = object()


def _op_eq(actual: Any, value: Any) -> bool:
    return actual == value


def _op_ne(actual: Any, value: Any) -> bool:
    return actual != value


def _op_in(actual: Any, value: Any) -> bool:
    allowed = value if isinstance(value, (list, tuple, set)) else [value]
    if isinstance(actual, (list, tuple, set)):
        return bool(set(actual) & set(allowed))
    return actual in allowed


def _op_is(actual: Any, value: Any) -> bool:
    return bool(actual) is bool(value)


def _op_gt(actual: Any, value: Any) -> bool:
    return actual > value


def _op_lt(actual: Any, value: Any) -> bool:
    return actual < value


def _op_not_in(actual: Any, value: Any) -> bool:
    return not _op_in(actual, value)


def _op_contains(actual: Any, value: Any) -> bool:
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


def _eval_leaf(field: str, operator: str, value: Any, context: Mapping[str, Any]) -> bool:
    actual = context.get(field, _MISSING)
    if actual is _MISSING or actual is None:
        return False
    op = OPERATORS.get(operator)
    if op is None:
        raise ValueError(f"unknown operator: {operator!r}")
    return op(actual, value)


def _eval_group(combinator: str, children: Any, context: Mapping[str, Any]) -> bool:
    if combinator == "and":
        return all(matches(child, context) for child in children)
    if combinator == "or":
        return any(matches(child, context) for child in children)
    if combinator == "not":
        if len(children) != 1:
            raise ValueError(f"NOT group must have exactly one child, got {len(children)}")
        return not matches(children[0], context)
    raise ValueError(f"unknown combinator: {combinator!r}")


def matches(tree: Mapping[str, Any] | Any, context: Mapping[str, Any]) -> bool:
    """True if ``context`` satisfies the condition ``tree``.

    Accepts raw dicts, or any object with leaf attributes (``.field``,
    ``.operator``, ``.value``) or group attributes (``.combinator``,
    ``.conditions``). This duck-typing contract means hyperrules does not
    need to import the typed classes from hypster or anywhere else.
    """
    if hasattr(tree, "field") and hasattr(tree, "operator"):
        return _eval_leaf(tree.field, tree.operator, tree.value, context)

    if hasattr(tree, "combinator") and hasattr(tree, "conditions"):
        return _eval_group(tree.combinator, tree.conditions, context)

    if isinstance(tree, Mapping):
        if "combinator" in tree:
            children = _get_children(tree)
            return _eval_group(tree["combinator"], children, context)
        return _eval_leaf(tree["field"], tree["operator"], tree["value"], context)

    raise TypeError(f"expected a condition (Leaf, Group, or dict), got {type(tree).__name__}")


def evaluate(tree: Mapping[str, Any] | Any, context: Mapping[str, Any]) -> bool:
    """Deprecated alias for :func:`matches`."""
    warnings.warn(
        "evaluate() is deprecated, use matches() instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return matches(tree, context)
