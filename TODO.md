# gamesheet-teams Implementation TODO

Tracking the next steps for bringing `gamesheet-teams` from stub to functional CLI. Derived from the dual-CLI refactor architecture decisions (branch:
`feat/dual-cli-refactor`).

______________________________________________________________________

## Phase 1: Discovery (no code changes)

- [ ] **Auth flow** — Determine how `teams.gamesheet.app` authenticates (Firebase like admin? OAuth? Magic link? Different IdP?)
- [ ] **API surface** — Catalog endpoints the teams dashboard calls (DevTools Network tab). Note format: JSON:API, REST, GraphQL, BFF?
- [ ] **ID format** — Confirm whether teams uses UUIDs (vs admin's integer IDs)
- [ ] **Resource inventory** — List the resources available on the teams side (rosters, schedules, stats, etc.)

## Phase 2: Auth abstraction (`common/auth/`)

- [ ] Define `LoginFlow` base class or protocol in `common/auth/` — interface: `authenticate(email, password) -> tokens`
- [ ] Refactor current admin login (`common/auth/login.py`) as a concrete `LoginFlow` implementation
- [ ] Implement teams login as a second concrete `LoginFlow` (depends on Phase 1 auth discovery)
- [ ] Wire `gamesheet-teams login` command to the teams login strategy (replace current stub)
- [ ] Tests for the new abstraction + teams login flow
- [ ] Verify 100% coverage still holds

## Phase 3: Teams constants and shared utilities

- [ ] Add teams-specific API endpoints to `teams/constants.py` or `teams/shared/constants.py`
- [ ] Evaluate whether `common/gamesheet_http.py` and `common/jsonapi.py` apply to the teams API, or if teams needs its own HTTP helpers
- [ ] Move anything confirmed admin-only out of `common/` into `admin/shared/` (candidates: `image_upload.py`, possibly `gamesheet_http.py`, `jsonapi.py`)

## Phase 4: Teams domain modules

For each resource discovered in Phase 1, repeat this pattern:

- [ ] **Models** — Pydantic model(s) in `teams/<resource>/models.py` (or `teams/<resource>.py` for simple ones)
- [ ] **Actions** — Thin action functions wrapping teams API endpoints
- [ ] **CLI command** — `teams/cli/commands/<resource>.py` using `ResourceGroup` + standard verbs (`list`, `get`, `create`, `update`, `delete` with aliases)
- [ ] **Register** — Add command group to `teams/cli/main.py`
- [ ] **Tests** — Unit tests for models/actions, CLI tests for commands
- [ ] **Coverage** — Verify 100% after each resource

## Phase 5: ID abstraction

- [ ] Decide on approach: generic `str` IDs validated per-pillar, or per-pillar ID types with a common protocol
- [ ] Implement in models as needed (can be deferred until first teams domain module exposes the mismatch)

## Phase 6: Cleanup and docs

- [ ] Delete `watch_20260715-134537` from repo root
- [ ] Update `CLAUDE.md` structure docs once teams modules exist
- [ ] Decide `gamesheet_sdk.teams` public re-exports in `teams/__init__.py`
- [ ] Update `docs/reference/api.md` with new teams module autodoc entries
- [ ] Update `docs/reference/cli.md` if `sphinx-click` tree grows
- [ ] Update tutorials/how-to guides with teams CLI examples

______________________________________________________________________

## Dependencies

```text
Phase 1 (discovery)
  └─► Phase 2 (auth abstraction)
  └─► Phase 3 (constants/utilities)
        └─► Phase 4 (domain modules) ◄─── also depends on Phase 2
              └─► Phase 5 (ID abstraction, if needed)
                    └─► Phase 6 (cleanup/docs)
```
