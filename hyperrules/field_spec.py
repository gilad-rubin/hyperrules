from __future__ import annotations

from dataclasses import dataclass, field as _field
from typing import Any

from hyperrules.refs import ref
from hyperrules.types import Leaf

DEFAULT_OPERATORS: dict[str, list[str]] = {
    "select": ["=", "!=", "in", "not_in"],
    "multi_select": ["in", "not_in"],
    "bool": ["is"],
    "multi_bool": ["in"],
    "int": [">", "<", "=", "!="],
    "multi_int": ["in", "contains"],
    "float": [">", "<", "=", "!="],
    "multi_float": ["in", "contains"],
    "text": ["=", "contains"],
    "multi_text": ["in", "contains"],
}


@dataclass(frozen=True)
class FieldSpec:
    type: str
    name: str | None = None
    description: str | None = None
    options: tuple[Any, ...] | None = None
    multiline: bool = False
    operators: tuple[str, ...] = ()

    def eq(self, value: Any) -> Leaf:
        return Leaf(self._require_name(), "=", _operand(value))

    def neq(self, value: Any) -> Leaf:
        return Leaf(self._require_name(), "!=", _operand(value))

    def is_in(self, values: list | tuple | FieldSpec) -> Leaf:
        return Leaf(self._require_name(), "in", _operands(values))

    def not_in(self, values: list | tuple | FieldSpec) -> Leaf:
        return Leaf(self._require_name(), "not_in", _operands(values))

    def is_true(self) -> Leaf:
        return Leaf(self._require_name(), "is", True)

    def is_false(self) -> Leaf:
        return Leaf(self._require_name(), "is", False)

    def gt(self, value: Any) -> Leaf:
        return Leaf(self._require_name(), ">", _operand(value))

    def lt(self, value: Any) -> Leaf:
        return Leaf(self._require_name(), "<", _operand(value))

    def contains(self, value: Any) -> Leaf:
        return Leaf(self._require_name(), "contains", _operand(value))

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"type": self.type}
        if self.name is not None:
            result["name"] = self.name
        if self.description is not None:
            result["description"] = self.description
        if self.options is not None:
            result["options"] = list(self.options)
        if self.multiline:
            result["multiline"] = True
        result["operators"] = list(self.operators)
        return result

    def _require_name(self) -> str:
        if self.name is None:
            raise ValueError("FieldSpec must have a name to build conditions")
        return self.name


def _operand(value: Any) -> Any:
    """A field spec given as a value is a reference to that field (``district.eq(user_district)``)."""
    return ref(value._require_name()) if isinstance(value, FieldSpec) else value


def _operands(values: Any) -> Any:
    """A list of values, each field spec in it a reference (``district.is_in(["National", user_district])``)."""
    return _operand(values) if isinstance(values, FieldSpec) else [_operand(value) for value in values]


def _make_spec(type_name: str, *, name: str | None, description: str | None, options: tuple | None = None, multiline: bool = False) -> FieldSpec:
    ops = tuple(DEFAULT_OPERATORS.get(type_name, []))
    return FieldSpec(type=type_name, name=name, description=description, options=options, multiline=multiline, operators=ops)
