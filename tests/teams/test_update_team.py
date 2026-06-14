"""Tests for update_team function."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
    update_team,
)

_BASE = "https://test.example"
_SEASON_ID = "15020"
_TEAM_ID = "521623"
_BFF_BASE = "https://bff-dashboard-api-awy26srzoa-nn.a.run.app"
_UPLOAD_URL_ENDPOINT = f"{_BFF_BASE}/dwg/assets/upload-url"
_GET_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}"
_UPDATE_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}"


def _mock_get_team() -> dict[str, Any]:
    """Return a sample GET response for the current team."""
    return {
        "data": {
            "type": "teams",
            "id": _TEAM_ID,
            "attributes": {
                "title": "Old Team Name",
                "external_id": "old-ext-id",
                "logo_url": "https://example.com/old-logo.png",
                "roster": {},
                "data": {"prototeam": "proto-123"},
                "created_at": "2026-06-13T18:00:00Z",
                "updated_at": "2026-06-13T18:00:00Z",
            },
            "relationships": {
                "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                "division": {"data": {"type": "divisions", "id": "80385"}},
            },
        },
    }


def _mock_update_response(**updates: str | None) -> dict[str, Any]:
    """Return a sample POST response with updated attributes."""
    attrs = {
        "title": updates.get("title", "Old Team Name"),
        "external_id": updates.get("external_id", "old-ext-id"),
        "logo_url": updates.get("logo_url", "https://example.com/old-logo.png"),
        "roster": {},
        "data": {"prototeam": "proto-123"},
        "created_at": "2026-06-13T18:00:00Z",
        "updated_at": "2026-06-13T19:00:00Z",
    }
    return {
        "data": {
            "type": "teams",
            "id": _TEAM_ID,
            "attributes": attrs,
            "relationships": {
                "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                "division": {"data": {"type": "divisions", "id": updates.get("division_id", "80385")}},
            },
        },
    }


@responses.activate
def test_update_team_title_only(config: Config) -> None:

    responses.add(responses.GET, _GET_ENDPOINT, json=_mock_get_team(), status=200)
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json=_mock_update_response(title="Updated Team Name"),
        status=200,
    )

    with Session(config) as session:
        session.set_bearer_token("abc")
        result = update_team(session, _SEASON_ID, _TEAM_ID, title="Updated Team Name")
    assert result.title == "Updated Team Name"
    assert result.id == _TEAM_ID

    # Verify the update request payload
    import json

    assert len(responses.calls) == 2  # GET + POST
    update_req = responses.calls[1].request
    assert update_req.body is not None
    payload = json.loads(update_req.body)
    assert payload["data"]["attributes"]["title"] == "Updated Team Name"
    assert payload["data"]["attributes"]["external_id"] == "old-ext-id"  # Preserved


@responses.activate
def test_update_team_division_id_only(config: Config) -> None:

    responses.add(responses.GET, _GET_ENDPOINT, json=_mock_get_team(), status=200)
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json=_mock_update_response(division_id="99999"),
        status=200,
    )

    with Session(config) as session:
        session.set_bearer_token("abc")
        result = update_team(session, _SEASON_ID, _TEAM_ID, division_id="99999")
    assert result.division_id == "99999"

    # Verify division_id in payload
    import json

    update_req = responses.calls[1].request
    assert update_req.body is not None
    payload = json.loads(update_req.body)
    assert payload["data"]["relationships"]["division"]["data"]["id"] == "99999"
    assert payload["data"]["attributes"]["title"] == "Old Team Name"  # Preserved


@responses.activate
def test_update_team_external_id_only(config: Config) -> None:

    responses.add(responses.GET, _GET_ENDPOINT, json=_mock_get_team(), status=200)
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json=_mock_update_response(external_id="new-ext-id"),
        status=200,
    )

    with Session(config) as session:
        session.set_bearer_token("abc")
        result = update_team(session, _SEASON_ID, _TEAM_ID, external_id="new-ext-id")
    assert result.id == _TEAM_ID

    # Verify external_id in payload
    import json

    update_req = responses.calls[1].request
    assert update_req.body is not None
    payload = json.loads(update_req.body)
    assert payload["data"]["attributes"]["external_id"] == "new-ext-id"


@responses.activate
def test_update_team_multiple_fields(config: Config) -> None:

    responses.add(responses.GET, _GET_ENDPOINT, json=_mock_get_team(), status=200)
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json=_mock_update_response(
            title="New Title",
            division_id="88888",
            external_id="custom-id",
        ),
        status=200,
    )

    with Session(config) as session:
        session.set_bearer_token("abc")
        result = update_team(
            session,
            _SEASON_ID,
            _TEAM_ID,
            title="New Title",
            division_id="88888",
            external_id="custom-id",
        )
    assert result.title == "New Title"
    assert result.division_id == "88888"

    # Verify all fields in payload
    import json

    update_req = responses.calls[1].request
    assert update_req.body is not None
    payload = json.loads(update_req.body)
    assert payload["data"]["attributes"]["title"] == "New Title"
    assert payload["data"]["relationships"]["division"]["data"]["id"] == "88888"
    assert payload["data"]["attributes"]["external_id"] == "custom-id"


@responses.activate
def test_update_team_with_logo(config: Config) -> None:
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"fake-image-data")
        logo_path = f.name

    try:
        responses.add(responses.GET, _GET_ENDPOINT, json=_mock_get_team(), status=200)

        # Mock upload URL request
        responses.add(
            responses.POST,
            _UPLOAD_URL_ENDPOINT,
            json={
                "status": "success",
                "data": {
                    "id": "new-image-id",
                    "uploadURL": "https://upload.example/new-image-id",
                },
            },
            status=200,
        )

        # Mock image upload
        responses.add(
            responses.POST,
            "https://upload.example/new-image-id",
            json={
                "success": True,
                "result": {
                    "id": "new-image-id",
                    "filename": "new.png",
                },
            },
            status=200,
        )

        # Mock team update
        new_logo_url = "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/new-image-id"
        responses.add(
            responses.PATCH,
            _UPDATE_ENDPOINT,
            json=_mock_update_response(logo_url=new_logo_url),
            status=200,
        )

        with Session(config) as session:
            session.set_bearer_token("abc")
            result = update_team(session, _SEASON_ID, _TEAM_ID, logo_path=logo_path)

        assert result.logo == new_logo_url

        # Verify all requests were made
        assert len(responses.calls) == 4  # GET + upload-url + upload + POST

        # Verify team update payload includes logo
        import json

        team_req = responses.calls[3].request
        assert team_req.body is not None
        payload = json.loads(team_req.body)
        assert payload["data"]["attributes"]["logo_url"] == new_logo_url

    finally:
        Path(logo_path).unlink()


@responses.activate
def test_update_team_remove_logo(config: Config) -> None:
    delete_logo_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}/logo"

    responses.add(responses.GET, _GET_ENDPOINT, json=_mock_get_team(), status=200)
    responses.add(responses.PATCH, _UPDATE_ENDPOINT, json=_mock_update_response(logo_url=None), status=200)
    responses.add(responses.DELETE, delete_logo_endpoint, status=204)

    with Session(config) as session:
        session.set_bearer_token("abc")
        result = update_team(session, _SEASON_ID, _TEAM_ID, remove_logo=True)
    assert result.logo is None

    # Verify logo is set to empty string in payload and DELETE was called
    import json

    assert len(responses.calls) == 3  # GET + PATCH + DELETE
    update_req = responses.calls[1].request
    assert update_req.body is not None
    payload = json.loads(update_req.body)
    assert payload["data"]["attributes"]["logo_url"] == ""


@responses.activate
def test_update_team_get_401_raises_authentication_error(config: Config) -> None:

    responses.add(responses.GET, _GET_ENDPOINT, json={"errors": [{"detail": "Token expired"}]}, status=401)

    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            update_team(session, _SEASON_ID, _TEAM_ID, title="New Title")


@responses.activate
def test_update_team_get_404_raises_gamesheet_error(config: Config) -> None:

    responses.add(responses.GET, _GET_ENDPOINT, status=404, body="Not found")

    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=r"Team '.*' not found.*valid team ID.*teams list --season-id",
        ):
            update_team(session, _SEASON_ID, _TEAM_ID, title="New Title")


@responses.activate
def test_update_team_get_500_raises_gamesheet_error(config: Config) -> None:

    responses.add(responses.GET, _GET_ENDPOINT, status=500, body="Internal error")

    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            update_team(session, _SEASON_ID, _TEAM_ID, title="New Title")


@responses.activate
def test_update_team_post_401_raises_authentication_error(config: Config) -> None:

    responses.add(responses.GET, _GET_ENDPOINT, json=_mock_get_team(), status=200)
    responses.add(
        responses.PATCH,
        _UPDATE_ENDPOINT,
        json={"errors": [{"detail": "Token expired"}]},
        status=401,
    )

    with Session(config) as session:
        session.set_bearer_token("stale")
        with pytest.raises(AuthenticationError, match="HTTP 401"):
            update_team(session, _SEASON_ID, _TEAM_ID, title="New Title")


@responses.activate
def test_update_team_post_404_raises_gamesheet_error(config: Config) -> None:

    responses.add(responses.GET, _GET_ENDPOINT, json=_mock_get_team(), status=200)
    responses.add(responses.PATCH, _UPDATE_ENDPOINT, status=404, body="Not found")

    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match=r"Team '.*' not found"):
            update_team(session, _SEASON_ID, _TEAM_ID, title="New Title")


@responses.activate
def test_update_team_other_failure_raises_gamesheet_error(config: Config) -> None:

    responses.add(responses.GET, _GET_ENDPOINT, json=_mock_get_team(), status=200)
    responses.add(responses.PATCH, _UPDATE_ENDPOINT, status=500, body="boom")

    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="HTTP 500"):
            update_team(session, _SEASON_ID, _TEAM_ID, title="New Title")


def test_update_team_no_fields_raises_value_error(config: Config) -> None:

    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(ValueError, match="At least one field must be provided"):
            update_team(session, _SEASON_ID, _TEAM_ID)


def test_update_team_both_logo_and_remove_logo_raises_value_error(config: Config) -> None:
    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"fake-image-data")
        logo_path = f.name

    try:
        with Session(config) as session:
            session.set_bearer_token("abc")
            with pytest.raises(ValueError, match="Cannot both upload a logo and remove it"):
                update_team(session, _SEASON_ID, _TEAM_ID, logo_path=logo_path, remove_logo=True)
    finally:
        Path(logo_path).unlink()


@responses.activate
def test_update_team_delete_logo_failure_raises_gamesheet_error(config: Config) -> None:
    delete_logo_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}/logo"

    responses.add(responses.GET, _GET_ENDPOINT, json=_mock_get_team(), status=200)
    responses.add(responses.PATCH, _UPDATE_ENDPOINT, json=_mock_update_response(logo_url=None), status=200)
    responses.add(responses.DELETE, delete_logo_endpoint, status=500, body="Server error")

    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(GameSheetError, match="DELETE.*HTTP 500"):
            update_team(session, _SEASON_ID, _TEAM_ID, remove_logo=True)
