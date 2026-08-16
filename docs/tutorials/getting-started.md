# Getting started

<!--TOC-->

______________________________________________________________________

- [1. What you will need](#1-what-you-will-need)
- [2. Step 1 — Create an isolated environment](#2-step-1--create-an-isolated-environment)
- [3. Step 2 — Install the SDK](#3-step-2--install-the-sdk)
- [4. Step 3 — Install the Playwright browser](#4-step-3--install-the-playwright-browser)
- [5. Step 4 — Verify the CLI works](#5-step-4--verify-the-cli-works)
- [6. Step 5 — Verify the Python API works](#6-step-5--verify-the-python-api-works)
- [7. Step 6 — Authentication quickstart](#7-step-6--authentication-quickstart)
- [8. Step 7 — Basic usage examples](#8-step-7--basic-usage-examples)
- [9. You're done](#9-youre-done)
- [10. Where to go next](#10-where-to-go-next)

______________________________________________________________________

<!--TOC-->

By the end of this tutorial you will have `gamesheet-sdk-py` installed into a fresh virtual environment, and you will have verified that it works both from the
command line and from Python.

The whole walkthrough should take about five minutes.

## 1. What you will need

- **Python 3.11, 3.12, 3.13, or 3.14** on your PATH. Check with:

  ```console
  $ python --version
  Python 3.12.5
  ```

  If `python` reports an older version, install a supported one before continuing. Other versions are not supported by this SDK.

- A working terminal (any shell will do).

That is the complete list. You do not need a GameSheet account for this tutorial.

## 2. Step 1 — Create an isolated environment

Pick a working directory and create a virtual environment named `.venv` inside it. Then activate it.

```console
$ mkdir gamesheet-firstrun
$ cd gamesheet-firstrun
$ python -m venv .venv
$ source .venv/bin/activate
(.venv) $
```

```{note}
On Windows PowerShell the activation command is `.venv\Scripts\Activate.ps1`
instead of `source .venv/bin/activate`. The rest of this tutorial is the same.
```

The `(.venv)` prefix on your prompt tells you the environment is active. Every command from here on assumes that prefix.

## 3. Step 2 — Install the SDK

Install `gamesheet-sdk-py` from PyPI:

```console
(.venv) $ pip install gamesheet-sdk-py
```

Pip will pull in `requests`, `playwright`, `pydantic`, and `click`. Wait for it to finish.

## 4. Step 3 — Install the Playwright browser

Some SDK workflows drive a headless browser, so you also need the Chromium binary that Playwright manages. Install it now so it's ready when you need it:

```console
(.venv) $ python -m playwright install chromium
```

```{note}
This downloads about 150 MB into your user cache (`~/.cache/ms-playwright/`
on Linux, the analogous location on other OSes). It only happens once per
machine, not per project.
```

## 5. Step 4 — Verify the CLI works

The package installs two console scripts: `gamesheet-admin` (admin dashboard) and `gamesheet-teams` (teams dashboard). Try the admin CLI first:

```console
(.venv) $ gamesheet-admin --version
gamesheet-admin 0.4.27
```

Then ask for its help text:

```console
(.venv) $ gamesheet-admin --help
Usage: gamesheet-admin [OPTIONS] COMMAND [ARGS]...

  Unofficial SDK for the GameSheet Inc. platform.

  Root command group for the GameSheet admin CLI. Automates the GameSheet
  WebUI via headless browser or direct HTTP where a public API is absent.

Options:
  --base-url TEXT         GameSheet base URL (default: https://gamesheet.app)
  --no-headless           Show browser window during Playwright flows
  -v, --verbose           Increase logging verbosity (-v = INFO, -vv = DEBUG)
  --version               Show the version and exit.
  --help                  Show this message and exit.

Commands:
  associations  List, view, and manage associations
  completion    Print shell-completion script for bash / zsh / fish
  divisions     List, view, and manage divisions
  games         List scheduled, completed, and bracket games
  ipad-keys     Retrieve Scoring Access Keys for an association
  leagues       List, view, and manage leagues
  locations     List and manage locations
  login         Authenticate against GameSheet and store tokens
  referees      List, view, and manage referees
  roster        Manage season-level players and coaches
  seasons       List, view, and manage seasons
  teams         List, view, and manage teams
```

If the command prints output and exits cleanly, the CLI is installed correctly.

## 6. Step 5 — Verify the Python API works

The SDK also imports as a Python package. Start the interpreter and ask it for the same version:

```console
(.venv) $ python
>>> import gamesheet_sdk
>>> gamesheet_sdk.__version__
'0.4.27'
>>> exit()
```

If the import succeeded and printed a version string, the package is installed correctly for Python use too.

## 7. Step 6 — Authentication quickstart

Most SDK operations require authentication. The `login` command handles this for you by opening a headless browser, submitting your credentials, and saving the
session tokens for future use.

Try authenticating now (you will need a GameSheet account):

```console
(.venv) $ gamesheet-admin login --email your.email@example.com
Password: [your input is hidden]
Login successful! Tokens saved.
```

```{note}
The password prompt hides your input for security. You can also provide it via the ``--password`` option or the ``GAMESHEET_PASSWORD`` environment
variable, but the interactive prompt is safer.
```

Your authentication tokens and browser state are saved to `$XDG_CACHE_HOME/gamesheet-sdk-py/` (or `~/.cache/gamesheet-sdk-py/` on Linux). Subsequent commands
will use these tokens automatically — no need to log in again until they expire.

If you do not have a GameSheet account yet, you can skip this step. The CLI and Python API verification steps above confirm the SDK is working; you can return
here when you are ready to authenticate.

## 8. Step 7 — Basic usage examples

Once authenticated, you can query GameSheet resources. Try listing the associations on your account:

```console
(.venv) $ gamesheet-admin associations list
ID      Name
------  -------------------------
12345   Example Hockey Association
67890   Another Association
```

You can also use the shorter alias `ls` instead of `list`:

```console
(.venv) $ gamesheet-admin associations ls
```

The CLI supports multiple output formats. Try JSON:

```console
(.venv) $ gamesheet-admin associations list --output json
[
  {
    "id": 12345,
    "name": "Example Hockey Association"
  },
  {
    "id": 67890,
    "name": "Another Association"
  }
]
```

Or YAML:

```console
(.venv) $ gamesheet-admin associations list --output yaml
- id: 12345
  name: Example Hockey Association
- id: 67890
  name: Another Association
```

Each resource (associations, leagues, seasons, etc.) follows the same pattern. Use `--help` on any command to see its options:

```console
(.venv) $ gamesheet-admin leagues --help
(.venv) $ gamesheet-admin seasons list --help
```

## 9. You're done

You have a working `gamesheet-sdk-py` installation. Both the CLI and the Python API are reachable. You have authenticated (or know how to do so when ready), and
you have seen how to query resources and format the output. The version you saw will increase as the SDK gains functionality.

## 10. Where to go next

- {doc}`../how-to/index` — recipes for solving specific tasks against the GameSheet platform.
- {doc}`../reference/index` — the full module-by-module and option-by-option technical description.
- {doc}`../explanation/index` — background on the design choices and the constraints the SDK works within.
