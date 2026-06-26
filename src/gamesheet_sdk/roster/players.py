"""Player roster operations."""  # pylint: disable=too-many-lines

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Any

from gamesheet_sdk.constants import BFF_API_BASE_URL, CLOUDFLARE_IMAGE_DELIVERY_BASE
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.roster.helpers import get_team_for_roster_update, update_team_roster
from gamesheet_sdk.roster.models import Player, parse_player
from gamesheet_sdk.shared import JSONAPI_HEADERS, handle_response

if TYPE_CHECKING:
    from gamesheet_sdk.session import Session


def get_player(session: Session, season_id: str, player_id: str) -> Player:
    """Get a single player by ID.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The parent season identifier.
    :param player_id: The player identifier to retrieve.
    :returns: The :class:`Player` with the specified ID.
    :rtype: Player
    """
    endpoint = f"/api/seasons/{season_id}/players/{player_id}"
    response = session.get(endpoint, headers=JSONAPI_HEADERS)
    handle_response(response, endpoint, "GET player")
    body: dict[str, Any] = response.json()
    return parse_player(body["data"])


def list_players(session: Session, season_id: str) -> list[Player]:
    """Return every player in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier whose players to list.
    :returns: A list of :class:`Player`, in the order the server returned them. The list may be empty if the
        season has no players.
    :rtype: list[Player]
    """
    endpoint = f"/api/seasons/{season_id}/players"
    response = session.get(endpoint, headers=JSONAPI_HEADERS, params={"include": "teams,divisions"})
    handle_response(response, endpoint, "GET players")
    body: dict[str, Any] = response.json()
    # Parse all players
    all_players = [parse_player(item) for item in body.get("data", [])]
    return all_players


def list_team_players(session: Session, season_id: str, team_id: str) -> list[Player]:
    """Return every player for the specified team.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier whose players to list.
    :returns: A list of :class:`Player`, in the order the server returned them. The list may be empty if the
        team has no players.
    :rtype: list[Player]
    """
    endpoint = f"/api/seasons/{season_id}/teams/{team_id}"
    response = session.get(endpoint, headers=JSONAPI_HEADERS, params={"include": "players,coaches"})
    handle_response(response, endpoint, "GET team")
    body: dict[str, Any] = response.json()
    included_players = {
        item["id"]: item
        for item in body.get(
            "included",
            [],
        )
        if item.get("type") == "players"
    }
    roster_metadata = {
        str(p["id"]): p
        for p in body.get("data", {}).get("attributes", {}).get("roster", {}).get("players", [])
    }
    players = []
    for player_id, player_data in included_players.items():
        player = parse_player(player_data)
        if player_id in roster_metadata:
            metadata = roster_metadata[player_id]
            player.number = metadata.get("number")
            player.position = metadata.get("position")
            player.duty = metadata.get("duty")
            # designation is stored as "duty" in the roster
            # Map back: "captain" -> "Captain", "alternate_captain" -> "Alternate Captain"
            if player.duty:
                player.designation = player.duty.replace("_", " ").title()
            player.status = metadata.get("status")
            player.starting = metadata.get("starting")
            player.added_at_game_time = metadata.get("added_at_game_time")
            player.affiliated = metadata.get("affiliated")
        players.append(player)
    return players


