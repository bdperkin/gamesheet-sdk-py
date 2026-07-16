# Configuration Reference

The `gamesheet-sdk-py` package uses `pydantic-settings` for configuration management. Values resolve in this order:

1. Keyword arguments passed to `Config(...)` (or CLI flags like `--base-url`)
2. `GAMESHEET_`-prefixed environment variables
3. Built-in defaults

## Environment Variables

| Variable                       | Purpose                                              | Default                                               |
| ------------------------------ | ---------------------------------------------------- | ----------------------------------------------------- |
| `GAMESHEET_BASE_URL`           | Root URL of the GameSheet WebUI                      | `https://gamesheet.app`                               |
| `GAMESHEET_USERNAME`           | Account email (CLI `--email` overrides)              | _unset_                                               |
| `GAMESHEET_PASSWORD`           | Account password (CLI `--password` overrides)        | _unset_                                               |
| `GAMESHEET_TIMEOUT`            | Default per-request HTTP timeout in seconds          | `30`                                                  |
| `GAMESHEET_REQUEST_RETRIES`    | Auto-retries on 5xx and connection errors            | `3`                                                   |
| `GAMESHEET_USER_AGENT`         | Override the HTTP `User-Agent` header                | requests default                                      |
| `GAMESHEET_VERIFY_SSL`         | TLS certificate verification                         | `true`                                                |
| `GAMESHEET_SESSION_PATH`       | Where to persist cookie state                        | `$XDG_CACHE_HOME/gamesheet-sdk-py/session.json`       |
| `GAMESHEET_BROWSER_STATE_PATH` | Where to persist Playwright storage state            | `$XDG_CACHE_HOME/gamesheet-sdk-py/browser-state.json` |
| `GAMESHEET_BROWSER_HEADLESS`   | Launch Playwright in headless mode (`--no-headless`) | `true`                                                |

## Usage Examples

### Python API

```python
from gamesheet_sdk import Config

# Use defaults
config = Config()

# Override via kwargs
config = Config(base_url="https://gamesheet.app", timeout=60, request_retries=5)

# Mix env vars and kwargs (kwargs take precedence)
import os

os.environ["GAMESHEET_TIMEOUT"] = "45"
config = Config(timeout=60)  # Uses 60, not 45
```

### CLI

```bash
# Use env vars
export GAMESHEET_USERNAME=you@example.com
export GAMESHEET_PASSWORD=secret
gamesheet-admin login

# Override with flags
gamesheet-admin --base-url https://custom.gamesheet.app login --email you@example.com
```

## Session Storage

The package persists authentication state in two files:

- **`session.json`** — HTTP session cookies and bearer tokens
- **`browser-state.json`** — Playwright storage state (cookies, localStorage, sessionStorage)

Default location: `$XDG_CACHE_HOME/gamesheet-sdk-py/` (typically `~/.cache/gamesheet-sdk-py/` on Linux/macOS).

Override via:

```bash
export GAMESHEET_SESSION_PATH=~/.config/gamesheet/session.json
export GAMESHEET_BROWSER_STATE_PATH=~/.config/gamesheet/browser-state.json
```

## SSL/TLS Verification

By default, SSL certificate verification is enabled. To disable (not recommended for production):

```bash
export GAMESHEET_VERIFY_SSL=false
```

Or in Python:

```python
config = Config(verify_ssl=False)
```
