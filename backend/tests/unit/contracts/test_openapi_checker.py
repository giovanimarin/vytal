import copy
import json
from pathlib import Path

import pytest
from scripts.check_v1_contract import assert_compatible, normalize_contract

BASELINE = Path(__file__).resolve().parents[2] / "baseline/fixtures/openapi-v1.json"


@pytest.fixture
def schema():
    return json.loads(BASELINE.read_text())


@pytest.mark.parametrize("mutation", ["path", "method", "status", "request-type", "request-required", "nullable",
                                      "field-removal", "response", "security", "body-required", "default", "bounds",
                                      "optional-field-required", "date-serialization", "number-serialization"])
def test_checker_rejects_public_contract_mutations(schema, mutation):
    changed = copy.deepcopy(schema)
    login = changed["paths"]["/api/v1/auth/login"]["post"]
    workout = changed["components"]["schemas"]["WorkoutIn"]
    if mutation == "path":
        del changed["paths"]["/api/v1/auth/login"]
    elif mutation == "method":
        changed["paths"]["/api/v1/auth/login"]["get"] = login
        del changed["paths"]["/api/v1/auth/login"]["post"]
    elif mutation == "status":
        login["responses"]["201"] = login["responses"].pop("200")
    elif mutation == "request-type":
        workout["properties"]["duration_min"]["type"] = "string"
    elif mutation == "request-required":
        workout["required"].remove("user_id")
    elif mutation == "nullable":
        workout["properties"]["notes"] = {"type": "string"}
    elif mutation == "field-removal":
        del workout["properties"]["notes"]
    elif mutation == "response":
        login["responses"]["200"]["content"]["application/json"]["schema"] = {"type": "array"}
    elif mutation == "security":
        changed["components"]["securitySchemes"]["HTTPBearer"]["scheme"] = "basic"
    elif mutation == "body-required":
        login["requestBody"]["required"] = False
    elif mutation == "default":
        workout["properties"]["notes"]["default"] = "changed-default"
    elif mutation == "bounds":
        workout["properties"]["duration_min"]["exclusiveMinimum"] = 1
    elif mutation == "optional-field-required":
        workout["required"].append("notes")
    else:
        # Enforce format/type changes even when outputs currently lack models.
        workout["properties"]["date" if mutation == "date-serialization" else "duration_min"]["format"] = "changed-format"
    with pytest.raises(ValueError, match="Public OpenAPI contract differs"):
        assert_compatible(schema, changed)


def test_query_nullability_is_not_silently_normalized_away(schema):
    before = {"parameters": [{"in": "query", "name": "date", "required": False, "schema": {"type": "string"}}]}
    after = copy.deepcopy(before)
    after["parameters"][0]["schema"] = {"anyOf": [{"type": "string"}, {"type": "null"}]}
    with pytest.raises(ValueError):
        assert_compatible(before, after)


def test_editorial_description_and_parameter_order_are_ignored(schema):
    changed = copy.deepcopy(schema)
    changed["paths"]["/api/v1/auth/login"]["post"]["description"] = "Editorial correction"
    assert_compatible(schema, changed)
    assert normalize_contract({"parameters": [{"in": "query", "name": "b"}, {"in": "query", "name": "a"}]}) == {
        "parameters": [{"in": "query", "name": "a"}, {"in": "query", "name": "b"}]}


@pytest.mark.parametrize("location", ["properties", "default"])
def test_payload_fields_named_description_are_never_ignored(location):
    before = {location: {"description": {"type": "string"}}}
    after = copy.deepcopy(before)
    after[location]["description"] = {"type": "integer"}
    with pytest.raises(ValueError):
        assert_compatible(before, after)


@pytest.mark.parametrize("before,after", [
    ({"date": "2026-01-15"}, {"date": "2026-01-15T00:00:00Z"}),
    ({"value": None}, {"value": ""}), ({"value": 0}, {"value": False}),
    ({"score": 1.0}, {"score": 1}), ({"optional": None}, {}),
    ({"status": 201}, {"status": 200}), ({"description": "a"}, {"description": "b"}),
])
def test_observed_response_contract_rejects_serialization_and_field_changes(before, after):
    from scripts.check_v1_contract import assert_wire_equal

    with pytest.raises(ValueError, match="Observed v1 response contract differs"):
        assert_wire_equal(before, after)


def test_explicit_additions_mode_accepts_new_operations_but_preserves_existing_contracts(schema):
    added = copy.deepcopy(schema)
    added['paths']['/api/v1/additive-only'] = {'get': {'responses': {'200': {'description': 'OK'}}}}
    added['components']['schemas']['AddedOnly'] = {'type': 'object'}
    with pytest.raises(ValueError):
        assert_compatible(schema, added)
    assert_compatible(schema, added, allow_additions=True)
    added['components']['schemas']['WorkoutIn']['required'].append('notes')
    with pytest.raises(ValueError):
        assert_compatible(schema, added, allow_additions=True)