def _upload_photo(session: Session, photo_path: str) -> str:
    """Upload a photo image and return its URL."""
    photo_file_path = Path(photo_path)
    if not photo_file_path.exists():
        _err_msg = (f"Photo file not found: {photo_path}",)
        raise GameSheetError(_err_msg)
    mime_type, _ = mimetypes.guess_type(photo_path)
    if not mime_type or not mime_type.startswith("image/"):
        _err_msg = (f"Invalid image file: {photo_path}",)
        raise GameSheetError(_err_msg)
    upload_url_endpoint = f"{BFF_API_BASE_URL}/dwg/assets/upload-url"
    upload_url_response = session.post(upload_url_endpoint)
    if upload_url_response.status_code == 401:
        _err_msg = (
            "Access token rejected (HTTP 401). Likely expired; re-run "
            "`gamesheet-sdk-py login` to refresh and try again.",
        )
        raise AuthenticationError(_err_msg)
    if upload_url_response.status_code >= 400:
        _err_msg = (
            f"POST {upload_url_endpoint} returned HTTP {upload_url_response.status_code}: "
            f"{upload_url_response.text[:200]!r}",
        )
        raise GameSheetError(_err_msg)
    upload_data: dict[str, Any] = upload_url_response.json()
    if upload_data.get("status") != "success":
        _err_msg = (f"Failed to get upload URL: {upload_data}",)
        raise GameSheetError(_err_msg)
    upload_url: str = upload_data["data"]["uploadURL"]
    image_id: str = upload_data["data"]["id"]
    with photo_file_path.open("rb") as f:
        upload_response = session.post(
            upload_url,
            files={"file": (photo_file_path.name, f, mime_type)},
        )
    if upload_response.status_code >= 400:
        _err_msg = (
            f"POST {upload_url} returned HTTP {upload_response.status_code}: "
            f"{upload_response.text[:200]!r}",
        )
        raise GameSheetError(_err_msg)
    upload_result: dict[str, Any] = upload_response.json()
    if not upload_result.get("success"):
        _err_msg = (f"Failed to upload photo: {upload_result}",)
        raise GameSheetError(_err_msg)
    return f"{CLOUDFLARE_IMAGE_DELIVERY_BASE}/{image_id}"


def create_player(  # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
    session: Session,
    season_id: str,
    first_name: str,
    last_name: str,
    *,
    external_id: str | None = None,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
    team_id: str | None = None,
    biography: str | None = None,
    height: str | None = None,
    weight: str | None = None,
    shot_hand: str | None = None,
    birthdate: str | None = None,
    hometown: str | None = None,
    country: str | None = None,
    province: str | None = None,
    drafted_by: str | None = None,
    committed_to: str | None = None,
    photo_path: str | None = None,
) -> Player:
    r"""Create a new player in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier to create the player in.
    :param first_name: Player's first name.
    :param last_name: Player's last name.
    :param external_id: Optional external identifier for the player.
    :param jersey: Optional jersey number.
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :param status: Optional status (Regular, Affiliated, etc.).
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :param team_id: Optional team identifier to associate the player with.
    :param biography: Optional biography text.
    :param height: Optional height (e.g., "6'2\"").
    :param weight: Optional weight (e.g., "185").
    :param shot_hand: Optional shooting hand (left, right).
    :param birthdate: Optional birthdate (ISO format: YYYY-MM-DD).
    :param hometown: Optional hometown.
    :param country: Optional country code (e.g., "US", "CA").
    :param province: Optional province/state.
    :param drafted_by: Optional drafted by team name.
    :param committed_to: Optional committed to institution.
    :param photo_path: Optional path to a local photo image file.
    :returns: The created :class:`Player`.
    :rtype: Player
    """
    photo_url: str | None = None
    if photo_path:
        photo_url = _upload_photo(session, photo_path)
    endpoint = f"/api/seasons/{season_id}/players"
    payload: dict[str, Any] = {
        "data": {
            "type": "players",
            "attributes": {
                "first_name": first_name,
                "last_name": last_name,
            },
        },
    }
    attrs = payload["data"]["attributes"]
    if external_id:
        attrs["external_id"] = external_id
    if jersey:
        attrs["jersey"] = jersey
    if position:
        attrs["position"] = position
    if status:
        attrs["status"] = status
    if designation:
        attrs["designation"] = designation
    if biography:
        attrs["biography"] = biography
    if height:
        attrs["height"] = height
    if weight:
        attrs["weight"] = weight
    if shot_hand:
        attrs["shot_hand"] = shot_hand
    if birthdate:
        attrs["birthdate"] = birthdate
    if hometown:
        attrs["hometown"] = hometown
    if country:
        attrs["country"] = country
    if province:
        attrs["province"] = province
    if drafted_by:
        attrs["drafted_by"] = drafted_by
    if committed_to:
        attrs["committed_to"] = committed_to
    if photo_url:
        attrs["photo_url"] = photo_url
    if team_id:
        payload["data"]["relationships"] = {
            "teams": {"data": [{"type": "teams", "id": team_id}]},
        }
    response = session.post(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "POST player")
    body: dict[str, Any] = response.json()
    return parse_player(body["data"])


