# Architecture Overview

This document describes the high-level architecture of `gamesheet-sdk-py`, explaining how the major components fit together and the design decisions behind
them.

## 1. System Design

The SDK is organized into three pillars:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                        gamesheet_sdk (top-level)                           │
│                  Re-exports for backward compatibility                     │
└─────────────────────────────────────────────────────────────────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│     common/     │  │       admin/        │  │       teams/        │
│  Shared infra   │  │  Admin dashboard    │  │  Teams dashboard    │
│                 │  │                     │  │                     │
│ • auth/         │  │ • associations.py   │  │ • cli/ (stub)       │
│ • cli/core      │  │ • divisions.py      │  │   - login (NYI)     │
│ • browser.py    │  │ • leagues.py        │  │   - completion      │
│ • config.py     │  │ • seasons.py        │  │                     │
│ • session.py    │  │ • teams.py          │  │ (domain modules     │
│ • output.py     │  │ • referees.py       │  │  forthcoming)       │
│ • errors.py     │  │ • ipad_keys.py      │  │                     │
│ • exceptions.py │  │ • games/            │  │                     │
│ • constants.py  │  │ • roster/           │  │                     │
│ • shared/       │  │ • cli/ (full)       │  │                     │
└─────────────────┘  └─────────────────────┘  └─────────────────────┘
```

Each pillar has a clear responsibility:

- **`common/`** — Infrastructure shared by both dashboards: authentication, HTTP sessions, browser automation, configuration, output formatting, error messages.
- **`admin/`** — Domain modules and CLI for the admin dashboard (`gamesheet-admin`). Contains all resource models and action functions.
- **`teams/`** — CLI and domain modules for the teams dashboard (`gamesheet-teams`). Currently a stub with login not yet implemented.

Dependencies flow inward: `admin/` and `teams/` depend on `common/`, but never on each other.

## 2. Component Relationships

### 2.1. Core Components

#### 2.1.1. Configuration (`common/config.py`)

Central configuration object that resolves settings from multiple sources:

```python
Config(
    # Sources in priority order:
    # 1. Constructor arguments (highest priority)
    # 2. Environment variables (GAMESHEET_*)
    # 3. Default values (lowest priority)
)
```

**Responsibilities**:

- Environment variable resolution
- Default value management
- Path configuration (tokens, sessions, browser state)
- Timeout and retry settings

#### 2.1.2. Session Layer

**Base Session** (`common/session.py`):

- Wraps `requests.Session` with GameSheet-specific defaults
- Automatic retries on transient failures
- Cookie persistence across process invocations
- User-Agent header management

**Authenticated Session** (`common/auth/session.py`):

- Extends base session with token auto-refresh
- Intercepts HTTP 401/403 responses
- Refreshes access token using refresh token
- Invokes callback to persist new tokens

**Browser Session** (`common/browser.py`):

- Playwright-based headless Chromium automation
- Used when HTTP requests are insufficient (JavaScript rendering, anti-bot measures)
- Lazy initialization (only starts browser when needed)
- Storage state persistence (cookies + localStorage)

#### 2.1.3. Authentication (`common/auth/`)

**Login Flow** (`common/auth/login.py`):

1. Opens GameSheet login page in headless browser
2. Captures Firebase Authentication response
3. Extracts `idToken` (access token) and `refreshToken`
4. Saves tokens to `~/.gamesheet/access_token` and `~/.gamesheet/refresh_token`

**Token Management** (`common/auth/tokens.py`):

- `load_access_token()` — Read from disk
- `load_refresh_token()` — Read from disk
- `save_tokens()` — Write both to disk
- `refresh_access_token()` — Exchange refresh token for new access token

**Storage** (`common/auth/storage.py`):

- File I/O for token files
- Directory creation with safe permissions
- Path resolution

#### 2.1.4. Domain Modules (`admin/`)

Each domain module follows a consistent pattern:

```python
# Example: src/gamesheet_sdk/admin/associations.py


