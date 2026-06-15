"""GameSheet referees: officials assigned to games within a season.

A referee is an official who can be assigned to games within a season. Each referee belongs to exactly one
season. The dashboard displays referees after navigating into a season view. This module talks to the
GameSheet JSON:API at ``/api/seasons/{season_id}/referees`` directly with the lightweight
:class:`gamesheet_sdk.Session` path -- no Playwright needed for read-only access once a bearer token has been
obtained (typically by reading the SPA's ``accessToken`` from the saved browser storage state via
:func:`gamesheet_sdk.auth.load_access_token`).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session
_JSONAPI_CONTENT_TYPE = "application/vnd.api+json"


class Referee(BaseModel):
    """A single referee.

    Maps the ``data[*]`` items in the JSON:API response of ``GET /api/seasons/{season_id}/referees`` to a flat
    typed model.
    """

    id: str = Field(description="Referee identifier (string in JSON:API).")
    season_id: str = Field(description="Parent season identifier.")
    first_name: str = Field(description="Referee's first name.")
    last_name: str = Field(description="Referee's last name.")
    email: str | None = Field(default=None, description="Referee's email address.")
    external_id: str | None = Field(default=None, description="External identifier for the referee.")
    created_at: datetime = Field(description="When the referee was created.")
    updated_at: datetime = Field(description="Last time the referee was updated.")


class RefereeReport(BaseModel):
    """A referee report with career statistics and games officiated.

    Maps the response from ``GET /api/reports/referees/{external_id}`` to a typed model.
    """

    external_id: str = Field(description="External referee identifier.")
    first_name: str = Field(description="Referee's first name.")
    last_name: str = Field(description="Referee's last name.")
    games_refereed: int = Field(description="Total number of games refereed.")
    average_pim_per_game: float = Field(description="Average penalties in minutes per game.")
    most_frequent_penalty: str | None = Field(
        default=None,
        description="Most frequently assessed penalty type.",
    )
    major_penalties_count: int = Field(description="Number of major penalties assessed.")
    games: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of games officiated.",
    )
    major_penalties: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of major and misconduct penalties.",
    )


def _parse(item: dict[str, Any]) -> Referee:
    """Flatten a JSON:API resource object into a :class:`Referee`."""
    attrs = item.get("attributes", {})
    # Extract season_id from relationships
    season_id = item.get("relationships", {}).get("season", {}).get("data", {}).get("id", "")
    return Referee(
        id=item["id"],
        season_id=season_id,
        first_name=attrs.get("first_name", ""),
        last_name=attrs.get("last_name", ""),
        email=attrs.get("email_address"),
        external_id=attrs.get("external_id"),
        created_at=attrs["created_at"],
        updated_at=attrs["updated_at"],
    )


def get_referee(session: Session, season_id: str, referee_id: str) -> Referee:
    """Get a single referee by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier containing the referee.
    :type season_id: str
    :param referee_id: The referee identifier to retrieve.
    :type referee_id: str
    :returns: The :class:`Referee` with the specified ID.
    :rtype: Referee
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    endpoint = f"/api/seasons/{season_id}/referees/{referee_id}"
    response = session.get(
        endpoint,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
    )

    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:
        _err_msg = (
            f"Referee '{referee_id}' not found in season '{season_id}' (HTTP 404). "
            f"Make sure you're using a valid referee ID and season ID.",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)

    body: dict[str, Any] = response.json()
    return _parse(body["data"])


