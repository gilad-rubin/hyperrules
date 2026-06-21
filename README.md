# rules

Tiny, zero-dependency predicate->payload rule engine.

A **rule** is a plain dict with a `when` key holding a nestable boolean condition
tree, plus opaque payload keys (`text`, `then`/`else`, …) the engine never reads:

- **leaf** — `{"field": "...", "operator": "...", "value": ...}`
- **group** — `{"combinator": "and" | "or" | "not", "conditions": [ ...nodes... ]}`

```python
from hyperrules import matches, load_dir, validate, RuleSet

tree = {"combinator": "and", "conditions": [
    {"field": "document_tag", "operator": "in", "value": ["drug_leaflet", "formulary"]},
]}
matches(tree, {"document_tag": ["drug_leaflet"]})   # -> True

rules = RuleSet.load_dir("path/to/rules")            # reads *.json
text = rules.concat({"document_tag": ["drug_leaflet"]}, key="text")
```

Operators: `=`, `!=`, `in`, `not_in`, `is`, `>`, `<`, `contains`. Combinators: `and`, `or`, `not`.
The engine depends on nothing; validation (`validate`) is a separate save-time
concern, never on the evaluation hot path.

## Talking to the UI — declare a field schema

The "talk to it" surface (the analog of hypster's `explore`): declare your closed
field vocabulary once, and `Schema.to_dict()` is the exact JSON the
`<ConditionBuilder>` UI renders an editor from. The package owns the
field-type → operators map, so hosts don't re-derive it.

```python
from hyperrules import Field, Schema

schema = Schema([
    Field("document_tag", "Document tag", "multi_enum", options=["drug_leaflet", "formulary"]),
    Field("document_station", "Document station", "enum", options=["NICU", "ER"]),
    Field("vision_page_presence", "Has diagram page", "bool"),
])
schema.to_dict()
# {"fields": [...], "operators": {"multi_enum": ["in"], "enum": ["=", "!="], "bool": ["is"], ...}}
```

Field types: `enum`, `multi_enum`, `bool`, `number`, `string`.