def get_team_player(session: Session, season_id: str, team_id: str, player_id: str) -> Player:
    """Get a single player from a team's roster.

    This function retrieves team roster metadata (number, position, status, etc.) that is only available in
    the team context, unlike :func:`get_player` which fetches from the season-level players endpoint without
    roster metadata.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.

    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier.
    :param player_id: The player identifier to retrieve.
    :returns: The :class:`Player` with team roster metadata populated.
    :rtype: Player
    :raises GameSheetError: If the player is not found on the team's roster.
    """
    players = list_team_players(session, season_id, team_id)
    for player in players:
        if player.id == player_id:
            return player
    msg = f"Player {player_id} not found on team {team_id}"
    raise GameSheetError(msg)


def _build_player_roster_entry(
    player_id: str,
    *,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
) -> dict[str, Any]:
    """Build a player roster entry dict for team roster updates."""
    entry: dict[str, Any] = {
        "id": player_id,
        "affiliated": False,
        "status": "playing",
        "starting": False,
        "added_at_game_time": False,
    }
    if jersey:
        entry["number"] = jersey
    if position:
        entry["position"] = position.lower()
    if status:
        status_map = {"Regular": "playing", "Affiliated": "affiliated"}
        entry["status"] = status_map.get(status, status.lower())
        if status == "Affiliated":
            entry["affiliated"] = True
    if designation:
        entry["duty"] = designation.lower().replace(" ", "_")
    return entry


def _populate_player_metadata(
    player: Player,
    *,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
) -> None:
    """Populate player object with roster metadata."""
    if jersey:
        player.number = jersey
    if position:
        player.position = position
    if status:
        player.status = status
    if designation:
        player.designation = designation


def create_team_player(  # pylint: disable=too-many-arguments,too-many-locals,too-many-statements
    session: Session,
    season_id: str,
    team_id: str,
    first_name: str,
    last_name: str,
    *,
    external_id: str | None = None,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
    biography: str | None = None,
    height: str | None = None,
    weight: str | None = None,
    shot_hand: str | None = None,
    birthdate: str | None = None,
    hometown: str | None = None,
    country: str | None = None,
    province: str | None = None,
    drafted_by: str | None = None,
    committed_to: str | None = None,
    photo_path: str | None = None,
) -> Player:
    r"""Create a new player and add to the specified team's roster.

    This function performs two operations: (1) creates the player at the season level,
    (2) updates the team's roster to include the new player with position and other metadata.
    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier to add the player to.
    :param first_name: Player's first name.
    :param last_name: Player's last name.
    :param external_id: Optional external identifier for the player.
    :param jersey: Optional jersey number.
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :param status: Optional status (Regular, Affiliated, etc.).
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :param biography: Optional biography text.
    :param height: Optional height (e.g., "6'2\"").
    :param weight: Optional weight (e.g., "185").
    :param shot_hand: Optional shooting hand (left, right).
    :param birthdate: Optional birthdate (ISO format: YYYY-MM-DD).
    :param hometown: Optional hometown.
    :param country: Optional country code (e.g., "US", "CA").
    :param province: Optional province/state.
    :param drafted_by: Optional drafted by team name.
    :param committed_to: Optional committed to institution.
    :param photo_path: Optional path to a local photo image file.
    :returns: The created :class:`Player`.
    :rtype: Player
    """
    photo_url: str | None = None
    if photo_path:
        photo_url = _upload_photo(session, photo_path)
    # Step 1: Create the player at the season level (without "type" field for team context)
    endpoint = f"/api/seasons/{season_id}/players"
    payload: dict[str, Any] = {"data": {"attributes": {"first_name": first_name, "last_name": last_name}}}
    attrs = payload["data"]["attributes"]
    if external_id:
        attrs["external_id"] = external_id
    if biography:
        attrs["biography"] = biography
    if height:
        attrs["height"] = height
    if weight:
        attrs["weight"] = weight
    if shot_hand:
        attrs["shot_hand"] = shot_hand
    if birthdate:
        attrs["birthdate"] = birthdate
    if hometown:
        attrs["hometown"] = hometown
    if country:
        attrs["country"] = country
    if province:
        attrs["province"] = province
    if drafted_by:
        attrs["drafted_by"] = drafted_by
    if committed_to:
        attrs["committed_to"] = committed_to
    if photo_url:
        attrs["photo_url"] = photo_url
    response = session.post(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "POST player")
    player = parse_player(response.json()["data"])
    # Step 2: Fetch current team data and update roster
    team_data = get_team_for_roster_update(session, season_id, team_id)
    roster = team_data.get("data", {}).get("attributes", {}).get("roster", {})
    players_roster = roster.get("players", [])
    players_roster.append(
        _build_player_roster_entry(
            player.id,
            jersey=jersey,
            position=position,
            status=status,
            designation=designation,
        ),
    )
    roster["players"] = players_roster
    # Step 3: Update team roster
    update_team_roster(
        session,
        season_id,
        team_id,
        roster,
        team_data.get("data", {}).get("attributes", {}),
        team_data.get("data", {}).get("relationships", {}),
    )
    _populate_player_metadata(
        player,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )
    return player


