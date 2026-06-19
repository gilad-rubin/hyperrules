# rules

Tiny, zero-dependency predicate->payload rule engine.

A **rule** is a plain dict with a `when` key holding a nestable boolean condition
tree, plus opaque payload keys (`text`, `then`/`else`, …) the engine never reads:

- **leaf** — `{"field": "...", "operator": "...", "value": ...}`
- **group** — `{"combinator": "and" | "or" | "not", "rules": [ ...nodes... ]}`

```python
from rules import evaluate, load_dir, validate, RuleSet

tree = {"combinator": "and", "rules": [
    {"field": "document_tag", "operator": "in", "value": ["drug_leaflet", "formulary"]},
]}
evaluate(tree, {"document_tag": ["drug_leaflet"]})   # -> True

rules = RuleSet.load_dir("path/to/rules")            # reads *.json
text = rules.concat({"document_tag": ["drug_leaflet"]}, key="text")
```

Operators: `=`, `!=`, `in`, `is`, `>`, `<`. Combinators: `and`, `or`, `not`.
The engine depends on nothing; validation (`validate`) is a separate save-time
concern, never on the evaluation hot path.
