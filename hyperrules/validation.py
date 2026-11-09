"""Save-time checks: every problem with a condition tree, each named by its path.

Never call these on the evaluation hot path. Given the field vocabulary the
rules may name (``fields``), a check also refuses an unknown field or
reference, an operator the field's type does not offer, and a value or
reference of the wrong type: a rule is refused whole, never run with a
condition dropped.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

from hyperrules.engine import OPERATORS
from hyperrules.field_spec import DEFAULT_OPERATORS
from hyperrules.refs import ref_path

COMBINATORS = {"and", "or", "not"}

# A field type's kind of value, and whether the field holds a list of them.
_KINDS: dict[str, tuple[str, bool]] = {
    "select": ("text", False),
    "text": ("text", False),
    "bool": ("bool", False),
    "int": ("number", False),
    "float": ("number", False),
    "multi_select": ("text", True),
    "multi_text": ("text", True),
    "multi_bool": ("bool", True),
    "multi_int": ("number", True),
    "multi_float": ("number", True),
}


def validate(tree: Any, *, fields: Iterable[Any] | None = None, path: str = "when") -> list[str]:
    """Every problem with the condition ``tree`` (empty = valid).

    ``tree`` is a ``Leaf``/``Group`` (hyperrules' or hypster's: any object with
    their attributes) or its dict form. ``fields`` declares what a rule may
    name: field specs (``hyperrules.field``/``hypster.field``) or their
    ``to_dict()`` form, each with ``name``, ``type``, and optional ``options``
    and ``operators``; dotted names (``user.district``) declare the context
    a reference reads. Without ``fields`` only the tree's shape is checked.
    """
    return _validate(tree, None if fields is None else _vocabulary(fields), path)


def validate_rules(rules: Iterable[Any], *, fields: Iterable[Any] | None = None) -> list[str]:
    """Every problem with each rule's ``when`` (a ``Rule`` or its dict form), by its place in ``rules``."""
    vocabulary = None if fields is None else _vocabulary(fields)
    problems: list[str] = []
    for index, rule in enumerate(rules):
        when = rule.get("when") if isinstance(rule, Mapping) else getattr(rule, "when", None)
        if when is None:
            problems.append(f"rules[{index}]: has no 'when'")
            continue
        problems.extend(_validate(when, vocabulary, f"rules[{index}].when"))
    return problems


def _vocabulary(fields: Iterable[Any]) -> dict[str, dict[str, Any]]:
    vocabulary = {}
    for spec in fields:
        data = spec if isinstance(spec, Mapping) else spec.to_dict()
        vocabulary[data["name"]] = dict(data)
    return vocabulary


def _node(tree: Any) -> tuple[str, Any, Any, Any] | None:
    """``("leaf", field, operator, value)`` or ``("group", combinator, children, None)``; None when neither."""
    if all(hasattr(tree, name) for name in ("field", "operator", "value")):
        return "leaf", tree.field, tree.operator, tree.value
    if hasattr(tree, "combinator") and hasattr(tree, "conditions"):
        return "group", tree.combinator, list(tree.conditions), None
    return None


def _validate(tree: Any, vocabulary: dict[str, dict[str, Any]] | None, path: str) -> list[str]:
    node = _node(tree)
    if node is None and isinstance(tree, Mapping):
        if "combinator" in tree:
            node = "group", tree["combinator"], tree.get("conditions"), None
        else:
            missing = [key for key in ("field", "operator", "value") if key not in tree]
            if missing:
                return [f"{path}: leaf is missing {key!r}" for key in missing]
            node = "leaf", tree["field"], tree["operator"], tree["value"]
    if node is None:
        return [f"{path}: expected a condition, got {type(tree).__name__}"]

    kind, first, second, value = node
    if kind == "group":
        errors = []
        if first not in COMBINATORS:
            errors.append(f"{path}: unknown combinator {first!r}")
        if not isinstance(second, list):
            return [*errors, f"{path}: group is missing a 'conditions' list"]
        if first == "not" and len(second) != 1:
            errors.append(f"{path}: NOT group must have exactly one child, got {len(second)}")
        for index, child in enumerate(second):
            errors.extend(_validate(child, vocabulary, f"{path}.conditions[{index}]"))
        return errors

    if second not in OPERATORS:
        return [f"{path}: unknown operator {second!r}"]
    return [] if vocabulary is None else _check_leaf(first, second, value, vocabulary, path)


def _check_leaf(field: Any, operator: str, value: Any, vocabulary: dict[str, dict[str, Any]], path: str) -> list[str]:
    spec = vocabulary.get(field) if isinstance(field, str) else None
    if spec is None:
        return [f"{path}: unknown field {field!r}"]
    if spec.get("type") not in _KINDS:
        return [f"{path}: field {field!r} declares an unknown type {spec.get('type')!r}"]
    offered = list(spec.get("operators") or DEFAULT_OPERATORS[spec["type"]])
    if operator not in offered:
        return [f"{path}: operator {operator!r} does not apply to {field!r} ({spec['type']}); use {', '.join(offered)}"]
    kind, _ = _KINDS[spec["type"]]
    takes_list = operator in ("in", "not_in")

    if ref_path(value) is not None:
        problem = _check_ref(field, spec, kind, ref_path(value), takes_list, vocabulary, path)
        return [problem] if problem else []
    if operator == "is":
        return [] if isinstance(value, bool) else [f"{path}: {field!r} {operator} takes true or false, got {value!r}"]
    values = value if takes_list and isinstance(value, (list, tuple)) else [value]
    problems = []
    for item in values:
        target = ref_path(item) if takes_list else None
        problem = (
            _check_ref(field, spec, kind, target, True, vocabulary, path)
            if target is not None
            else _check_value(field, spec, kind, item, path)
        )
        if problem:
            problems.append(problem)
    return problems


def _check_ref(
    field: str,
    spec: Mapping[str, Any],
    kind: str,
    target: str,
    takes_list: bool,
    vocabulary: dict[str, dict[str, Any]],
    path: str,
) -> str | None:
    """A reference fits when it names a declared field of the same kind; a list field only where a list is taken."""
    other = vocabulary.get(target)
    if other is None:
        return f"{path}: {field!r} refers to an unknown field {target!r}"
    other_kind, other_many = _KINDS.get(other.get("type"), (None, False))
    if other_kind != kind or (other_many and not takes_list):
        return f"{path}: {field!r} ({spec['type']}) cannot be compared with {target!r} ({other.get('type')})"
    return None


def _check_value(field: str, spec: Mapping[str, Any], kind: str, value: Any, path: str) -> str | None:
    fits = {
        "text": isinstance(value, str),
        "bool": isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value),
    }[kind]
    if not fits:
        return f"{path}: {field!r} ({spec['type']}) cannot take {value!r}"
    options = spec.get("options")
    if options is not None and spec["type"] in ("select", "multi_select") and value not in options:
        return f"{path}: {value!r} is not one of {field!r}'s options ({', '.join(map(str, options))})"
    return None
