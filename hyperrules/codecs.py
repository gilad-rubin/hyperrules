"""Rule-level codecs: markdown with frontmatter, YAML dicts, JSON dicts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hyperrules.refs import has_ref
from hyperrules.types import And, Group, Leaf, Rule, _node_from_dict


def rule_to_dict(rule: Rule) -> dict[str, Any]:
    return rule.to_dict()


def rule_from_dict(data: dict[str, Any]) -> Rule:
    return Rule(
        when=_condition_from_dict(data["when"]),
        then=data["then"],
        name=data.get("name"),
    )


def condition_to_simple_dict(condition: Leaf | Group) -> dict[str, Any] | None:
    """The ``{field: [values]}`` shorthand of an all-``in`` condition, or None when it has none (a reference has none)."""
    leaves = [condition] if isinstance(condition, Leaf) else list(getattr(condition, "conditions", ()))
    if any(isinstance(leaf, Leaf) and has_ref(leaf.value) for leaf in leaves):
        return None
    if isinstance(condition, Leaf) and condition.operator == "in":
        return {condition.field: condition.value}
    if isinstance(condition, Group) and condition.combinator == "and":
        if all(isinstance(c, Leaf) and c.operator == "in" for c in condition.conditions):
            fields = [c.field for c in condition.conditions]
            if len(fields) != len(set(fields)):
                return None
            return {c.field: c.value for c in condition.conditions}
    return None


def condition_from_simple_dict(data: dict[str, Any]) -> Group:
    leaves = [Leaf(field=k, operator="in", value=v if isinstance(v, list) else [v]) for k, v in data.items()]
    return And(*leaves) if len(leaves) != 1 else Group(combinator="and", conditions=tuple(leaves))


def _condition_from_dict(data: dict[str, Any]) -> Leaf | Group:
    if "combinator" in data or "field" in data:
        return _node_from_dict(data)
    return condition_from_simple_dict(data)


def load_rule(path: str | Path) -> Rule:
    """Load a Rule from a markdown file with YAML frontmatter."""
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required for loading rule files: pip install pyyaml")

    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"Expected YAML frontmatter in {path}")

    _, front, body = text.split("---", 2)
    meta = yaml.safe_load(front)
    when_data = meta.get("when")
    if when_data is None:
        when_data = {}
    condition = _condition_from_dict(when_data)
    return Rule(
        when=condition,
        then=body.strip(),
        name=meta.get("name", Path(path).stem),
    )


def save_rule(rule: Rule, path: str | Path) -> None:
    """Save a Rule to a markdown file with YAML frontmatter."""
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required for saving rule files: pip install pyyaml")

    meta: dict[str, Any] = {}
    if rule.name is not None:
        meta["name"] = rule.name

    simple = condition_to_simple_dict(rule.when)
    meta["when"] = simple if simple is not None else rule.when.to_dict()

    frontmatter = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
    payload = rule.then if isinstance(rule.then, str) else str(rule.then)
    Path(path).write_text(f"---\n{frontmatter}---\n{payload}\n", encoding="utf-8")
