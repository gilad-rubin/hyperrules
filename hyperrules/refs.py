"""References: a leaf's value that names another field of the context.

``{"field": "district", "operator": "=", "value": {"ref": "user.district"}}``
compares a document's district with the requesting user's own. A reference is
plain JSON, so it lives in YAML, rule dicts and hypster's recorded values as
it is, and it may stand inside a list of values too
(``{"operator": "in", "value": ["National", {"ref": "user.district"}]}``).
Field names and references are paths: ``user.district`` reads the context's
``"user.district"`` key when it has one, else ``context["user"]["district"]``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

MISSING = object()
"""What ``lookup`` returns for a path the context does not hold."""


def ref(path: str) -> dict[str, str]:
    """A leaf value that reads ``path`` from the context, e.g. ``ref("user.district")``."""
    if not isinstance(path, str) or not path:
        raise ValueError(f"a reference names a field, got {path!r}")
    return {"ref": path}


def ref_path(value: Any) -> str | None:
    """The path ``value`` refers to, or ``None`` when it is a plain value."""
    if (
        isinstance(value, Mapping)
        and set(value) == {"ref"}
        and isinstance(value["ref"], str)
    ):
        return value["ref"]
    return None


def has_ref(value: Any) -> bool:
    """True when ``value`` is a reference or a list of values holding one."""
    if isinstance(value, (list, tuple)):
        return any(ref_path(item) is not None for item in value)
    return ref_path(value) is not None


def lookup(context: Mapping[str, Any], path: str) -> Any:
    """The context's value at ``path``, or ``MISSING``."""
    if path in context:
        return context[path]
    node: Any = context
    for part in path.split("."):
        if not isinstance(node, Mapping) or part not in node:
            return MISSING
        node = node[part]
    return node
