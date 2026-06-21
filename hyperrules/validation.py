from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from hyperrules.engine import OPERATORS

COMBINATORS = {"and", "or", "not"}


def validate(tree: Mapping[str, Any], *, path: str = "when") -> list[str]:
    """Return human-readable problems with a condition ``tree`` (empty = valid).

    Save-time / CI use only — never call this on the evaluation hot path.
    """
    from hyperrules.types import Group, Leaf

    if isinstance(tree, Leaf):
        errors: list[str] = []
        if tree.operator not in OPERATORS:
            errors.append(f"{path}: unknown operator {tree.operator!r}")
        return errors

    if isinstance(tree, Group):
        errors = []
        if tree.combinator not in COMBINATORS:
            errors.append(f"{path}: unknown combinator {tree.combinator!r}")
        if tree.combinator == "not" and len(tree.conditions) != 1:
            errors.append(f"{path}: NOT group must have exactly one child, got {len(tree.conditions)}")
        for index, child in enumerate(tree.conditions):
            errors.extend(validate(child, path=f"{path}.conditions[{index}]"))
        return errors

    errors = []
    if "combinator" in tree:  # group node
        if tree["combinator"] not in COMBINATORS:
            errors.append(f"{path}: unknown combinator {tree['combinator']!r}")
        children = tree.get("conditions")
        if not isinstance(children, list):
            errors.append(f"{path}: group is missing a 'conditions' list")
        else:
            if tree["combinator"] == "not" and len(children) != 1:
                errors.append(f"{path}: NOT group must have exactly one child, got {len(children)}")
            for index, child in enumerate(children):
                errors.extend(validate(child, path=f"{path}.conditions[{index}]"))
        return errors
    if "field" not in tree:
        errors.append(f"{path}: leaf is missing 'field'")
    if "operator" not in tree:
        errors.append(f"{path}: leaf is missing 'operator'")
    if "value" not in tree:
        errors.append(f"{path}: leaf is missing 'value'")
    operator = tree.get("operator")
    if operator is not None and operator not in OPERATORS:
        errors.append(f"{path}: unknown operator {operator!r}")
    return errors