def update_player(  # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
    session: Session,
    season_id: str,
    player_id: str,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    external_id: str | None = None,
    biography: str | None = None,
    height: str | None = None,
    weight: str | None = None,
    shot_hand: str | None = None,
    birthdate: str | None = None,
    hometown: str | None = None,
    country: str | None = None,
    province: str | None = None,
    drafted_by: str | None = None,
    committed_to: str | None = None,
    photo_path: str | None = None,
    remove_photo: bool = False,
) -> Player:
    r"""Update an existing player in the specified season.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401. At least one field
    must be provided for update.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier containing the player.
    :param player_id: The player identifier to update.
    :param first_name: Optional updated first name.
    :param last_name: Optional updated last name.
    :param external_id: Optional updated external identifier.
    :param biography: Optional updated biography text.
    :param height: Optional updated height (e.g., "6'2\"").
    :param weight: Optional updated weight (e.g., "185").
    :param shot_hand: Optional updated shooting hand (left, right).
    :param birthdate: Optional updated birthdate (ISO format: YYYY-MM-DD).
    :param hometown: Optional updated hometown.
    :param country: Optional updated country code (e.g., "US", "CA").
    :param province: Optional updated province/state.
    :param drafted_by: Optional updated drafted by team name.
    :param committed_to: Optional updated committed to institution.
    :param photo_path: Optional path to a new photo image file.
    :param remove_photo: If True, remove the player's photo.
    :returns: The updated :class:`Player`.
    :rtype: Player
    :raises ValueError: If no fields are provided for update or both photo_path and remove_photo are set.
    """
    if all(
        v is None or v is False
        for v in (
            first_name,
            last_name,
            external_id,
            biography,
            height,
            weight,
            shot_hand,
            birthdate,
            hometown,
            country,
            province,
            drafted_by,
            committed_to,
            photo_path,
            remove_photo,
        )
    ):
        msg = "At least one field must be provided for update"
        raise ValueError(msg)
    if photo_path and remove_photo:
        msg = "Cannot both upload a photo and remove it"
        raise ValueError(msg)
    # Handle photo upload/removal
    photo_url: str | None = None
    if photo_path:
        photo_url = _upload_photo(session, photo_path)
    # Fetch current player to get all fields
    current_player = get_player(session, season_id, player_id)
    # Build payload with updated values, preserving current for unchanged fields
    payload: dict[str, Any] = {
        "data": {
            "id": player_id,
            "type": "players",
            "attributes": {
                "first_name": first_name if first_name is not None else current_player.first_name,
                "last_name": last_name if last_name is not None else current_player.last_name,
            },
        },
    }
    attrs = payload["data"]["attributes"]
    # Handle optional fields
    if external_id is not None:  # pragma: no cover
        attrs["external_id"] = external_id  # pragma: no cover
    elif current_player.external_id:  # pragma: no cover
        attrs["external_id"] = current_player.external_id  # pragma: no cover
    if biography is not None:  # pragma: no cover
        attrs["biography"] = biography  # pragma: no cover
    elif current_player.biography:  # pragma: no cover
        attrs["biography"] = current_player.biography  # pragma: no cover
    if height is not None:  # pragma: no cover
        attrs["height"] = height  # pragma: no cover
    elif current_player.height:  # pragma: no cover
        attrs["height"] = current_player.height  # pragma: no cover
    if weight is not None:  # pragma: no cover
        attrs["weight"] = weight  # pragma: no cover
    elif current_player.weight:  # pragma: no cover
        attrs["weight"] = current_player.weight  # pragma: no cover
    if shot_hand is not None:  # pragma: no cover
        attrs["shot_hand"] = shot_hand  # pragma: no cover
    elif current_player.shot_hand:  # pragma: no cover
        attrs["shot_hand"] = current_player.shot_hand  # pragma: no cover
    if birthdate is not None:  # pragma: no cover
        attrs["birthdate"] = birthdate  # pragma: no cover
    elif current_player.birthdate:  # pragma: no cover
        attrs["birthdate"] = str(current_player.birthdate)  # pragma: no cover
    if hometown is not None:  # pragma: no cover
        attrs["hometown"] = hometown  # pragma: no cover
    elif current_player.hometown:  # pragma: no cover
        attrs["hometown"] = current_player.hometown  # pragma: no cover
    if country is not None:  # pragma: no cover
        attrs["country"] = country  # pragma: no cover
    elif current_player.country:  # pragma: no cover
        attrs["country"] = current_player.country  # pragma: no cover
    if province is not None:  # pragma: no cover
        attrs["province"] = province  # pragma: no cover
    elif current_player.province:  # pragma: no cover
        attrs["province"] = current_player.province  # pragma: no cover
    if drafted_by is not None:  # pragma: no cover
        attrs["drafted_by"] = drafted_by  # pragma: no cover
    elif current_player.drafted_by:  # pragma: no cover
        attrs["drafted_by"] = current_player.drafted_by  # pragma: no cover
    if committed_to is not None:  # pragma: no cover
        attrs["committed_to"] = committed_to  # pragma: no cover
    elif current_player.committed_to:  # pragma: no cover
        attrs["committed_to"] = current_player.committed_to  # pragma: no cover
    # Handle photo # pragma: no cover
    if photo_url:  # pragma: no cover
        attrs["photo_url"] = photo_url  # pragma: no cover
    elif remove_photo:  # pragma: no cover
        attrs["photo_url"] = ""  # pragma: no cover
    elif current_player.photo_url:  # pragma: no cover
        attrs["photo_url"] = current_player.photo_url  # pragma: no cover
    endpoint = f"/api/seasons/{season_id}/players/{player_id}"
    response = session.patch(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "PATCH player")
    body: dict[str, Any] = response.json()
    return parse_player(body["data"])