# Pydantic model for data validation
class Association(BaseModel):
    id: str
    title: str
    # ... other fields


# Action functions
def list_associations(config: Config | None = None) -> list[Association]:
    """Retrieve all associations."""
    # Implementation using Session or BrowserSession
```

**Current Domain Modules** (all under `admin/`):

- `associations.py` — Sports associations
- `leagues.py` — Leagues within associations
- `seasons.py` — Seasons within leagues
- `divisions.py` — Divisions within seasons
- `teams.py` — Teams within divisions
- `games/` — Game management (scheduled, completed, brackets)
- `referees.py` — Referee management
- `roster/` — Player and coach roster management
- `ipad_keys.py` — iPad/Scoring access keys

#### 2.1.5. CLI Layer

The CLI is split into two entry points with shared infrastructure:

**Common CLI** (`common/cli/`):

- `core.py` — `ResourceGroup` class, `confirm_destructive` decorator, logging setup, exit code resolution
- `constants.py` — Shared constants (`SHELL_TYPES`)

**Admin CLI** (`admin/cli/`):

- `main.py` — Root CLI group (`gamesheet-admin`) and `main()` entry point
- `constants.py` — Admin-specific constants (format choices, column specs)
- `helpers.py` — Session building, action helpers
- `commands/` — Individual command modules
- `shared/` — Shared decorators and rendering utilities

**Teams CLI** (`teams/cli/`):

- `main.py` — Root CLI group (`gamesheet-teams`) and `main()` entry point
- `commands/` — Login (stub) and completion commands

**Resource-Oriented Design**:

```text
gamesheet-admin <resource> <verb> [options]
               └─────┬────┘ └─┬──┘
                  Noun      Verb

Examples:
  gamesheet-admin associations list
  gamesheet-admin teams get --team-id 123
  gamesheet-admin referees create --first-name John --last-name Doe
```

**Canonical Verbs and Aliases**:

- `create` (aliases: `add`, `new`)
- `get` (aliases: `show`, `view`)
- `list` (aliases: `ls`)
- `update` (aliases: `set`, `edit`)
- `delete` (aliases: `rm`, `remove`)

## 3. Data Flow

### 3.1. Typical Read Operation (GET)

```text
User Command
    │
    ▼
CLI Command (e.g., seasons list)
    │
    ▼
Domain Function (list_seasons)
    │
    ▼
Session.get("/api/seasons")
    │
    ▼
Retry Logic (on 5xx errors)
    │
    ▼
JSON Response
    │
    ▼
Pydantic Model Validation
    │
    ▼
List[Season] returned to CLI
    │
    ▼
Output Formatter (JSON/YAML/table)
    │
    ▼
User sees formatted output
```

### 3.2. Authenticated Operation with Auto-Refresh

```text
User Command
    │
    ▼
CLI Command (requires auth)
    │
    ▼
Domain Function
    │
    ▼
AuthenticatedSession.get(...)
    │
    ▼
HTTP 401 Unauthorized
    │
    ▼
Auto-refresh: refresh_access_token()
    │
    ▼
Save new tokens via callback
    │
    ▼
Retry original request with new token
    │
    ▼
Success: process response
```

### 3.3. Browser-Based Operation

```text
User Command (e.g., login)
    │
    ▼
common/auth/login.py
    │
    ▼
BrowserSession.goto("/login")
    │
    ▼
Playwright launches Chromium
    │
    ▼
Inject email/password, submit form
    │
    ▼
Capture Firebase Auth response
    │
    ▼
Extract tokens from XHR response
    │
    ▼
Save tokens to disk
    │
    ▼
BrowserSession saves storage state
    │
    ▼