def get_referee_report(
    session: Session,
    season_id: str,
    referee_id: str,
) -> RefereeReport:
    """Get a comprehensive referee report with statistics and games.

    This function fetches the full referee report including career statistics and games officiated. It first
    retrieves the referee to get their external_id, then fetches the report.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier containing the referee.
    :type season_id: str
    :param referee_id: The referee identifier to retrieve the report for.
    :type referee_id: str
    :returns: The :class:`RefereeReport` with statistics and games.
    :rtype: RefereeReport
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response, or if the referee has no external_id.
    """
    # First, get the referee to obtain the external_id
    referee = get_referee(session, season_id, referee_id)

    if not referee.external_id:
        _err_msg = (
            f"Referee '{referee_id}' does not have an external_id set. "
            f"Cannot fetch report without external_id."
        )
        raise GameSheetError(_err_msg)

    # Now fetch the report using the external_id
    endpoint = f"/api/reports/referees/{referee.external_id}"
    response = session.get(endpoint)

    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again."
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:
        _err_msg = (
            f"Report not found for referee with external_id '{referee.external_id}' (HTTP 404). "
            f"The referee may not have officiated any games yet."
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}"
        raise GameSheetError(_err_msg)

    body: dict[str, Any] = response.json()

    # Parse the report response
    # The structure may vary, so we'll extract what we can
    return RefereeReport(
        external_id=referee.external_id,
        first_name=referee.first_name,
        last_name=referee.last_name,
        games_refereed=body.get("gamesRefereed", 0),
        average_pim_per_game=body.get("averagePimPerGame", 0.0),
        most_frequent_penalty=body.get("mostFrequentPenalty"),
        major_penalties_count=body.get("majorPenaltiesCount", 0),
        games=body.get("games", []),
        major_penalties=body.get("majorPenalties", []),
    )


