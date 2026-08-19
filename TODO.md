# gamesheet-teams Implementation TODO

<!--TOC-->

______________________________________________________________________

- [1. Phase 1: Discovery (no code changes) — COMPLETE](#1-phase-1-discovery-no-code-changes--complete)
- [2. Phase 2: Auth abstraction (`common/auth/`)](#2-phase-2-auth-abstraction--commonauth)
- [3. Phase 3: Teams constants and shared utilities](#3-phase-3-teams-constants-and-shared-utilities)
- [4. Phase 4: Teams domain modules](#4-phase-4-teams-domain-modules)
  - [4.1. Phase 4a — Core resources (overlap with admin, most useful)](#41-phase-4a--core-resources-overlap-with-admin-most-useful)
  - [4.2. CLI help harmonization (cross-cutting, applies to both CLIs)](#42-cli-help-harmonization-cross-cutting-applies-to-both-clis)
  - [4.3. Phase 4b — Teams-unique features](#43-phase-4b--teams-unique-features)
  - [4.4. Phase 4c — Complex features (may defer)](#44-phase-4c--complex-features-may-defer)
- [5. Phase 5: ID abstraction — LIKELY UNNECESSARY](#5-phase-5-id-abstraction--likely-unnecessary)
- [6. Phase 6: Cleanup and docs](#6-phase-6-cleanup-and-docs)
- [7. Dependencies](#7-dependencies)
- [8. Key architectural findings from Phase 1](#8-key-architectural-findings-from-phase-1)

______________________________________________________________________

<!--TOC-->

Tracking the next steps for bringing `gamesheet-teams` from stub to functional CLI. Derived from the dual-CLI refactor architecture decisions (branch:
`feat/dual-cli-refactor`).

______________________________________________________________________

## 1. Phase 1: Discovery (no code changes) — COMPLETE

- [x] **Auth flow** — Both admin and teams use the same Firebase project:

  ```text
  (`gamesheet-production`, apiKey `AIzaSyCk5pKBFxvCMuwPchzXgvvz4XmmscJTvs8`)  # notsecret
  ```

  Teams auth is HTTP-only (no browser needed): Firebase REST `signInWithPassword` → `GET /api/auth/tokens` (Bearer ID token) → access+refresh tokens. Refresh
  via `POST /api/auth/refresh` (Bearer refresh token). Three auth methods: email/password, OTP, Google/Apple sign-in. Ten auth endpoints total under
  `/api/auth/*`.

- [x] **API surface** — ~80 pure REST/JSON endpoints through a single gateway (`https://api.teams.gamesheet.app`). No JSON:API, no GraphQL, no BFF. All calls
  use `Authorization: Bearer <access_token>`. Auto-refresh on 401 via fetch wrapper. Response envelope: `{success: true, <resource>: ...}` or
  `{success: true, data: ...}`. Errors: `{error: "msg"}` or `{errors: [{message: "..."}]}`. Contrast with admin's 4+ backends and JSON:API format.

- [x] **ID format** — Dual-ID system for teams: integer `.id` (internal) + string `.teamId`/`.prototeamId` (primary routing key, likely UUID). Most resources
  (games, seasons, divisions, members, players, coaches) use integer IDs. Conversations and calendar events use string IDs. Registries use UUIDs.
  Recommendation: use `str` for all IDs in pydantic models (matching admin convention), which may eliminate the need for Phase 5 entirely.

- [x] **Resource inventory** — Nine sections cataloged: Schedule (games, practices, events, calendar subscribe, availability RSVP, scoresheets), Roster
  (players, coaches, CSV/HCR/USAH import), Messages (conversations, DMs, groups, attachments, reactions), Members (staff + follower invitations, code-based
  join), Lineups (playing/not-playing, starter goalie, coach signatures, sign & publish), Team Management (create/edit/archive, seasons, divisions, leagues,
  scoring keys), Profile (account, notifications, photo), Billing (Teams+ $99 purchase, entitlement), Lookups (public endpoint, 15 enum categories). Four sports
  supported: hockey, soccer, boxla, field_lacrosse.

## 2. Phase 2: Auth abstraction (`common/auth/`)

- [x] Define `LoginFlow` protocol in `common/auth/flow.py` — `@runtime_checkable` Protocol with `authenticate(email, password, *, timeout) -> dict[str, str]`.
  Exported from `common.auth`. Tests in `tests/common/auth/test_flow.py` (5 tests, 100% coverage). Committed `1363119`.
- [x] Refactor current admin login (`common/auth/login.py`) as a concrete `LoginFlow` implementation — `AdminLoginFlow` class wraps existing `login()` +
  `BrowserSession`, reads tokens from saved state via `load_access_token()`/`load_refresh_token()`. Exported from `common.auth`. 4 tests in
  `tests/common/auth/test_login.py`. Committed `dee6213`.
- [x] Implement teams login as a second concrete `LoginFlow` — `TeamsLoginFlow` in `teams/login.py`: HTTP-only Firebase REST `signInWithPassword` →
  `GET /api/auth/tokens`. Extracted shared credential resolution (`common/auth/credentials.py`) and Firebase error parsing (`common/auth/firebase.py`) to
  de-duplicate admin/teams code. Teams constants in `teams/shared/constants.py`. 10 tests in `tests/teams/test_login.py`, 8 in
  `tests/common/auth/test_credentials.py`, 6 in `tests/common/auth/test_firebase.py`. Committed `c5f54c3`.
- [x] Add teams-specific auth constants — `TEAMS_API_GATEWAY`, `FIREBASE_API_KEY`, `TEAMS_TOKEN_EXCHANGE_PATH`, `TEAMS_REFRESH_PATH` in
  `teams/shared/constants.py`. Committed `c5f54c3`.
- [x] Wire `gamesheet-teams login` command to the teams login strategy (replace current stub) — replaced stub with working `TeamsLoginFlow`-backed
  implementation, 7 tests in `tests/teams/cli/test_main.py`. Committed `83970ac`.
- [x] Implement teams token refresh via `POST /api/auth/refresh` with Bearer refresh token header — `refresh_access_token()` in `teams/login.py`: standalone
  HTTP POST mirroring admin pattern, returns `{"access", "refresh"}` (no roles). Exported from `teams/__init__.py`. 3 tests in `tests/teams/test_login.py`.
  Committed `5c08ee1`.
- [x] Verify 100% coverage still holds — 1013 tests pass, 100.00% coverage confirmed after `5c08ee1`. Now 1046 tests after Phase 4a Lookups + CLI harmonization.

## 3. Phase 3: Teams constants and shared utilities

- [x] Add teams API gateway URL and endpoint paths to `teams/shared/constants.py` — auth-related constants added in Phase 2 (`c5f54c3`). Domain endpoint paths
  to be added as Phase 4 modules are implemented.
- [x] Implement teams `AuthenticatedSession` — `TeamsAuthenticatedSession` in `teams/session.py` subclasses `BaseAuthenticatedSession` (extracted to
  `common/auth/session.py` to de-duplicate admin/teams session code). Each pillar implements `_do_refresh()` only. 8 tests in `tests/teams/test_session.py`.
  Committed `2d3b97f`.
- [x] Evaluate whether `common/shared/gamesheet_http.py` and `common/shared/jsonapi.py` apply to teams API — `jsonapi.py` is entirely admin-only (teams uses
  plain REST/JSON, not JSON:API). `gamesheet_http.py` has a useful pattern (`handle_response`) but is coupled to admin-specific error messages; teams will get
  its own HTTP helper in Phase 4. `check_bff_response_status` and `handle_season_scoped_response` are admin-only.
- [x] Move anything confirmed admin-only out of `common/` into `admin/shared/` — moved `jsonapi.py` from `common/shared/` to `admin/shared/`, updated all 5
  admin domain module imports (`associations`, `divisions`, `leagues`, `teams`, `roster/models`). Updated `admin/shared/__init__.py` exports and removed jsonapi
  from `common/shared/__init__.py`. Committed `cbcf42d`.

## 4. Phase 4: Teams domain modules

SDK implementation priority based on discovery:

### 4.1. Phase 4a — Core resources (overlap with admin, most useful)

For each resource, repeat this pattern: pydantic model(s), action functions, CLI command module, register in `teams/cli/main.py`, tests, verify 100% coverage.

- [x] **Lookups** — Public endpoint (`GET /api/lookups`, no auth), 15 enum categories (sports, positions, game_types, etc.). Domain module (`teams/lookups.py`)
  with `LookupValue` model and `list_lookups()` action. CLI commands: `list` (default, summary or filtered by `--category`) and `get` (`--category` required).
  Aliases: `ls` for list, `show`/`view` for get. Committed `0957ac6` (domain + list), then added `get` subcommand, vulture `ignore_decorators` fix for
  `@lookups_group.command`.
- [x] **Seasons** — Bearer-authenticated endpoint (`GET /api/seasons`), returns list of seasons. Domain module (`teams/seasons.py`) with models
  (`SeasonSummary`, `SeasonDetail`, `PenaltyCode`, `SeasonTeam`) and actions (`list_seasons`, `get_season`, `get_season_penalty_codes`, `get_season_teams`). CLI
  commands: `list` (default, alias `ls`), `get` (aliases `show`, `view`), `penalty-codes` (aliases `penalty_codes`, `penalties`), and `teams`. Selected via
  `--season-id` or `GAMESHEET_SEASON_ID`. Shared CLI options, rendering, and action runner extracted into `common/cli/` (`decorators.py`, `rendering.py`,
  `helpers.py`).
- [x] **Teams** — Bearer-authenticated endpoint (`GET /api/teams`), returns list of teams associated with user. Domain module (`teams/teams.py`) with models
  (`TeamSummary`, `TeamDetail`) and actions (`list_teams`, `get_team`, `fetch_teams_raw`, `fetch_team_raw`, `upload_team_image`, `update_team`, `archive_team`,
  `restore_team`, `delete_team`). CLI commands: `list` (default, alias `ls`, primary focus fields: `memberId`, `teamId`, `relationship`, `status`,
  `onboardingCompletedAt`, `teamName`, `ageCategory`, `clubId`, `joinedAt`, `statsYear`), `get` (aliases `show`, `view`, selected via `--team-id` / `-t` or
  `GAMESHEET_TEAM_ID`), `update` (aliases `set`, `edit`, supporting `--name`/`--team-name`, `--skill`, `--logo`/`--team-logo`, `--age-category`, `--province`,
  with automatic image upload via `GET /api/images/upload-url` and direct Cloudflare POST), `archive` (selected via `--team-id` / `-t` or `GAMESHEET_TEAM_ID`,
  setting `isArchived: true`), `restore` (alias `unarchive`, selected via `--team-id` / `-t` or `GAMESHEET_TEAM_ID`, setting `isArchived: false` via
  `PATCH /api/teams/{team_id}`), and `delete` (aliases `rm`, `remove`, selected via `--team-id` / `-t` or `GAMESHEET_TEAM_ID`, with destructive confirmation and
  `--force` / `-f` flag via `DELETE /api/teams/{team_id}`).
- [ ] **Roster — Players** — CRUD (`/api/roster/players/*`), 23 positions, player statuses/duties
- [ ] **Roster — Coaches** — CRUD (`/api/roster/coaches/*`), 5 coach positions
- [ ] **Games** — CRUD (`/api/schedule-game/*`), game status, 5 game types
- [ ] **Divisions** — List by season, by team+season (`/api/divisions/*`)
- [ ] **Leagues** — List by association (`GET /api/leagues/association/{id}`)

### 4.2. CLI help harmonization (cross-cutting, applies to both CLIs)

- [x] **Unified rich-click configuration** — Extracted shared rich-click defaults (11 settings: `TEXT_MARKUP`, `SHOW_ARGUMENTS`, `GROUP_ARGUMENTS_OPTIONS`,
  `STYLE_ERRORS_SUGGESTION`, `ERRORS_SUGGESTION`, `ERRORS_EPILOGUE`, `MAX_WIDTH`, `OPTIONS_TABLE_COLUMN_TYPES`, `OPTIONS_TABLE_HELP_SECTIONS`) into
  `common/cli/rich_config.py:apply_rich_click_defaults()`. Both CLIs call it at module level, eliminating duplicate code.
- [x] **Consistent option/command grouping** — Both CLIs use: "Configuration Options" (`--base-url`, `--no-headless`), "General Options" (`-v`, `-V/--version`,
  `-h/--help`), "Authentication" (`login`), "Utilities" (`completion`), "Resources" (resource commands). Admin resources ordered: associations, leagues,
  seasons, ipad-keys, locations, games, divisions, teams, roster, referees.
- [x] **Removed "GameSheet" from resource descriptions** — `associations.py` and `leagues.py` group descriptions no longer redundantly include "GameSheet".
- [x] **`context_settings` on teams lookups** — Added `context_settings={"help_option_names": ["-h", "--help"]}` to `lookups_group` decorator.
- [x] **Tests** — Updated `test_command_groups_configured` for new group names. Added 3 teams rich-click config tests
  (`test_teams_rich_click_configuration_applied`, `test_teams_option_groups_configured`, `test_teams_command_groups_configured`). 1046 tests, 100% coverage.

### 4.3. Phase 4b — Teams-unique features

- [x] **Schedule & Calendar (list)** — `GET /api/calendar?teamId={id}&month=all` endpoint support in domain module (`teams/schedule.py`) with `ScheduleEvent`
  model and action functions (`fetch_calendar_raw`, `list_schedule`, `list_events`, `list_games`, `list_practices`). CLI commands: `schedule list` (default,
  alias `ls`), `schedule events list` (default, alias `ls`), `schedule games list` (default, alias `ls`), `schedule practices list` (default, alias `ls`),
  focusing on `eventDate`, `eventLocation`, `eventTime`, `eventTitle`, `id`, and `type`.
- [x] **Schedule & Calendar (get) & Availability (batch)** — `GET /api/calendar/occurrences/{id}`, `GET /api/schedule-game/{game_id}`, and
  `GET /api/availability/batch` in domain module (`teams/schedule.py`) with `ScheduleEventDetail` model and action functions (`fetch_event_occurrence_raw`,
  `fetch_scheduled_game_raw`, `fetch_availability_raw`, `get_schedule_event`, `get_event`, `get_game`, `get_practice`). CLI commands: `schedule get` (aliases
  `show`, `view`), `schedule events get` (aliases `show`, `view`), `schedule games get` (aliases `show`, `view`), `schedule practices get` (aliases `show`,
  `view`), with optional `--availability` / `--include-availability` switch.
- [x] **Schedule & Calendar (subscribe)** — Calendar subscription URL generation (`CalendarSubscription` model, `get_calendar_subscription` in
  `teams/schedule.py`) for Apple Calendar, Google Calendar, and generic calendar feed (`webcal`). CLI command: `schedule subscribe` (alias `sub`), with support
  for `--team-id` / `-t` / `GAMESHEET_TEAM_ID` and URL column filtering via `--apple`, `--google`, `--webcal`, or `--columns`.
- [x] **Schedule & Calendar (create: events, games, practices)** — Create events and practices via `POST /api/calendar/events` and games via
  `POST /api/schedule-game` in domain module (`teams/schedule.py`) with `CalendarEventCreated` and `CreatedGameResult` models, `build_rrule`,
  `validate_game_type`, `create_calendar_event_raw`, `create_schedule_game_raw`, `create_event`, `create_practice`, and `create_game`. CLI commands:
  `schedule events create`, `schedule practices create`, and `schedule games create` with aliases `add` and `new`, supporting flexible datetime parsing,
  start/end/duration resolution, all-day flag, recurrence rules (daily, weekly with `--by-day`, monthly), and game metadata (scorekeeper, broadcaster, timezone
  offset).
- [x] **Schedule & Calendar (delete: events, games, practices)** — Delete events and practices via `DELETE /api/calendar/events/{event_id}` (all occurrences)
  and `DELETE /api/calendar/occurrences/{occurrence_id}?deleteFuture={true|false}` and games via `DELETE /api/schedule-game/{game_id}` in domain module
  (`teams/schedule.py`) with `ScheduleDeleteResult` model, `delete_schedule_game_raw`, `delete_game`, `delete_calendar_event_raw`, `delete_calendar_event`,
  `delete_calendar_occurrence_raw`, `delete_calendar_occurrence`, `delete_event`, and `delete_practice`. CLI commands: `schedule delete`,
  `schedule events delete`, `schedule games delete`, and `schedule practices delete` with aliases `del`, `rm`, and `remove`, supporting destructive confirmation
  (`--force` / `-f`), repeating event occurrence scope (`--future`, `--all`, `--single`), and interactive prompting.
- [x] **Schedule & Calendar (update: events, games, practices)** — Update events and practices via
  `PUT /api/calendar/occurrences/{occurrence_id}?updateFuture={true|false}` and games via `PUT /api/schedule-game/{game_id}` in domain module
  (`teams/schedule.py`) with `UpdatedGameResult` model, `update_schedule_game_raw`, `update_game`, `update_calendar_occurrence_raw`,
  `update_calendar_occurrence`, `update_event`, and `update_practice`. CLI commands: `schedule update`, `schedule events update`, `schedule games update`, and
  `schedule practices update` with aliases `set` and `edit`, supporting flexible datetime resolution (`resolve_update_times`), start/end/duration, repeating
  event occurrence scope (`--future`, `--single`), and game metadata.
- [ ] **Availability RSVP** — Game/event/practice RSVP (`/api/availability/*`)
- [ ] **Lineups** — View/set lineup, sign & publish (`/api/lineups/*`)
- [ ] **Members/Invitations** — List members, invite staff + parents/players, accept/remove (`/api/teams/{id}/members/*`, `/api/invitations/*`)
- [ ] **Scoresheets** — Download PDF, bulk export (`/api/scoresheets/*`)
- [ ] **User profile** — View/update account, subscriptions/notifications (`/api/users/*`)

### 4.4. Phase 4c — Complex features (may defer)

- [ ] **Chat/Messages** — Conversations, messages, reactions, attachments, read status (13+ endpoints under `/api/chat/*`)
- [ ] **Billing** — Entitlement check, checkout session (`/api/billing/*`)
- [ ] **Registry import** — HCR/USAH import (`POST /api/registry-import/start`)

## 5. Phase 5: ID abstraction — LIKELY UNNECESSARY

- [ ] ~~Decide on approach: generic `str` IDs validated per-pillar, or per-pillar ID types with a common protocol~~ → Phase 1 discovery recommends `str` for all
  IDs in both admin and teams models. Admin already does this (JSON:API returns string IDs). Teams returns integers for most resources but `str` works
  uniformly. The dual-ID pattern (integer `.id` + string `.prototeamId`) only affects the Team model. Re-evaluate after Phase 4a implementation — if `str` works
  everywhere, delete this phase.

## 6. Phase 6: Cleanup and docs

- [ ] Update `CLAUDE.md` structure docs once teams modules exist
- [ ] Decide `gamesheet_sdk.teams` public re-exports in `teams/__init__.py`
- [ ] Update `docs/reference/api.md` with new teams module autodoc entries
- [ ] Update `docs/reference/cli.md` if `sphinx-click` tree grows
- [ ] Update tutorials/how-to guides with teams CLI examples

______________________________________________________________________

## 7. Dependencies

```text
Phase 1 (discovery) ✅ COMPLETE
  └─► Phase 2 (auth abstraction)
  └─► Phase 3 (constants/utilities)
        └─► Phase 4a (core domain modules) ◄─── also depends on Phase 2
              └─► Phase 4b (teams-unique features)
                    └─► Phase 4c (complex features, may defer)
                          └─► Phase 5 (ID abstraction — likely unnecessary)
                                └─► Phase 6 (cleanup/docs)
```

______________________________________________________________________

## 8. Key architectural findings from Phase 1

| Aspect       | Admin                                     | Teams                                      |
| ------------ | ----------------------------------------- | ------------------------------------------ |
| Auth         | Playwright browser automation             | HTTP-only (Firebase REST API)              |
| API format   | JSON:API + REST mix                       | Pure REST/JSON                             |
| API backends | 4+ (main, BFF, scoresheet, auth)          | 1 gateway (`api.teams.gamesheet.app`)      |
| Auth header  | Cookie-based (browser state)              | Bearer token                               |
| Auto-refresh | `AuthenticatedSession` (requests.Session) | Fetch wrapper retries on 401               |
| Resource IDs | Integer (string in JSON:API)              | Integer + string prototeamId               |
| Unique       | Associations, referees, iPad keys         | Chat, availability, lineups, billing, etc. |
| Shared       | Leagues, seasons, divisions, teams, etc.  | (same)                                     |