def update_team_player(
    session: Session,
    season_id: str,
    team_id: str,
    player_id: str,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    external_id: str | None = None,
    biography: str | None = None,
    height: str | None = None,
    weight: str | None = None,
    shot_hand: str | None = None,
    birthdate: str | None = None,
    hometown: str | None = None,
    country: str | None = None,
    province: str | None = None,
    drafted_by: str | None = None,
    committed_to: str | None = None,
    photo_path: str | None = None,
    remove_photo: bool = False,
) -> Player:
    # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
    r"""Update a player for a specific team.

    This function updates the player at the season level. The supplied :class:`Session` must already carry a
    bearer token (e.g. via :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will
    401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier.
    :param player_id: The player identifier to update.
    :param first_name: Optional updated first name.
    :param last_name: Optional updated last name.
    :param external_id: Optional updated external identifier.
    :param biography: Optional updated biography text.
    :param height: Optional updated height (e.g., "6'2\"").
    :param weight: Optional updated weight (e.g., "185").
    :param shot_hand: Optional updated shooting hand (left, right).
    :param birthdate: Optional updated birthdate (ISO format: YYYY-MM-DD).
    :param hometown: Optional updated hometown.
    :param country: Optional updated country code (e.g., "US", "CA").
    :param province: Optional updated province/state.
    :param drafted_by: Optional updated drafted by team name.
    :param committed_to: Optional updated committed to institution.
    :param photo_path: Optional path to a new photo image file.
    :param remove_photo: If True, remove the player's photo.
    :returns: The updated :class:`Player`.
    :rtype: Player
    :raises ValueError: If no fields are provided for update or both photo_path and remove_photo are set.
    """
    if all(
        v is None or v is False
        for v in (
            first_name,
            last_name,
            external_id,
            biography,
            height,
            weight,
            shot_hand,
            birthdate,
            hometown,
            country,
            province,
            drafted_by,
            committed_to,
            photo_path,
            remove_photo,
        )
    ):
        msg = "At least one field must be provided for update"  # pragma: no cover
        raise ValueError(msg)  # pragma: no cover
    if photo_path and remove_photo:  # pragma: no cover
        msg = "Cannot both upload a photo and remove it"  # pragma: no cover
        raise ValueError(msg)  # pragma: no cover
    # Handle photo upload/removal # pragma: no cover
    photo_url: str | None = None  # pragma: no cover
    if photo_path:  # pragma: no cover
        photo_url = _upload_photo(session, photo_path)  # pragma: no cover
    # Fetch current player to get all fields # pragma: no cover
    current_player = get_team_player(session, season_id, team_id, player_id)  # pragma: no cover
    # Build payload with updated values (without "type" field for team context) # pragma: no cover
    payload: dict[str, Any] = {  # pragma: no cover
        "data": {  # pragma: no cover
            "id": player_id,  # pragma: no cover
            "attributes": {  # pragma: no cover
                "first_name": (
                    first_name if first_name is not None else current_player.first_name
                ),  # pragma: no cover
                "last_name": (
                    last_name if last_name is not None else current_player.last_name
                ),  # pragma: no cover
            },  # pragma: no cover
        },  # pragma: no cover
    }  # pragma: no cover
    attrs = payload["data"]["attributes"]  # pragma: no cover
    # Handle optional fields # pragma: no cover
    if external_id is not None:  # pragma: no cover
        attrs["external_id"] = external_id  # pragma: no cover
    elif current_player.external_id:  # pragma: no cover
        attrs["external_id"] = current_player.external_id  # pragma: no cover
    if biography is not None:  # pragma: no cover
        attrs["biography"] = biography  # pragma: no cover
    elif current_player.biography:  # pragma: no cover
        attrs["biography"] = current_player.biography  # pragma: no cover
    if height is not None:  # pragma: no cover
        attrs["height"] = height  # pragma: no cover
    elif current_player.height:  # pragma: no cover
        attrs["height"] = current_player.height  # pragma: no cover
    if weight is not None:  # pragma: no cover
        attrs["weight"] = weight  # pragma: no cover
    elif current_player.weight:  # pragma: no cover
        attrs["weight"] = current_player.weight  # pragma: no cover
    if shot_hand is not None:  # pragma: no cover
        attrs["shot_hand"] = shot_hand  # pragma: no cover
    elif current_player.shot_hand:  # pragma: no cover
        attrs["shot_hand"] = current_player.shot_hand  # pragma: no cover
    if birthdate is not None:  # pragma: no cover
        attrs["birthdate"] = birthdate  # pragma: no cover
    elif current_player.birthdate:  # pragma: no cover
        attrs["birthdate"] = str(current_player.birthdate)  # pragma: no cover
    if hometown is not None:  # pragma: no cover
        attrs["hometown"] = hometown  # pragma: no cover
    elif current_player.hometown:  # pragma: no cover
        attrs["hometown"] = current_player.hometown  # pragma: no cover
    if country is not None:  # pragma: no cover
        attrs["country"] = country  # pragma: no cover
    elif current_player.country:  # pragma: no cover
        attrs["country"] = current_player.country  # pragma: no cover
    if province is not None:  # pragma: no cover
        attrs["province"] = province  # pragma: no cover
    elif current_player.province:  # pragma: no cover
        attrs["province"] = current_player.province  # pragma: no cover
    if drafted_by is not None:  # pragma: no cover
        attrs["drafted_by"] = drafted_by  # pragma: no cover
    elif current_player.drafted_by:  # pragma: no cover
        attrs["drafted_by"] = current_player.drafted_by  # pragma: no cover
    if committed_to is not None:  # pragma: no cover
        attrs["committed_to"] = committed_to  # pragma: no cover
    elif current_player.committed_to:  # pragma: no cover
        attrs["committed_to"] = current_player.committed_to  # pragma: no cover
    # Handle photo # pragma: no cover
    if photo_url:  # pragma: no cover
        attrs["photo_url"] = photo_url  # pragma: no cover
    elif remove_photo:  # pragma: no cover
        attrs["photo_url"] = ""  # pragma: no cover
    elif current_player.photo_url:  # pragma: no cover
        attrs["photo_url"] = current_player.photo_url  # pragma: no cover
    endpoint = f"/api/seasons/{season_id}/players/{player_id}"
    response = session.patch(endpoint, headers=JSONAPI_HEADERS, json=payload)
    handle_response(response, endpoint, "PATCH team player")
    body: dict[str, Any] = response.json()
    player = parse_player(body["data"])
    # Populate with current roster metadata
    _populate_player_metadata(
        player,
        jersey=getattr(current_player, "jersey", None),
        position=getattr(current_player, "position", None),
        status=getattr(current_player, "status", None),
        designation=getattr(current_player, "designation", None),
    )
    return player


