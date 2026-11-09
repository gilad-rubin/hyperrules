# hyperrules

Tiny, zero-dependency predicate->payload rule engine.

A **rule** is a plain dict with a `when` key holding a nestable boolean condition
tree, plus opaque payload keys (`text`, `then`/`else`, …) the engine never reads:

- **leaf** — `{"field": "...", "operator": "...", "value": ...}`
- **group** — `{"combinator": "and" | "or" | "not", "conditions": [ ...nodes... ]}`

```python
from hyperrules import matches, validate, RuleSet

tree = {"combinator": "and", "conditions": [
    {"field": "document_tag", "operator": "in", "value": ["drug_leaflet", "formulary"]},
]}
matches(tree, {"document_tag": ["drug_leaflet"]})   # -> True

rules = RuleSet.load_dir("path/to/rules")           # reads *.json
text = rules.concat({"document_tag": ["drug_leaflet"]}, key="text")
```

Operators: `=`, `!=`, `in`, `not_in`, `is`, `>`, `<`, `contains`. Combinators: `and`, `or`, `not`.
A leaf is false when its field is missing or `None`; a `not` group inverts it, as it inverts any leaf.
The engine depends on nothing; validation (`validate`) is a separate save-time
concern, never on the evaluation hot path.

## The user's own context — references

A leaf's value may name another field of the context instead of a fixed value:
`{"ref": "user.district"}`. "Show a document of the user's own district" is

```python
from hyperrules import field, matches, ref

district = field.select(["North", "South"], name="district")
user_district = field.select(["North", "South"], name="user.district")

own = district.eq(user_district)          # a field spec as a value is a reference to it
own.to_dict()                             # {"field": "district", "operator": "=", "value": {"ref": "user.district"}}
matches(own, {"district": "North", "user": {"district": "North"}})   # -> True
matches(own, {"district": "North", "user": {}})                      # -> False: a missing value never matches
```

A reference is plain JSON, so it lives in YAML, rule files and hypster's recorded `hp.rules` values as it is
(`hypster.field` specs take `ref("user.district")`). Field names and references are paths: `user.district` reads the
context's `"user.district"` key when it has one, else `context["user"]["district"]`.

A reference may stand inside a list of values too. "National documents, and the user's own district" is

```python
national_or_own = district.is_in(["National", user_district])
# {"field": "district", "operator": "in", "value": ["National", {"ref": "user.district"}]}
matches(national_or_own, {"district": "National", "user": {}})       # -> True: a missing reference is one value fewer
```

Inside an `in` list, a missing reference is one value fewer and the others still match; a reference to a list adds
each of its values. Inside a `not_in` list, a missing reference makes the leaf false, since the unknown value might be
the document's. `lookup(context, path)` reads a path the same way the engine does, and returns `MISSING` when the
context lacks it.

## Checking rules when they are saved

Given the fields a rule may name (field specs from `hyperrules.field` or `hypster.field`, or their `to_dict()` form;
dotted names declare the context a reference reads), `validate` and `validate_rules` name every problem by its place:
an unknown field or reference, an operator the field's type does not offer, a value or reference of the wrong type, a
value outside a select's options. A host refuses the rule set when the list is not empty; a condition is never dropped.

```python
from hyperrules import validate, validate_rules

validate({"field": "distrct", "operator": "=", "value": "North"}, fields=[district, user_district])
# ["when: unknown field 'distrct'"]
validate_rules(rules, fields=[district, user_district])   # Rule objects or dicts, by rules[i].when
```

Without `fields`, only the tree's shape (operators, combinators, keys) is checked.

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
