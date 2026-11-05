"""Characterization of real current v1 responses, not a proposed future API."""
import json
from pathlib import Path

import pytest
from scripts.check_v1_contract import assert_wire_equal

DAY = "2026-01-15"
FIXTURES = Path(__file__).parent / "fixtures"


def expect(name, response):
    expected = json.loads((FIXTURES / f"{name}.json").read_text())
    # JSON text distinguishes false/0 and integer/float, unlike Python equality.
    assert_wire_equal(expected, response)


@pytest.mark.parametrize("case,method,path,body,status", [
    ("register", "POST", "/auth/register", {"email": "C@example.invalid", "password": "synthetic-password-123", "name": "C"}, 201),
    ("duplicate-email", "POST", "/auth/register", {"email": "A@example.invalid", "password": "synthetic-password-123", "name": "A"}, 409),
    ("short-password", "POST", "/auth/register", {"email": "C@example.invalid", "password": "short", "name": "C"}, 422),
    ("login", "POST", "/auth/login", {"email": "A@example.invalid", "password": "synthetic-password-123"}, 200),
    ("wrong-password", "POST", "/auth/login", {"email": "A@example.invalid", "password": "wrong"}, 401),
    ("unknown-login", "POST", "/auth/login", {"email": "unknown@example.invalid", "password": "wrong"}, 401),
    ("refresh", "POST", "/auth/refresh", {"refresh_token": "{A.refresh}"}, 200),
    ("invalid-refresh", "POST", "/auth/refresh", {"refresh_token": "not-issued"}, 401),
    ("logout", "POST", "/auth/logout", {"refresh_token": "{A.refresh}"}, 200),
    ("unknown-logout", "POST", "/auth/logout", {"refresh_token": "not-issued"}, 200),
])
def test_auth_wire_contract(api, case, method, path, body, status):
    response = api(method, path, body=body)
    assert response["status"] == status
    expect(case, response)


@pytest.mark.parametrize("actor", ["A", "B"])
def test_refresh_replay_and_logout_real_api(api, actor):
    initial = {"refresh_token": "{" + actor + ".refresh}"}
    assert api("POST", "/auth/refresh", body=initial)["status"] == 200
    assert api("POST", "/auth/refresh", body=initial)["status"] == 401
    assert api("POST", "/auth/logout", body={"refresh_token": "{last.refresh}"})["status"] == 200
    assert api("POST", "/auth/refresh", body={"refresh_token": "{last.refresh}"})["status"] == 401
    # Current v1: logout revokes refresh, not the already issued access JWT.
    assert api("GET", "/users/me", actor)["status"] == 200


@pytest.mark.parametrize("method,path,body", [
    ("POST", "/auth/register", {}), ("POST", "/auth/login", {"email": "A@example.invalid"}),
    ("POST", "/auth/refresh", {}), ("POST", "/auth/logout", {"refresh_token": None}),
    ("POST", "/workouts", {"user_id": "{A}"}),
    ("POST", "/wellness-feedback", {"user_id": "{A}"}),
    ("POST", "/health-data/sync", {"user_id": "{A}", "start_date": DAY}),
    ("GET", "/readiness/{A}/history", None),
    ("GET", "/health-data/{A}/summary", None),
])
def test_missing_required_fields_are_422(api, method, path, body):
    result = api(method, path, body=body)
    assert result["status"] == 422
    assert all(error["type"] in {"missing", "string_type"} for error in result["body"]["detail"])
    assert result["provider_calls"] == 0


@pytest.mark.parametrize("actor,status", [(None, 403), ("invalid", 401)])
@pytest.mark.parametrize("path", ["/users/me", "/wellness-feedback/{A}", "/workouts/{A}?start_date=2026-01-15&end_date=2026-01-15",
                                  "/muscles/{A}/recovery?date=2026-01-15", "/readiness/{A}?date=2026-01-15"])
def test_unauthenticated_contract(api, actor, status, path):
    result = api("GET", path, actor)
    assert result["status"] == status and result["provider_calls"] == 0
    assert set(result["body"]) == {"detail"}


@pytest.mark.parametrize("actor,target", [("A", "B"), ("B", "A")])
def test_feedback_workout_and_recovery_are_account_scoped(api, actor, target):
    assert api("POST", "/wellness-feedback", actor, {"user_id": "{" + target + "}", "date": DAY})["status"] == 404
    assert api("POST", "/workouts", actor, workout(target))["status"] == 404
    for suffix in ["/wellness-feedback/{%s}?date=%s", "/muscles/{%s}/recovery?date=%s", "/readiness/{%s}?date=%s"]:
        assert api("GET", suffix % (target, DAY), actor)["status"] == 404


def workout(actor="A"):
    return {"user_id": "{" + actor + "}", "modality": "academia", "intensity": "moderado", "duration_min": 30,
            "date": DAY, "notes": None, "exercises": [{"name": "Supino reto", "sets": 3, "reps": None}]}


