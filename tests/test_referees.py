"""Tests for :mod:`gamesheet_sdk.referees`."""

# pylint: disable=too-many-lines

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
)
from gamesheet_sdk.referees import (
    Referee,
    create_referee,
    delete_referee,
    get_referee,
    list_referees,
    update_referee,
)

_BASE = "https://test.example"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/referees"


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a JSON:API ``{"data": [...]}`` body."""
    return {"data": rows}


@responses.activate
def test_list_referees_parses_jsonapi_response(config: Config) -> None:

    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_payload(
            [
                {
                    "type": "referees",
                    "id": "101",
                    "attributes": {
                        "first_name": "John",
                        "last_name": "Smith",
                        "email_address": "john.smith@example.com",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-15T14:30:00Z",
                    },
                    "relationships": {
                        "season": {
                            "data": {
                                "type": "seasons",
                                "id": _SEASON_ID,
                            },
                        },
                    },
                },
                {
                    "type": "referees",
                    "id": "102",
                    "attributes": {
                        "first_name": "Jane",
                        "last_name": "Doe",
                        "email_address": None,
                        "created_at": "2023-09-01T10:00:00Z",
                        "updated_at": "2023-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {
                            "data": {
                                "type": "seasons",
                                "id": _SEASON_ID,
                            },
                        },
                    },
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("any-non-empty-token")
        result = list_referees(session, _SEASON_ID)
    assert [r.id for r in result] == ["101", "102"]
    assert result[0].first_name == "John"
    assert result[0].last_name == "Smith"
    assert result[0].email == "john.smith@example.com"
    assert result[0].season_id == _SEASON_ID
    assert result[0].created_at == datetime(2024, 9, 1, 10, tzinfo=timezone.utc)
    assert result[0].updated_at == datetime(2024, 9, 15, 14, 30, tzinfo=timezone.utc)
    assert result[1].first_name == "Jane"
    assert result[1].last_name == "Doe"
    assert result[1].email is None


@responses.activate
def test_list_referees_sends_bearer_and_jsonapi_accept(config: Config) -> None:

    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        list_referees(session, _SEASON_ID)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer abc"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_list_referees_empty_data_returns_empty_list(config: Config) -> None:

    responses.add(responses.GET, _ENDPOINT, json=_payload([]), status=200)
    with Session(config) as session:
        session.set_bearer_token("abc")
        assert not list_referees(session, _SEASON_ID)


@responses.activate
def test_list_referees_401_raises_authentication_error(config: Config) -> None:

    responses.add(
        responses.GET,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            list_referees(session, _SEASON_ID)


@responses.activate
def test_list_referees_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:

    responses.add(responses.GET, _ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Season '.*' not found.*valid season ID.*seasons list --league-id",
        ):
            list_referees(session, _SEASON_ID)


@responses.activate
def test_list_referees_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    responses.add(responses.GET, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            list_referees(session, _SEASON_ID)


def test_referee_model_ignores_unknown_attributes() -> None:

    r = Referee(
        id="101",
        season_id="15020",
        first_name="John",
        last_name="Smith",
        email="john.smith@example.com",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        unexpected_future_attr="ignored",
    )
    assert r.first_name == "John"
    assert r.last_name == "Smith"


def test_referee_model_handles_optional_email() -> None:

    r = Referee(
        id="102",
        season_id="15020",
        first_name="Jane",
        last_name="Doe",
        email=None,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    assert r.email is None


@responses.activate
@responses.activate
def test_get_referee_returns_single_referee(config: Config) -> None:
    _referee_id = "1146197"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": "0EB978DD-66B8-4CA1-AAA8-D855EED39D6A",
                    "first_name": "WES",
                    "last_name": "MCCAULEY",
                    "email_address": "Wes.McCauley@example.com",
                    "created_at": "2026-06-15T12:04:05.0325Z",
                    "updated_at": "2026-06-15T12:04:05.0325Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_referee(session, _SEASON_ID, _referee_id)
    assert result.id == _referee_id
    assert result.first_name == "WES"
    assert result.last_name == "MCCAULEY"
    assert result.email == "Wes.McCauley@example.com"
    assert result.season_id == _SEASON_ID


@responses.activate
def test_get_referee_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    _referee_id = "101"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Test",
                    "last_name": "Ref",
                    "created_at": "2024-09-01T10:00:00Z",
                    "updated_at": "2024-09-01T10:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        get_referee(session, _SEASON_ID, _referee_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_get_referee_401_raises_authentication_error(config: Config) -> None:
    _referee_id = "101"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            get_referee(session, _SEASON_ID, _referee_id)


@responses.activate
def test_get_referee_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    _referee_id = "nonexistent"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(responses.GET, _get_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Referee '.*' not found.*valid referee ID and season ID",
        ):
            get_referee(session, _SEASON_ID, _referee_id)


@responses.activate
def test_get_referee_other_failure_raises_gamesheet_error(config: Config) -> None:
    _referee_id = "101"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(responses.GET, _get_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            get_referee(session, _SEASON_ID, _referee_id)


@responses.activate
def test_list_referees_uses_correct_endpoint(config: Config) -> None:
    """Verify that referees endpoint includes season_id in the path."""
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_payload(
            [
                {
                    "type": "referees",
                    "id": "101",
                    "attributes": {
                        "first_name": "John",
                        "last_name": "Smith",
                        "email_address": "john.smith@example.com",
                        "created_at": "2024-09-01T10:00:00Z",
                        "updated_at": "2024-09-01T10:00:00Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": "15020"}},
                    },
                },
            ],
        ),
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = list_referees(session, "15020")
    # API filters by season_id in URL path, so all results are for that season
    assert len(result) == 1
    assert result[0].id == "101"
    assert result[0].season_id == "15020"
    assert result[0].first_name == "John"
    assert result[0].last_name == "Smith"


@responses.activate
def test_create_referee_sends_correct_payload_with_all_fields(config: Config) -> None:

    responses.add(
        responses.POST,
        _ENDPOINT,
        json={
            "data": {
                "type": "referees",
                "id": "1146197",
                "attributes": {
                    "external_id": "0EB978DD-66B8-4CA1-AAA8-D855EED39D6A",
                    "first_name": "Wes",
                    "last_name": "McCauley",
                    "email_address": "Wes.McCauley@example.com",
                    "created_at": "2026-06-15T12:04:05.0325Z",
                    "updated_at": "2026-06-15T12:04:05.0325Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = create_referee(
            session,
            _SEASON_ID,
            "Wes",
            "McCauley",
            email_address="Wes.McCauley@example.com",
            external_id="0EB978DD-66B8-4CA1-AAA8-D855EED39D6A",
        )
    assert result.id == "1146197"
    assert result.first_name == "Wes"
    assert result.last_name == "McCauley"
    assert result.email == "Wes.McCauley@example.com"
    assert result.season_id == _SEASON_ID

    # Verify the request payload
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    import json

    assert req.body is not None
    payload = json.loads(req.body)
    assert payload["data"]["attributes"]["first_name"] == "Wes"
    assert payload["data"]["attributes"]["last_name"] == "McCauley"
    assert payload["data"]["attributes"]["email_address"] == "Wes.McCauley@example.com"
    assert payload["data"]["attributes"]["external_id"] == "0EB978DD-66B8-4CA1-AAA8-D855EED39D6A"


@responses.activate
def test_create_referee_sends_correct_payload_required_fields_only(
    config: Config,
) -> None:

    responses.add(
        responses.POST,
        _ENDPOINT,
        json={
            "data": {
                "type": "referees",
                "id": "1146198",
                "attributes": {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email_address": None,
                    "created_at": "2026-06-15T13:00:00Z",
                    "updated_at": "2026-06-15T13:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = create_referee(session, _SEASON_ID, "Jane", "Doe")
    assert result.id == "1146198"
    assert result.first_name == "Jane"
    assert result.last_name == "Doe"
    assert result.email is None

    # Verify the request payload
    import json

    req = responses.calls[0].request
    assert req.body is not None
    payload = json.loads(req.body)
    assert payload["data"]["attributes"]["first_name"] == "Jane"
    assert payload["data"]["attributes"]["last_name"] == "Doe"
    assert "email_address" not in payload["data"]["attributes"]
    assert "external_id" not in payload["data"]["attributes"]


@responses.activate
def test_create_referee_sends_bearer_and_jsonapi_headers(config: Config) -> None:

    responses.add(
        responses.POST,
        _ENDPOINT,
        json={
            "data": {
                "type": "referees",
                "id": "101",
                "attributes": {
                    "first_name": "Test",
                    "last_name": "Ref",
                    "created_at": "2024-09-01T10:00:00Z",
                    "updated_at": "2024-09-01T10:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        create_referee(session, _SEASON_ID, "Test", "Ref")
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == "application/vnd.api+json"
    assert req.headers["Content-Type"] == "application/vnd.api+json"


@responses.activate
def test_create_referee_401_raises_authentication_error(config: Config) -> None:

    responses.add(
        responses.POST,
        _ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            create_referee(session, _SEASON_ID, "Test", "Ref")


@responses.activate
def test_create_referee_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:

    responses.add(responses.POST, _ENDPOINT, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Season '.*' not found.*valid season ID.*seasons list --league-id",
        ):
            create_referee(session, _SEASON_ID, "Test", "Ref")


@responses.activate
def test_create_referee_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:

    responses.add(responses.POST, _ENDPOINT, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            create_referee(session, _SEASON_ID, "Test", "Ref")


@responses.activate
def test_update_referee_sends_correct_payload_all_fields(config: Config) -> None:
    _referee_id = "1146196"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _patch_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"

    # Mock GET request to fetch current data
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": "OLD-EXTERNAL-ID",
                    "first_name": "Wes",
                    "last_name": "McCauley",
                    "email_address": "wes@old.com",
                    "created_at": "2026-06-15T12:01:41.449299Z",
                    "updated_at": "2026-06-15T12:01:41.449299Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )

    # Mock PATCH request with updated data
    responses.add(
        responses.PATCH,
        _patch_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "external_id": "87487685-24B9-46EF-B8A3-D3B7ECEB1F68",
                    "first_name": "WES",
                    "last_name": "MCCAULEY",
                    "email_address": "McCauley.Wes@example.com",
                    "created_at": "2026-06-15T12:01:41.449299Z",
                    "updated_at": "2026-06-15T12:06:46.519767Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = update_referee(
            session,
            _SEASON_ID,
            _referee_id,
            first_name="WES",
            last_name="MCCAULEY",
            email_address="McCauley.Wes@example.com",
            external_id="87487685-24B9-46EF-B8A3-D3B7ECEB1F68",
        )
    assert result.id == _referee_id
    assert result.first_name == "WES"
    assert result.last_name == "MCCAULEY"
    assert result.email == "McCauley.Wes@example.com"
    assert result.season_id == _SEASON_ID

    # Verify we made both GET and PATCH requests
    assert len(responses.calls) == 2
    get_req = responses.calls[0].request
    patch_req = responses.calls[1].request
    assert get_req.method == "GET"
    assert patch_req.method == "PATCH"

    # Verify the PATCH request payload includes all fields
    import json

    assert patch_req.body is not None
    payload = json.loads(patch_req.body)
    assert payload["data"]["id"] == _referee_id
    assert payload["data"]["type"] == "referees"
    assert payload["data"]["attributes"]["first_name"] == "WES"
    assert payload["data"]["attributes"]["last_name"] == "MCCAULEY"
    assert payload["data"]["attributes"]["email_address"] == "McCauley.Wes@example.com"
    assert payload["data"]["attributes"]["external_id"] == "87487685-24B9-46EF-B8A3-D3B7ECEB1F68"


@responses.activate
def test_update_referee_sends_correct_payload_partial_fields(
    config: Config,
) -> None:
    _referee_id = "1146197"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _patch_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"

    # Mock GET request to fetch current data
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Original",
                    "last_name": "Name",
                    "email_address": "original@example.com",
                    "created_at": "2026-06-15T12:00:00Z",
                    "updated_at": "2026-06-15T12:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )

    # Mock PATCH request
    responses.add(
        responses.PATCH,
        _patch_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Updated",
                    "last_name": "Name",
                    "email_address": "original@example.com",
                    "created_at": "2026-06-15T12:00:00Z",
                    "updated_at": "2026-06-15T13:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = update_referee(
            session,
            _SEASON_ID,
            _referee_id,
            first_name="Updated",
        )
    assert result.id == _referee_id
    assert result.first_name == "Updated"
    assert result.last_name == "Name"
    assert result.email == "original@example.com"

    # Verify we made both GET and PATCH requests
    assert len(responses.calls) == 2

    # Verify the PATCH payload includes all required fields (from current + updates)
    import json

    patch_req = responses.calls[1].request
    assert patch_req.body is not None
    payload = json.loads(patch_req.body)
    assert payload["data"]["attributes"]["first_name"] == "Updated"
    assert payload["data"]["attributes"]["last_name"] == "Name"  # Preserved from current
    assert payload["data"]["attributes"]["email_address"] == "original@example.com"  # Preserved


@responses.activate
def test_update_referee_sends_bearer_and_jsonapi_headers(config: Config) -> None:
    _referee_id = "101"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    _patch_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"

    # Mock GET request
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Old",
                    "last_name": "Ref",
                    "created_at": "2024-09-01T10:00:00Z",
                    "updated_at": "2024-09-01T10:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )

    # Mock PATCH request
    responses.add(
        responses.PATCH,
        _patch_endpoint,
        json={
            "data": {
                "type": "referees",
                "id": _referee_id,
                "attributes": {
                    "first_name": "Test",
                    "last_name": "Ref",
                    "created_at": "2024-09-01T10:00:00Z",
                    "updated_at": "2024-09-01T10:00:00Z",
                },
                "relationships": {
                    "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                },
            },
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        update_referee(session, _SEASON_ID, _referee_id, first_name="Test")
    assert len(responses.calls) == 2
    get_req = responses.calls[0].request
    patch_req = responses.calls[1].request
    assert get_req.headers["Authorization"] == "Bearer test-token"
    assert get_req.headers["Accept"] == "application/vnd.api+json"
    assert patch_req.headers["Authorization"] == "Bearer test-token"
    assert patch_req.headers["Accept"] == "application/vnd.api+json"
    assert patch_req.headers["Content-Type"] == "application/vnd.api+json"


@responses.activate
def test_update_referee_401_raises_authentication_error(config: Config) -> None:
    _referee_id = "101"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # The GET request fails with 401
    responses.add(
        responses.GET,
        _get_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            update_referee(session, _SEASON_ID, _referee_id, first_name="Test")


@responses.activate
def test_update_referee_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    _referee_id = "nonexistent"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # The GET request fails with 404
    responses.add(responses.GET, _get_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Referee '.*' not found.*valid referee ID and season ID",
        ):
            update_referee(session, _SEASON_ID, _referee_id, first_name="Test")


@responses.activate
def test_update_referee_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    _referee_id = "101"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    # The GET request fails with 500
    responses.add(responses.GET, _get_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            update_referee(session, _SEASON_ID, _referee_id, first_name="Test")


@responses.activate
def test_delete_referee_success(config: Config) -> None:
    _referee_id = "1146197"
    _delete_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.DELETE,
        _delete_endpoint,
        status=204,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        # Should not raise
        delete_referee(session, _SEASON_ID, _referee_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.method == "DELETE"


@responses.activate
def test_delete_referee_sends_bearer_and_jsonapi_accept(config: Config) -> None:
    _referee_id = "101"
    _delete_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.DELETE,
        _delete_endpoint,
        status=204,
    )
    with Session(config) as session:
        session.set_bearer_token("test-token")
        delete_referee(session, _SEASON_ID, _referee_id)
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer test-token"
    assert req.headers["Accept"] == "application/vnd.api+json"


@responses.activate
def test_delete_referee_401_raises_authentication_error(config: Config) -> None:
    _referee_id = "101"
    _delete_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(
        responses.DELETE,
        _delete_endpoint,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )
    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            delete_referee(session, _SEASON_ID, _referee_id)


@responses.activate
def test_delete_referee_404_raises_gamesheet_error_with_helpful_message(
    config: Config,
) -> None:
    _referee_id = "nonexistent"
    _delete_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(responses.DELETE, _delete_endpoint, status=404, body="Not found")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Referee '.*' not found.*valid referee ID and season ID",
        ):
            delete_referee(session, _SEASON_ID, _referee_id)


@responses.activate
def test_delete_referee_other_failure_raises_gamesheet_error(
    config: Config,
) -> None:
    _referee_id = "101"
    _delete_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/referees/{_referee_id}"
    responses.add(responses.DELETE, _delete_endpoint, status=500, body="boom")
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            delete_referee(session, _SEASON_ID, _referee_id)
