# Authentication workflow

<!--TOC-->

______________________________________________________________________

- [1. What you will need](#1-what-you-will-need)
- [2. Step 1 — Run the login command](#2-step-1--run-the-login-command)
- [3. Step 2 — Wait for the login to complete](#3-step-2--wait-for-the-login-to-complete)
- [4. Step 3 — Verify the tokens were saved](#4-step-3--verify-the-tokens-were-saved)
- [5. Step 4 — Use the access token from the CLI](#5-step-4--use-the-access-token-from-the-cli)
- [6. Step 5 — Use the access token from Python](#6-step-5--use-the-access-token-from-python)
- [7. Step 6 — Use environment variables instead of interactive prompts](#7-step-6--use-environment-variables-instead-of-interactive-prompts)
- [8. You're done](#8-youre-done)
- [9. Where to go next](#9-where-to-go-next)

______________________________________________________________________

<!--TOC-->

By the end of this tutorial you will have logged in to GameSheet using the SDK, stored your credentials securely, and verified that the authentication tokens
work both from the CLI and from Python.

The whole walkthrough should take about ten minutes.

## 1. What you will need

- A **GameSheet account** with login credentials (email and password). If you don't have one, visit [gamesheet.app](https://gamesheet.app) to create an account.
- A working `gamesheet-sdk-py` installation. If you haven't installed it yet, complete {doc}`getting-started` first.

That is the complete list.

## 2. Step 1 — Run the login command

The `login` command opens a headless browser, navigates to the GameSheet login page, submits your credentials, and saves the authentication tokens to disk.

```console
(.venv) $ gamesheet-admin login
Email: your-email@example.com
Password:
```

Type your email address and press Enter. Then type your password and press Enter again. The password input is hidden for security.

```{note}
The login flow runs in a headless Chromium browser, so you won't see a window. If you want to watch what's happening, add `--no-headless`:

    $ gamesheet-admin --no-headless login
```

## 3. Step 2 — Wait for the login to complete

The SDK navigates to the login page, fills in the form, and waits for GameSheet to redirect to the dashboard. This takes a few seconds. When it finishes, you'll
see:

```console
Login successful. Tokens saved to /home/you/.config/gamesheet-sdk-py/
```

The exact path depends on your operating system. On Linux it's `~/.config/gamesheet-sdk-py/`, on macOS it's `~/Library/Application Support/gamesheet-sdk-py/`,
and on Windows it's `%LOCALAPPDATA%\gamesheet-sdk-py\`.

## 4. Step 3 — Verify the tokens were saved

List the contents of the config directory:

```console
(.venv) $ ls ~/.config/gamesheet-sdk-py/
access_token  browser_state  refresh_token
```

You should see three items:

- `access_token` — The bearer token for API requests. Expires after a few hours.
- `refresh_token` — A long-lived token used to get a new access token when the old one expires.
- `browser_state` — The saved browser session (cookies, localStorage, etc.). Used to avoid re-login.

All three are plain text files. You can inspect them with `cat`, but do not share them — they grant full access to your GameSheet account.

## 5. Step 4 — Use the access token from the CLI

Now that you're logged in, try listing your associations. This command reads the saved access token and makes an authenticated API request:

```console
(.venv) $ gamesheet-admin associations list
ID      TITLE                    CREATED AT
12345   Springfield Youth Hockey 2024-01-15 08:23:45
67890   Tournament Series 2024   2024-03-22 14:12:03
```

The output format depends on your associations. If the list is empty, your account doesn't have access to any associations yet.

## 6. Step 5 — Use the access token from Python

The Python API provides direct top-level access to authentication and session management. Import `load_access_token` and `AuthenticatedSession`:

```console
(.venv) $ python
>>> from gamesheet_sdk import (
...     AuthenticatedSession,
...     Config,
...     list_associations,
...     load_access_token,
...     load_refresh_token,
...     save_tokens,
... )
>>>
>>> config = Config()
>>> access = load_access_token(config)
>>> refresh = load_refresh_token(config)
>>>
>>> with AuthenticatedSession(
...     config,
...     access_token=access or "",
...     refresh_token=refresh or "",
...     on_refresh=lambda tokens: save_tokens(config, **tokens),
... ) as session:
...     associations = list_associations(session)
...     for a in associations:
...         print(f"{a.title} (ID: {a.id})")
...
Springfield Youth Hockey (ID: 12345)
Tournament Series 2024 (ID: 67890)
>>> exit()
```

If the code above printed your associations, authentication is working from Python too.

## 7. Step 6 — Use environment variables instead of interactive prompts

If you're running the SDK in a script or CI environment, you can skip the interactive prompts by setting two environment variables:

```console
(.venv) $ export GAMESHEET_USERNAME=your-email@example.com
(.venv) $ export GAMESHEET_PASSWORD=your-password
(.venv) $ gamesheet-admin login
Login successful. Tokens saved to /home/you/.config/gamesheet-sdk-py/
```

The `login` command reads `GAMESHEET_USERNAME` and `GAMESHEET_PASSWORD` first. If they're set, it skips the prompts. If they're not set, it falls back to asking
you.

```{warning}
Do not hardcode your password in a shell script or commit it to version control. Use a secret manager or environment file instead.
```

## 8. You're done

You have logged in to GameSheet, stored your authentication tokens, and verified that they work from both the CLI and Python. The access token expires after a
few hours, but the SDK refreshes it automatically using the refresh token whenever you run a command.

## 9. Where to go next

- {doc}`using-cli-commands` — explore the other CLI commands for associations, leagues, seasons, and more.
- {doc}`working-with-api` — build Python scripts that automate GameSheet workflows.
- {doc}`../reference/index` — detailed documentation of every module, function, and option.