# pylint: disable-next=too-many-positional-arguments
def create_referee(
    session: Session,
    season_id: str,
    first_name: str,
    last_name: str,
    email_address: str | None = None,
    external_id: str | None = None,
) -> Referee:
    """Create a new referee in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier in which to create the referee.
    :type season_id: str
    :param first_name: Referee's first name.
    :type first_name: str
    :param last_name: Referee's last name.
    :type last_name: str
    :param email_address: Optional email address for the referee.
    :type email_address: str | None
    :param external_id: Optional external identifier for the referee.
    :type external_id: str | None
    :returns: The newly created :class:`Referee`.
    :rtype: Referee
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    endpoint = f"/api/seasons/{season_id}/referees"
    attributes: dict[str, Any] = {
        "first_name": first_name,
        "last_name": last_name,
    }
    if email_address is not None:
        attributes["email_address"] = email_address
    if external_id is not None:
        attributes["external_id"] = external_id

    payload = {"data": {"attributes": attributes}}
    response = session.post(
        endpoint,
        json=payload,
        headers={
            "Accept": _JSONAPI_CONTENT_TYPE,
            "Content-Type": _JSONAPI_CONTENT_TYPE,
        },
    )
    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:
        _err_msg = (
            f"Season '{season_id}' not found (HTTP 404). "
            f"Make sure you're using a valid season ID. "
            f"To get valid season IDs, run: gamesheet-sdk-py seasons list --league-id <LEAGUE_ID>",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = (f"POST {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    return _parse(body["data"])


# pylint: disable-next=too-many-positional-arguments,too-many-locals
def update_referee(
    session: Session,
    season_id: str,
    referee_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    email_address: str | None = None,
    external_id: str | None = None,
) -> Referee:
    """Update an existing referee in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    At least one field must be provided to update. The API requires sending the full referee data, so this
    function first fetches the current referee to preserve unchanged fields.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier containing the referee.
    :type season_id: str
    :param referee_id: The referee identifier to update.
    :type referee_id: str
    :param first_name: Optional updated first name.
    :type first_name: str | None
    :param last_name: Optional updated last name.
    :type last_name: str | None
    :param email_address: Optional updated email address.
    :type email_address: str | None
    :param external_id: Optional updated external identifier.
    :type external_id: str | None
    :returns: The updated :class:`Referee`.
    :rtype: Referee
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    # Fetch current referee data to get all fields
    get_endpoint = f"/api/seasons/{season_id}/referees/{referee_id}"
    get_response = session.get(
        get_endpoint,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
    )

    if get_response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if get_response.status_code == 404:
        _err_msg = (
            f"Referee '{referee_id}' not found in season '{season_id}' (HTTP 404). "
            f"Make sure you're using a valid referee ID and season ID.",
        )
        raise GameSheetError(_err_msg)
    if get_response.status_code >= 400:
        _err_msg = (
            f"GET {get_endpoint} returned HTTP {get_response.status_code}: {get_response.text[:200]!r}",
        )
        raise GameSheetError(_err_msg)

    current_attrs = get_response.json().get("data", {}).get("attributes", {})

    # Build updated attributes, preserving current values for unchanged fields
    attributes: dict[str, Any] = {
        "first_name": first_name if first_name is not None else current_attrs.get("first_name", ""),
        "last_name": last_name if last_name is not None else current_attrs.get("last_name", ""),
    }

    # Handle optional fields - only include if they exist in current data or being updated
    if email_address is not None:
        attributes["email_address"] = email_address
    elif "email_address" in current_attrs:
        attributes["email_address"] = current_attrs["email_address"]

    if external_id is not None:
        attributes["external_id"] = external_id
    elif "external_id" in current_attrs:
        attributes["external_id"] = current_attrs["external_id"]

    # Now send the PATCH request with complete data
    patch_endpoint = f"/api/seasons/{season_id}/referees/{referee_id}"
    payload = {
        "data": {
            "id": referee_id,
            "type": "referees",
            "attributes": attributes,
        },
    }
    response = session.patch(
        patch_endpoint,
        json=payload,
        headers={
            "Accept": _JSONAPI_CONTENT_TYPE,
            "Content-Type": _JSONAPI_CONTENT_TYPE,
        },
    )
    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:
        _err_msg = (
            f"Referee '{referee_id}' not found in season '{season_id}' (HTTP 404). "
            f"Make sure you're using a valid referee ID and season ID.",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = (f"PATCH {patch_endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    return _parse(body["data"])


def delete_referee(
    session: Session,
    season_id: str,
    referee_id: str,
) -> None:
    """Delete a referee.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier containing the referee.
    :type season_id: str
    :param referee_id: The referee identifier to delete.
    :type referee_id: str
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    endpoint = f"/api/seasons/{season_id}/referees/{referee_id}"

    response = session.delete(
        endpoint,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
    )

    if response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again."
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:
        _err_msg = (
            f"Referee '{referee_id}' not found in season '{season_id}' (HTTP 404). "
            f"Make sure you're using a valid referee ID and season ID."
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:
        _err_msg = f"DELETE {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}"
        raise GameSheetError(_err_msg)


def list_referees(session: Session, season_id: str) -> list[Referee]:
    """Return every referee in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :type session: Session
    :param season_id: The season identifier whose referees to list.
    :type season_id: str
    :returns: A list of :class:`Referee`, in the order the server returned them. The list may be empty if the
        season has no referees.
    :rtype: list[Referee]
    :raises AuthenticationError: If the server returns 401 (the bearer is missing, malformed, or expired --
        run ``gamesheet-sdk-py login`` to refresh).
    :raises GameSheetError: For any other non-2xx response.
    """
    endpoint = f"/api/seasons/{season_id}/referees"
    response = session.get(
        endpoint,
        headers={"Accept": _JSONAPI_CONTENT_TYPE},
    )
    if response.status_code == 401:

        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if response.status_code == 404:

        _err_msg = (
            f"Season '{season_id}' not found (HTTP 404). "
            f"Make sure you're using a valid season ID. "
            f"To get valid season IDs, run: gamesheet-sdk-py seasons list --league-id <LEAGUE_ID>",
        )
        raise GameSheetError(_err_msg)
    if response.status_code >= 400:

        _err_msg = (f"GET {endpoint} returned HTTP {response.status_code}: {response.text[:200]!r}",)
        raise GameSheetError(_err_msg)
    body: dict[str, Any] = response.json()
    return [_parse(item) for item in body.get("data", [])]
