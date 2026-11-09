from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from hyperrules.refs import MISSING, has_ref, lookup, ref_path


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
    if "conditions" not in tree:
        raise ValueError("group node is missing a 'conditions' key")
    children = tree["conditions"]
    if not isinstance(children, list):
        raise TypeError(f"group children must be a list, got {type(children).__name__}")
    return children


def _absent(value: Any) -> bool:
    return value is MISSING or value is None


def _resolve(operator: str, value: Any, context: Mapping[str, Any]) -> Any:
    """``value`` with each reference read from ``context``, or ``MISSING`` when the leaf cannot hold.

    A reference to a missing or ``None`` value makes the leaf false, except
    inside an ``in`` list, where it is one value fewer: the other values still
    match. A reference to a list inside a list adds each of its values.
    """
    path = ref_path(value)
    if path is not None:
        resolved = lookup(context, path)
        return MISSING if _absent(resolved) else resolved
    if not isinstance(value, (list, tuple)) or not has_ref(value):
        return value
    values: list[Any] = []
    for item in value:
        path = ref_path(item)
        if path is None:
            values.append(item)
            continue
        resolved = lookup(context, path)
        if _absent(resolved):
            if operator != "in":
                return MISSING
        elif isinstance(resolved, (list, tuple, set)):
            values.extend(resolved)
        else:
            values.append(resolved)
    return values


def _eval_leaf(field: str, operator: str, value: Any, context: Mapping[str, Any]) -> bool:
    actual = lookup(context, field)
    if _absent(actual):
        return False
    value = _resolve(operator, value, context)
    if value is MISSING:
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

    A field or reference is a path (``user.district``). A leaf is False when
    its field, or a field its value refers to (``{"ref": "user.district"}``),
    is missing or ``None``; inside an ``in`` list such a reference is one value
    fewer. A ``not`` group inverts a leaf's result, as it inverts any leaf.

    Accepts raw dicts, or any object with leaf attributes (``.field``,
    ``.operator``, ``.value``) or group attributes (``.combinator``,
    ``.conditions``). This duck-typing contract means hyperrules does not
    need to import the typed classes from hypster or anywhere else.
    """
    if hasattr(tree, "field") and hasattr(tree, "operator") and hasattr(tree, "value"):
        return _eval_leaf(tree.field, tree.operator, tree.value, context)

    if hasattr(tree, "combinator") and hasattr(tree, "conditions"):
        return _eval_group(tree.combinator, list(tree.conditions), context)

    if isinstance(tree, Mapping):
        if "combinator" in tree:
            children = _get_children(tree)
            return _eval_group(tree["combinator"], children, context)
        if "field" not in tree:
            raise TypeError(f"dict condition must have 'combinator' or 'field' key, got keys: {set(tree)}")
        for required in ("operator", "value"):
            if required not in tree:
                raise TypeError(f"leaf condition dict is missing required key {required!r}")
        return _eval_leaf(tree["field"], tree["operator"], tree["value"], context)

    raise TypeError(f"expected a condition (Leaf, Group, or dict), got {type(tree).__name__}")