def assign_player(
    session: Session,
    season_id: str,
    player_id: str,
    team_id: str,
    *,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
) -> Player:
    """Assign an existing player to a team's roster.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param player_id: The player identifier to assign.
    :param team_id: The team identifier to assign the player to.
    :param jersey: Optional jersey number.
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :param status: Optional status (Regular, Affiliated, etc.).
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :returns: The :class:`Player` with roster metadata populated.
    :rtype: Player
    :raises GameSheetError: If the player is already assigned to the team.
    """
    player = get_player(session, season_id, player_id)
    team_data = get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    roster = current_attrs.get("roster", {})
    players_roster = roster.get("players", [])
    # Check if player is already on the roster
    for existing_player in players_roster:
        if existing_player.get("id") == player_id:
            msg = f"Player {player_id} is already assigned to team {team_id}"
            raise GameSheetError(msg)
    player_entry = _build_player_roster_entry(
        player_id,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )
    players_roster.append(player_entry)
    roster["players"] = players_roster
    update_team_roster(session, season_id, team_id, roster, current_attrs, current_relationships)
    _populate_player_metadata(
        player,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )
    return player


def unassign_player(session: Session, season_id: str, player_id: str, team_id: str) -> None:
    """Unassign a player from a team's roster.

    The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param player_id: The player identifier to unassign.
    :param team_id: The team identifier to unassign the player from.
    :raises GameSheetError: If the player is not assigned to the team.
    """
    # Step 1: Fetch current team data
    team_data = get_team_for_roster_update(session, season_id, team_id)
    current_attrs = team_data.get("data", {}).get("attributes", {})
    current_relationships = team_data.get("data", {}).get("relationships", {})
    # Step 2: Remove player from roster
    roster = current_attrs.get("roster", {})
    players_roster = roster.get("players", [])
    # Find and remove the player
    original_count = len(players_roster)
    players_roster = [p for p in players_roster if p.get("id") != player_id]
    if len(players_roster) == original_count:
        msg = f"Player {player_id} is not assigned to team {team_id}"
        raise GameSheetError(msg)
    roster["players"] = players_roster
    # Step 3: Update team roster
    update_team_roster(session, season_id, team_id, roster, current_attrs, current_relationships)


