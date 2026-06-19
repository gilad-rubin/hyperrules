from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from hyperrules.engine import evaluate


def load_dir(path: str | Path, *, when_key: str = "when") -> list[dict]:
    """Read every ``*.json`` rule file in ``path`` (sorted) into a list of dicts."""
    directory = Path(path)
    if not directory.is_dir():
        return []
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(directory.glob("*.json"))
    ]


class RuleSet:
    """A collection of rule dicts. A rule is matched when its ``when`` subtree
    evaluates true (or it has no ``when`` key, in which case it always matches)."""

    def __init__(self, rules: list[dict], *, when_key: str = "when") -> None:
        self.rules = rules
        self.when_key = when_key

    @classmethod
    def load_dir(cls, path: str | Path, *, when_key: str = "when") -> "RuleSet":
        return cls(load_dir(path, when_key=when_key), when_key=when_key)

    def matching(self, context: Mapping[str, Any]) -> list[dict]:
        return [
            rule
            for rule in self.rules
            if self.when_key not in rule or evaluate(rule[self.when_key], context)
        ]

    def concat(self, context: Mapping[str, Any], *, key: str, sep: str = "\n\n") -> str:
        """Join the ``key`` payload of every matching rule (additive append)."""
        return sep.join(rule[key] for rule in self.matching(context) if rule.get(key))

    def first(self, context: Mapping[str, Any]) -> dict | None:
        """The first matching rule dict, or ``None`` (first-match-wins hosts)."""
        matched = self.matching(context)
        return matched[0] if matched else None
