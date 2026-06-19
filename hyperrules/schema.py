"""Declare a field vocabulary once, hand the UI the schema it renders from.

This is the rule engine's "talk to it" surface — the analog of hypster's
``explore``: a host declares its closed field vocabulary as ``Field`` objects,
wraps them in a ``Schema``, and ``schema.to_dict()`` is the exact JSON contract
the ``<ConditionBuilder>`` builds an editor from. The package owns the
field-type -> operators map so hosts don't re-derive it.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field
from typing import Any

# Which operators each field type offers (and, implicitly, its value widget).
DEFAULT_OPERATORS: dict[str, list[str]] = {
    "multi_enum": ["in"],
    "enum": ["=", "!="],
    "bool": ["is"],
    "number": [">", "<", "=", "!="],
    "string": ["="],
}


@dataclass
class Field:
    """One predicate the UI can build a condition from."""

    id: str
    label: str
    type: str
    options: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"id": self.id, "label": self.label, "type": self.type}
        if self.options is not None:
            data["options"] = list(self.options)
        return data


@dataclass
class Schema:
    """A closed field vocabulary plus the operator map the editor renders."""

    fields: list[Field]
    operators: dict[str, list[str]] = _field(default_factory=lambda: dict(DEFAULT_OPERATORS))

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": [field.to_dict() for field in self.fields],
            "operators": {key: list(value) for key, value in self.operators.items()},
        }
