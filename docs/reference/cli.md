# Command-line Interface

The package installs a `gamesheet-sdk-py` console script whose entry point is {func}`gamesheet_sdk.cli.main`. The subcommand tree below is rendered live from
the click group {data}`gamesheet_sdk.cli.cli` by `sphinx-click`, so the options always match the shipped binary.

```{eval-rst}
.. click:: gamesheet_sdk.cli:cli
    :prog: gamesheet-sdk-py
    :nested: full
```

## Usage Examples

The CLI follows a resource-oriented (noun-first) command structure. Every resource group supports canonical verbs (`create`, `get`, `list`, `update`, `delete`)
with short aliases (`add`/`new`, `show`/`view`, `ls`, `set`/`edit`, `rm`/`remove`).

### Basic authentication

Authenticate with GameSheet and save session tokens:

```console
$ gamesheet-sdk-py login --email user@example.com
Password: [hidden input]
Login successful! Tokens saved.
```

### Listing resources

List all associations on your account:

```console
$ gamesheet-sdk-py associations list
ID      TITLE                    CREATED AT
12345   Springfield Youth Hockey 2024-01-15 08:23:45
```

Use the `ls` alias for brevity:

```console
$ gamesheet-sdk-py associations ls
```

List leagues within an association:

```console
$ gamesheet-sdk-py leagues list --association-id 12345
```

### Output formats

Change output format using `--format`:

```console
$ gamesheet-sdk-py associations list --format json
$ gamesheet-sdk-py leagues ls --association-id 12345 --format yaml
$ gamesheet-sdk-py seasons list --league-id 111 --format csv > seasons.csv
```

Supported formats: `json`, `yaml`, `csv`, `tsv`, plus thirteen `tabulate` table formats (see `--help` for the full list).

### Verbose logging

Enable info-level logging with `-v`, debug-level with `-vv`:

```console
$ gamesheet-sdk-py -v associations list
INFO:gamesheet_sdk.session:GET https://gamesheet.app/api/associations
INFO:gamesheet_sdk.session:Response: 200 OK
```

The verbosity flag is a global option and must precede the resource name.

### Browser visibility

Show the browser window during headless operations (useful for debugging):

```console
$ gamesheet-sdk-py --no-headless login --email user@example.com
```

### Shell completion

Generate a completion script for your shell:

```console
$ gamesheet-sdk-py completion bash > ~/.bash_completion.d/gamesheet-sdk-py
$ gamesheet-sdk-py completion zsh > ~/.zsh/completion/_gamesheet-sdk-py
$ gamesheet-sdk-py completion fish > ~/.config/fish/completions/gamesheet-sdk-py.fish
```

Then source the script in your shell configuration file.

## Return Codes

The CLI follows Unix exit-code conventions:

| Code | Meaning                                                                                 |
| ---- | --------------------------------------------------------------------------------------- |
| 0    | Success. The command completed without errors.                                          |
| 1    | General error. Authentication failed, resource not found, network error, or user abort. |
| 2    | Usage error. Invalid arguments, missing required options, or unknown command/option.    |

Exit codes are resolved by {func}`gamesheet_sdk.cli.core.resolve_exit` and {func}`gamesheet_sdk.cli.core.resolve_system_exit` from click exceptions:

- {class}`click.exceptions.Exit` — mapped to its `exit_code` attribute.
- {class}`click.exceptions.UsageError` — always returns 2 (after displaying the error message).
- {class}`click.exceptions.Abort` — returns 1 (after printing "Aborted.").
- {class}`SystemExit` — mapped to its code (0 if None, 1 if non-integer, otherwise the code itself).

## Environment Variables

The CLI reads configuration from `GAMESHEET_`-prefixed environment variables via {class}`gamesheet_sdk.config.Config` (implemented with `pydantic-settings`).
Values are resolved in this precedence order:

1. Command-line arguments (`--base-url`, `--email`, `--password`, etc.)
2. Environment variables
3. Field defaults defined in {class}`~gamesheet_sdk.config.Config`

### Supported variables

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

### Example usage

```bash
# Authenticate using environment variables instead of prompts
export GAMESHEET_USERNAME="user@example.com"
export GAMESHEET_PASSWORD="secret"
gamesheet-sdk-py login

# Use a custom base URL and increase timeout
export GAMESHEET_BASE_URL="https://custom.gamesheet.app"
export GAMESHEET_TIMEOUT="60.0"
gamesheet-sdk-py associations list

# Disable SSL verification (not recommended for production)
export GAMESHEET_VERIFY_SSL="false"
gamesheet-sdk-py login
```

## Configuration File Support

A TOML configuration file source is **not yet implemented**. Currently, configuration is resolved only from command-line arguments and environment variables.

Future releases may add support for a `~/.config/gamesheet-sdk-py/config.toml` file (XDG-compliant path) by overriding `settings_customise_sources` in
{class}`~gamesheet_sdk.config.Config`. When implemented, the precedence order will be:

1. Command-line arguments (highest priority)
2. Environment variables
3. Configuration file
4. Field defaults (lowest priority)

For now, use environment variables or CLI flags to configure the SDK. See the {ref}`reference/cli:Environment Variables` section above for details.

## See also

- {mod}`gamesheet_sdk.cli` — CLI module reference with full API documentation.
- {doc}`api` — Complete API reference for all SDK modules.
- {doc}`../tutorials/using-cli-commands` — Step-by-step tutorial for using CLI commands.
- {doc}`../how-to/index` — Task-oriented guides for common workflows.
