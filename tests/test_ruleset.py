import json
from pathlib import Path

from hyperrules import RuleSet, load_dir


def _write(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj), encoding="utf-8")


def _leaf(field: str, operator: str, value) -> dict:
    return {"combinator": "and", "rules": [{"field": field, "operator": operator, "value": value}]}


def test_ruleset_matching_returns_only_matched_rule_dicts(tmp_path: Path) -> None:
    _write(tmp_path / "leaflet.json",
           {"name": "leaflet", "when": _leaf("document_tag", "in", ["drug_leaflet"]), "text": "LEAFLET"})
    _write(tmp_path / "er.json",
           {"name": "er", "when": _leaf("selected_station", "=", "ER"), "text": "ER"})

    rules = RuleSet.load_dir(tmp_path)
    matched = rules.matching({"document_tag": ["drug_leaflet"], "selected_station": "NICU"})

    assert [r["name"] for r in matched] == ["leaflet"]


def test_concat_joins_matched_payload_text(tmp_path: Path) -> None:
    _write(tmp_path / "leaflet.json",
           {"name": "leaflet", "when": _leaf("document_tag", "in", ["drug_leaflet"]), "text": "LEAFLET"})
    _write(tmp_path / "er.json",
           {"name": "er", "when": _leaf("selected_station", "=", "ER"), "text": "ER"})

    rules = RuleSet.load_dir(tmp_path)
    both = rules.concat({"document_tag": ["drug_leaflet"], "selected_station": "ER"}, key="text")
    none = rules.concat({"document_tag": ["other"], "selected_station": "NICU"}, key="text")

    assert both == "ER\n\nLEAFLET"  # filename-sorted: er.json before leaflet.json
    assert none == ""


def test_first_returns_first_match_or_none(tmp_path: Path) -> None:
    _write(tmp_path / "er.json",
           {"name": "er", "when": _leaf("selected_station", "=", "ER"), "then": "X"})

    rules = RuleSet.load_dir(tmp_path)
    assert rules.first({"selected_station": "ER"})["name"] == "er"
    assert rules.first({"selected_station": "NICU"}) is None


def test_rule_without_when_always_matches(tmp_path: Path) -> None:
    _write(tmp_path / "always.json", {"name": "always", "text": "ALWAYS"})
    rules = RuleSet.load_dir(tmp_path)
    assert rules.concat({}, key="text") == "ALWAYS"


def test_load_dir_missing_dir_returns_empty(tmp_path: Path) -> None:
    assert load_dir(tmp_path / "does-not-exist") == []