def assign_team_player(
    session: Session,
    season_id: str,
    team_id: str,
    player_id: str,
    *,
    jersey: str | None = None,
    position: str | None = None,
    status: str | None = None,
    designation: str | None = None,
) -> Player:
    """Assign an existing player to a team's roster (team-scoped alias).

    This is an alias for :func:`assign_player` provided for consistency with the team-scoped command
    structure. The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier to assign the player to.
    :param player_id: The player identifier to assign.
    :param jersey: Optional jersey number.
    :param position: Optional position (Forward, Defence, Goalie, etc.).
    :param status: Optional status (Regular, Affiliated, etc.).
    :param designation: Optional designation (Captain, Alternate Captain, etc.).
    :returns: The :class:`Player` with roster metadata populated.
    :rtype: Player
    """
    return assign_player(
        session,
        season_id,
        player_id,
        team_id,
        jersey=jersey,
        position=position,
        status=status,
        designation=designation,
    )


def unassign_team_player(session: Session, season_id: str, team_id: str, player_id: str) -> None:
    """Unassign a player from a team's roster (team-scoped alias).

    This is an alias for :func:`unassign_player` provided for consistency with the team-scoped command
    structure. The supplied :class:`Session` must already carry a bearer token (e.g. via
    :meth:`Session.set_bearer_token`); the call is otherwise unauthenticated and will 401.
    :param session: An authenticated :class:`Session`.
    :param season_id: The season identifier.
    :param team_id: The team identifier to unassign the player from.
    :param player_id: The player identifier to unassign.
    """
    unassign_player(session, season_id, player_id, team_id)