def test_feedback_numbers_nulls_and_upsert(api):
    expect("feedback-save", api("POST", "/wellness-feedback", body={
        "user_id": "{A}", "date": DAY, "workout_worthwhile": False, "feeling_score": 3, "notes": None}))
    expect("feedback-read", api("GET", f"/wellness-feedback/{{A}}?date={DAY}"))
    assert api("POST", "/wellness-feedback", body={"user_id": "{A}", "date": DAY, "feeling_score": 5})["status"] == 201
    result = api("GET", f"/wellness-feedback/{{A}}?date={DAY}")
    assert result["body"]["feeling_score"] == 5 and result["body"]["workout_worthwhile"] is None
    assert api("GET", f"/wellness-feedback/{{B}}?date={DAY}", "B")["status"] == 404


def test_workout_exercises_history_recovery_and_suggestion(api):
    expect("workout-create", api("POST", "/workouts", body=workout()))
    expect("workout-history", api("GET", f"/workouts/{{A}}?start_date={DAY}&end_date={DAY}"))
    expect("recovery", api("GET", f"/muscles/{{A}}/recovery?date={DAY}"))
    expect("suggestion", api("GET", f"/muscles/{{A}}/suggestion?date={DAY}"))
    assert api("GET", f"/workouts/{{B}}?start_date={DAY}&end_date={DAY}", "B")["body"] == []


def test_profile_null_is_ignored_and_json_list_is_deserialized(api):
    expect("profile", api("GET", "/users/me"))
    result = api("PATCH", "/users/me", body={"name": None, "weight_kg": 72.5, "preferred_modalities": ["corrida"]})
    assert result["body"]["name"] == "A" and result["body"]["weight_kg"] == 72.5
    assert result["body"]["preferred_modalities"] == ["corrida"]
    assert "password_hash" not in result["body"]


@pytest.mark.parametrize("field,value,status", [("duration_min", 0, 422), ("modality", "invalid", 400), ("intensity", "invalid", 400)])
def test_workout_rejects_invalid_inputs(api, field, value, status):
    body = workout()
    body[field] = value
    assert api("POST", "/workouts", body=body)["status"] == status


@pytest.mark.parametrize("omitted", [False, True])
def test_workout_null_or_missing_date_defaults_to_today(api, omitted):
    body = workout()
    if omitted:
        body.pop("date")
    else:
        body["date"] = None
    response = api("POST", "/workouts", body=body)
    assert response["status"] == 201 and response["body"]["date"] == DAY
    history = api("GET", f"/workouts/{{A}}?start_date={DAY}&end_date={DAY}")
    assert len(history["body"]) == 1 and history["body"][0]["date"] == DAY


@pytest.mark.parametrize("bad_date", ["invalid", "2026-02-30", ""])
def test_invalid_workout_date_is_rejected_before_persistence(api, bad_date):
    body = workout()
    body["date"] = bad_date
    assert api("POST", "/workouts", body=body)["status"] == 400
    assert api("GET", f"/workouts/{{A}}?start_date={DAY}&end_date={DAY}")["body"] == []


def test_health_ingestion_readiness_history_and_advanced(api):
    expect("empty-summary", api("GET", f"/health-data/{{A}}/summary?date={DAY}"))
    expect("no-readiness", api("GET", f"/readiness/{{A}}?date={DAY}"))
    assert api("CONNECT", "", "A")["status"] == 200
    expect("sync", api("POST", "/health-data/sync", body={"user_id": "{A}", "start_date": DAY, "end_date": DAY}))
    expect("health-summary", api("GET", f"/health-data/{{A}}/summary?date={DAY}"))
    expect("readiness", api("GET", f"/readiness/{{A}}?date={DAY}"))
    expect("readiness-history", api("GET", f"/readiness/{{A}}/history?start_date={DAY}&end_date={DAY}"))
    expect("advanced", api("GET", f"/readiness/{{A}}/advanced?date={DAY}"))
    expect("modalities", api("GET", f"/readiness/modalities/{{A}}?date={DAY}"))
    assert api("GET", f"/readiness/{{B}}?date={DAY}", "B")["status"] == 422


@pytest.mark.parametrize("path", ["/health-data/{A}/summary?date=invalid", "/health-data/{A}/summary?date=2026-02-30"])
def test_invalid_health_dates(api, path):
    assert api("GET", path)["status"] == 400


def test_missing_provider_connection_and_bad_sync_dates(api):
    body = {"user_id": "{A}", "start_date": DAY, "end_date": DAY}
    assert api("POST", "/health-data/sync", body=body)["status"] == 404
    body["start_date"] = "invalid"
    response = api("POST", "/health-data/sync", body=body)
    assert response["status"] == 400 and response["provider_calls"] == 0