Browser closes
```

## 4. Design Decisions

### 4.1. Why Both HTTP and Browser?

**HTTP (requests)** is used for:

- Most API operations (list, get, create, update, delete)
- Fast, lightweight, easy to test
- VCR cassettes for reproducible tests

**Browser (Playwright)** is used for:

- Login flow (JavaScript-heavy, Firebase Auth)
- Operations blocked by anti-bot measures
- Workflows requiring full page rendering

**Trade-off**: Complexity (two session types) vs. reliability (can handle any GameSheet workflow).

### 4.2. Why Three Pillars?

The admin and teams dashboards are separate GameSheet products with different URLs, different authentication flows, and potentially different data models (admin
uses integer IDs, teams may use UUIDs). Splitting the codebase into `common/`, `admin/`, and `teams/` ensures:

- No cross-contamination of dashboard-specific logic
- Shared infrastructure is maintained once
- Each CLI can evolve independently
- The `gamesheet-admin` and `gamesheet-teams` entry points are distinct user experiences

### 4.3. Why Pydantic Models?

**Benefits**:

- Runtime validation of API responses
- Type hints for IDE autocomplete
- Automatic JSON serialization/deserialization
- Self-documenting API (field descriptions in docstrings)

**Trade-off**: Tight coupling to API shape (breaking changes upstream require model updates).

### 4.4. Why Click for CLI?

**Benefits**:

- Widely used, well-documented
- Subcommand support (nested resource groups)
- Auto-generated `--help` text
- Shell completion support (bash/zsh/fish)

**Alternative considered**: `argparse` (stdlib, no deps), rejected because subcommand support is verbose.

### 4.5. Why src/ Layout?

**Benefits**:

- Tests import from installed package (catches packaging issues)
- Prevents accidentally importing from source instead of installed version
- Clear separation between source and tests

**Trade-off**: Slightly more setup (need `pip install -e .`), but worth it for packaging correctness.

### 4.6. Why 100% Test Coverage?

**Benefits**:

- Confidence in refactoring (know what breaks)
- Forces thinking about edge cases
- Documentation via tests (shows how to use the API)

**Trade-off**: More upfront work, but pays dividends in maintenance.

### 4.7. Why Complexity Gate (Grade A)?

**Benefits**:

- Forces decomposition of complex logic
- Easier to test (small functions)
- Easier to review (less mental load)
- Self-documenting (function names describe intent)

**Trade-off**: More functions, but each is simpler.

## 5. Extension Points

### 5.1. Adding a New Admin Domain Module

1. Create `src/gamesheet_sdk/admin/<resource>.py`
2. Define Pydantic model(s)
3. Implement action functions (`list_<resource>`, `get_<resource>`, etc.)
4. Create `src/gamesheet_sdk/admin/cli/commands/<resource>.py`
5. Register CLI group in `admin/cli/main.py`
6. Add tests under `tests/unit/<resource>/` and `tests/cli/<resource>/`

### 5.2. Adding a New CLI Verb

If the standard CRUD verbs (`create`, `get`, `list`, `update`, `delete`) are insufficient:

1. Add custom command to resource group: `@<resource>_group.command("custom-verb")`
2. Update aliases map in `ResourceGroup` instantiation if needed
3. Add corresponding domain function
4. Add tests

### 5.3. Adding Teams Domain Modules

The teams pillar follows the same pattern as admin. When the teams authentication flow is implemented:

1. Create domain modules under `src/gamesheet_sdk/teams/`
2. Create CLI commands under `src/gamesheet_sdk/teams/cli/commands/`
3. Register commands in `teams/cli/main.py`

### 5.4. Adding a New Output Format

The SDK supports 15 output formats (see `src/gamesheet_sdk/common/output.py`). To add a new one:

1. Add formatter to `render()` function
2. Update `FORMAT_CHOICES` in `admin/cli/constants.py`
3. Update `--format` option help text
4. Add integration test

## 6. Testing Strategy

### 6.1. Test Organization

```text
tests/
├── unit/                   # Domain module tests
│   ├── associations/
│   ├── leagues/
│   └── ...
├── cli/                    # CLI command tests
│   ├── associations/
│   ├── leagues/
│   └── ...
├── admin/cli/              # Admin CLI entry point tests
├── teams/cli/              # Teams CLI entry point tests
├── integration/            # Multi-component tests
│   ├── browser/
│   ├── cli_games/
│   └── ...
└── fixtures/               # Shared test fixtures
```

### 6.2. Test Categories

**Unit Tests**:

- Domain function behavior
- Pydantic model validation
- Utility functions
- VCR cassettes for HTTP responses

**CLI Tests**:

- Command invocation
- Argument parsing
- Output formatting
- Error handling

**Integration Tests**:

- Browser flows (login, multi-step workflows)
- Multi-domain workflows (e.g., list leagues → list seasons)
- Configuration resolution
- End-to-end smoke tests

### 6.3. Test Markers

- `@pytest.mark.vcr` — Replays HTTP from cassette
- `@pytest.mark.browser` — Requires headless Chromium (slow, opt-in)

Run fast tests: `pytest -m "not browser"`

## 7. Security Considerations

### 7.1. Token Storage

Tokens are stored in `~/.gamesheet/` with restrictive permissions (0600 on Unix). Tokens are:

- **Access tokens**: Short-lived (hours), used for API requests
- **Refresh tokens**: Long-lived (weeks/months), used to obtain new access tokens

**Risk**: If refresh token is compromised, attacker can obtain access tokens until refresh token expires.

**Mitigation**: Store tokens with restricted filesystem permissions, don't log token values.

### 7.2. Browser State

Browser storage state (cookies + localStorage) is saved to `~/.gamesheet/browser-state.json`. This file contains session cookies that could be used to
impersonate the user.

**Risk**: If browser state is compromised, attacker has same access as logged-in user.

**Mitigation**: Restrict file permissions, clear on logout.

### 7.3. Secrets in Logs

The SDK uses `logging` with care to avoid logging sensitive values:

- Tokens are never logged
- Passwords are never logged
- Email addresses are logged only at INFO level (not in production)

**Guideline**: Use `_LOGGER.debug()` for details, `_LOGGER.info()` for user-visible messages.

## 8. Performance Characteristics

### 8.1. HTTP Operations

- **Latency**: ~100–500ms per request (network-bound)
- **Retries**: 3 retries on transient failures (configurable via `Config.request_retries`)
- **Timeout**: 30s default (configurable via `Config.timeout`)

### 8.2. Browser Operations

- **Startup**: ~500ms to launch Chromium (one-time per session)
- **Page load**: ~1–3s for JavaScript-heavy pages
- **Recommendation**: Minimize browser usage (use HTTP when possible)

### 8.3. Token Refresh

- **Frequency**: Only on HTTP 401 (not proactive)
- **Latency**: ~200–500ms (one HTTP request)
- **Caching**: New access token is saved immediately (subsequent requests use it)

## 9. Future Directions

### 9.1. Planned Features

- **Teams dashboard support**: Full domain modules and CLI commands for the teams dashboard
- **Auth strategy pattern**: `LoginFlow` ABC to support different authentication flows per dashboard
- **ID abstraction**: Admin uses integers, teams may use UUIDs
- **Async support**: `async`/`await` variants of domain functions for concurrent operations
- **Caching layer**: In-memory cache for frequently-accessed resources (leagues, associations)

### 9.2. API Stability

The SDK is **alpha** (0.x.y versions). Breaking changes are possible until 1.0.0. After 1.0.0:

- **Major version bump** (1.x → 2.x): Breaking changes allowed
- **Minor version bump** (1.0 → 1.1): New features, backward compatible
- **Patch version bump** (1.0.0 → 1.0.1): Bug fixes only

See [Release Process](../how-to/release-process.md) for versioning details.

## 10. Related Documentation

- {doc}`why-webui-automation` — Why we automate the WebUI instead of using a public API
- {doc}`../how-to/development-setup` — Setting up a local development environment
- {doc}`../reference/api` — Complete API reference for all modules
- {doc}`../reference/cli` — CLI command reference
