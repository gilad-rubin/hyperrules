"""``field.*`` constructors — mirrors ``hp.*`` names exactly.

Usage::

    from hyperrules import field

    tag = field.multi_select(["drug_leaflet", "formulary"], name="document_tag")
    station = field.select(["NICU", "ER", "ICU"], name="document_station")
    has_diagram = field.bool(name="vision_page_presence")
"""

from __future__ import annotations

from typing import Any

from hyperrules.field_spec import FieldSpec, _make_spec


def select(options: list[Any], *, name: str | None = None, description: str | None = None) -> FieldSpec:
    return _make_spec("select", name=name, description=description, options=tuple(options))


def multi_select(options: list[Any], *, name: str | None = None, description: str | None = None) -> FieldSpec:
    return _make_spec("multi_select", name=name, description=description, options=tuple(options))


def bool(*, name: str | None = None, description: str | None = None) -> FieldSpec:
    return _make_spec("bool", name=name, description=description)


def multi_bool(*, name: str | None = None, description: str | None = None) -> FieldSpec:
    return _make_spec("multi_bool", name=name, description=description)


def int(*, name: str | None = None, description: str | None = None) -> FieldSpec:
    return _make_spec("int", name=name, description=description)


def multi_int(*, name: str | None = None, description: str | None = None) -> FieldSpec:
    return _make_spec("multi_int", name=name, description=description)


def float(*, name: str | None = None, description: str | None = None) -> FieldSpec:
    return _make_spec("float", name=name, description=description)


def multi_float(*, name: str | None = None, description: str | None = None) -> FieldSpec:
    return _make_spec("multi_float", name=name, description=description)


def text(*, name: str | None = None, description: str | None = None, multiline: bool = False) -> FieldSpec:
    return _make_spec("text", name=name, description=description, multiline=multiline)


def multi_text(*, name: str | None = None, description: str | None = None) -> FieldSpec:
    return _make_spec("multi_text", name=name, description=description)
