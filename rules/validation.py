from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rules.engine import OPERATORS

COMBINATORS = {"and", "or", "not"}


def validate(tree: Mapping[str, Any], *, path: str = "when") -> list[str]:
    """Return human-readable problems with a condition ``tree`` (empty = valid).

    Save-time / CI use only — never call this on the evaluation hot path.
    """
    errors: list[str] = []
    if "combinator" in tree:  # group node
        if tree["combinator"] not in COMBINATORS:
            errors.append(f"{path}: unknown combinator {tree['combinator']!r}")
        rules = tree.get("rules")
        if not isinstance(rules, list):
            errors.append(f"{path}: group is missing a 'rules' list")
        else:
            for index, child in enumerate(rules):
                errors.extend(validate(child, path=f"{path}.rules[{index}]"))
        return errors
    if "field" not in tree:  # leaf node
        errors.append(f"{path}: leaf is missing 'field'")
    operator = tree.get("operator")
    if operator not in OPERATORS:
        errors.append(f"{path}: unknown operator {operator!r}")
    return errors
