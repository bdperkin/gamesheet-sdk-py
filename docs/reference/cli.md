# Command-line Interface

<!--TOC-->

______________________________________________________________________

- [1. Rich Help Output](#1-rich-help-output)
- [2. Admin CLI](#2-admin-cli)
- [3. Teams CLI](#3-teams-cli)
- [4. Usage Examples](#4-usage-examples)
  - [4.1. Basic authentication](#41-basic-authentication)
  - [4.2. Listing resources](#42-listing-resources)
  - [4.3. Output formats](#43-output-formats)
  - [4.4. Verbose logging](#44-verbose-logging)
  - [4.5. Browser visibility](#45-browser-visibility)
  - [4.6. Shell completion](#46-shell-completion)
- [5. Return Codes](#5-return-codes)
- [6. Environment Variables](#6-environment-variables)
  - [6.1. Supported variables](#61-supported-variables)
  - [6.2. Example usage](#62-example-usage)
- [7. Configuration File Support](#7-configuration-file-support)
- [8. See also](#8-see-also)

______________________________________________________________________

<!--TOC-->

The package installs two console scripts:

- **`gamesheet-admin`** — CLI for the GameSheet admin dashboard (entry point: {func}`gamesheet_sdk.admin.cli.main.main`)
- **`gamesheet-teams`** — CLI for the GameSheet teams dashboard (entry point: {func}`gamesheet_sdk.teams.cli.main.main`)

Both CLIs share common infrastructure (authentication, configuration, output formatting) from {mod}`gamesheet_sdk.common`.

## 1. Rich Help Output

Both CLIs use [rich-click](https://github.com/ewels/rich-click) to provide beautifully formatted help output with:

- **Grouped options** — Configuration and general options are organized into separate sections for clarity
- **Grouped commands** — Commands are categorized (Authentication, Resource Management) for easier navigation
- **Rich formatting** — Tables, borders, and color-coded sections enhance readability
- **Consistent styling** — All help pages follow the same visual design for a polished experience

## 2. Admin CLI

The admin CLI provides full resource management for the GameSheet admin dashboard.

```{eval-rst}
.. click:: gamesheet_sdk.admin.cli.main:cli
    :prog: gamesheet-admin
    :nested: full
```

## 3. Teams CLI

The teams CLI targets the GameSheet teams dashboard. Login is not yet implemented.

```{eval-rst}
.. click:: gamesheet_sdk.teams.cli.main:cli
    :prog: gamesheet-teams
    :nested: full
```

## 4. Usage Examples

Both CLIs follow a resource-oriented (noun-first) command structure. Every resource group supports canonical verbs (`create`, `get`, `list`, `update`, `delete`)
with short aliases (`add`/`new`, `show`/`view`, `ls`, `set`/`edit`, `rm`/`remove`).

### 4.1. Basic authentication

Authenticate with GameSheet and save session tokens:

```console
$ gamesheet-admin login --email user@example.com
Password: [hidden input]
Login successful! Tokens saved.
```

### 4.2. Listing resources

List all associations on your account:

```console
$ gamesheet-admin associations list
ID      TITLE                    CREATED AT
12345   Springfield Youth Hockey 2024-01-15 08:23:45
```

Use the `ls` alias for brevity:

```console
$ gamesheet-admin associations ls
```

List leagues within an association:

```console
$ gamesheet-admin leagues list --association-id 12345
```

### 4.3. Output formats

Change output format using `--format`:

```console
$ gamesheet-admin associations list --format json
$ gamesheet-admin leagues ls --association-id 12345 --format yaml
$ gamesheet-admin seasons list --league-id 111 --format csv > seasons.csv
```

Supported formats: `json`, `yaml`, `csv`, `tsv`, plus thirteen `tabulate` table formats (see `--help` for the full list).

### 4.4. Verbose logging

Enable info-level logging with `-v`, debug-level with `-vv`:

```console
$ gamesheet-admin -v associations list
INFO:gamesheet_sdk.common.session:GET https://gamesheet.app/api/associations
INFO:gamesheet_sdk.common.session:Response: 200 OK
```

The verbosity flag is a global option and must precede the resource name.

### 4.5. Browser visibility

Show the browser window during headless operations (useful for debugging):

```console
$ gamesheet-admin --no-headless login --email user@example.com
```

### 4.6. Shell completion

Generate a completion script for your shell:

```console
$ gamesheet-admin completion bash > ~/.bash_completion.d/gamesheet-admin
$ gamesheet-admin completion zsh > ~/.zsh/completion/_gamesheet-admin
$ gamesheet-admin completion fish > ~/.config/fish/completions/gamesheet-admin.fish
```

Then source the script in your shell configuration file.

## 5. Return Codes

Both CLIs follow Unix exit-code conventions:

| Code | Meaning                                                                                 |
| ---- | --------------------------------------------------------------------------------------- |
| 0    | Success. The command completed without errors.                                          |
| 1    | General error. Authentication failed, resource not found, network error, or user abort. |
| 2    | Usage error. Invalid arguments, missing required options, or unknown command/option.    |

Exit codes are resolved by {func}`gamesheet_sdk.common.cli.core.resolve_exit` and {func}`gamesheet_sdk.common.cli.core.resolve_system_exit` from click
exceptions:

- {class}`click.exceptions.Exit` — mapped to its `exit_code` attribute.
- {class}`click.exceptions.UsageError` — always returns 2 (after displaying the error message).
- {class}`click.exceptions.Abort` — returns 1 (after printing "Aborted.").
- {class}`SystemExit` — mapped to its code (0 if None, 1 if non-integer, otherwise the code itself).

## 6. Environment Variables

Both CLIs read configuration from `GAMESHEET_`-prefixed environment variables via {class}`gamesheet_sdk.common.config.Config` (implemented with
`pydantic-settings`). Values are resolved in this precedence order:

1. Command-line arguments (`--base-url`, `--email`, `--password`, etc.)
2. Environment variables
3. Field defaults defined in {class}`~gamesheet_sdk.common.config.Config`

### 6.1. Supported variables

| Variable                       | Type    | Default                                               | Description                                               |
| ------------------------------ | ------- | ----------------------------------------------------- | --------------------------------------------------------- |
| `GAMESHEET_BASE_URL`           | `str`   | `https://gamesheet.app`                               | Root URL of the GameSheet WebUI.                          |
| `GAMESHEET_USERNAME`           | `str`   | `None`                                                | GameSheet account username/email.                         |
| `GAMESHEET_PASSWORD`           | `str`   | `None`                                                | GameSheet account password (stored as `SecretStr`).       |
| `GAMESHEET_SESSION_PATH`       | `Path`  | `$XDG_CACHE_HOME/gamesheet-sdk-py/session.json`       | Where to persist cookie state between runs.               |
| `GAMESHEET_TIMEOUT`            | `float` | `30.0`                                                | Default per-request HTTP timeout in seconds.              |
| `GAMESHEET_USER_AGENT`         | `str`   | `None`                                                | Override the default User-Agent header.                   |
| `GAMESHEET_VERIFY_SSL`         | `bool`  | `True`                                                | Whether to verify TLS certificates on outgoing requests.  |
| `GAMESHEET_REQUEST_RETRIES`    | `int`   | `3`                                                   | Automatic retries on 5xx responses and connection errors. |
| `GAMESHEET_BROWSER_STATE_PATH` | `Path`  | `$XDG_CACHE_HOME/gamesheet-sdk-py/browser-state.json` | Where to persist Playwright storage state between runs.   |
| `GAMESHEET_BROWSER_HEADLESS`   | `bool`  | `True`                                                | Launch the Playwright browser in headless mode.           |

**Notes:**

- `$XDG_CACHE_HOME` defaults to `~/.cache` on Linux/macOS if the variable is not set. On Windows, the analogous user cache directory is used.
- `GAMESHEET_PASSWORD` is stored as a {class}`pydantic.SecretStr` to prevent accidental logging.
- Boolean environment variables accept `1`/`true`/`yes` (case-insensitive) for True, `0`/`false`/`no` for False.
- The admin CLI defaults `GAMESHEET_BASE_URL` to `https://gamesheet.app`; the teams CLI defaults to `https://teams.gamesheet.app`.

### 6.2. Example usage

```bash
# Authenticate using environment variables instead of prompts
export GAMESHEET_USERNAME="user@example.com"
export GAMESHEET_PASSWORD="secret"  # pragma: allowlist secret
gamesheet-admin login

# Use a custom base URL and increase timeout
export GAMESHEET_BASE_URL="https://custom.gamesheet.app"
export GAMESHEET_TIMEOUT="60.0"
gamesheet-admin associations list

# Disable SSL verification (not recommended for production)
export GAMESHEET_VERIFY_SSL="false"
gamesheet-admin login
```

## 7. Configuration File Support

A TOML configuration file source is **not yet implemented**. Currently, configuration is resolved only from command-line arguments and environment variables.

Future releases may add support for a `~/.config/gamesheet-sdk-py/config.toml` file (XDG-compliant path) by overriding `settings_customise_sources` in
{class}`~gamesheet_sdk.common.config.Config`. When implemented, the precedence order will be:

1. Command-line arguments (highest priority)
2. Environment variables
3. Configuration file
4. Field defaults (lowest priority)

For now, use environment variables or CLI flags to configure the SDK. See the {ref}`reference/cli:Environment Variables` section above for details.

## 8. See also

- {mod}`gamesheet_sdk.admin.cli` — Admin CLI module reference.
- {mod}`gamesheet_sdk.teams.cli` — Teams CLI module reference.
- {doc}`api` — Complete API reference for all SDK modules.
- {doc}`../tutorials/using-cli-commands` — Step-by-step tutorial for using CLI commands.
- {doc}`../how-to/index` — Task-oriented guides for common workflows.
