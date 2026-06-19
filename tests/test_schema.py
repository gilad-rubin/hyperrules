from rules import Field, Schema


def test_schema_to_dict_emits_fields_and_the_operator_map():
    schema = Schema([
        Field("document_tag", "Document tag", "multi_enum", options=["drug_leaflet", "formulary"]),
        Field("vision_page_presence", "Has diagram page", "bool"),
    ])

    data = schema.to_dict()

    fields = {f["id"]: f for f in data["fields"]}
    assert fields["document_tag"]["type"] == "multi_enum"
    assert fields["document_tag"]["options"] == ["drug_leaflet", "formulary"]
    assert "options" not in fields["vision_page_presence"]
    assert data["operators"]["multi_enum"] == ["in"]
    assert data["operators"]["bool"] == ["is"]
