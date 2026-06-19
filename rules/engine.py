from __future__ import annotations

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


OPERATORS = {
    "=": _op_eq,
    "!=": _op_ne,
    "in": _op_in,
    "is": _op_is,
    ">": _op_gt,
    "<": _op_lt,
}


def evaluate(tree: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
    """True if ``context`` satisfies the condition ``tree`` (a parsed JSON node)."""
    if "combinator" in tree:  # group node
        children = tree.get("rules", [])
        combinator = tree["combinator"]
        if combinator == "and":
            return all(evaluate(child, context) for child in children)
        if combinator == "or":
            return any(evaluate(child, context) for child in children)
        if combinator == "not":  # negate the AND of children
            return not all(evaluate(child, context) for child in children)
        raise ValueError(f"unknown combinator: {combinator!r}")
    op = OPERATORS.get(tree["operator"])  # leaf node
    if op is None:
        raise ValueError(f"unknown operator: {tree['operator']!r}")
    return op(context.get(tree["field"]), tree["value"])
