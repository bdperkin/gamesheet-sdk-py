# Authentication workflow

By the end of this tutorial you will have logged in to GameSheet using the SDK, stored your credentials securely, and verified that the authentication tokens
work both from the CLI and from Python.

The whole walkthrough should take about ten minutes.

## What you will need

- A **GameSheet account** with login credentials (email and password). If you don't have one, visit [gamesheet.app](https://gamesheet.app) to create an account.
- A working `gamesheet-sdk-py` installation. If you haven't installed it yet, complete {doc}`getting-started` first.

That is the complete list.

## Step 1 — Run the login command

The `login` command opens a headless browser, navigates to the GameSheet login page, submits your credentials, and saves the authentication tokens to disk.

```console
(.venv) $ gamesheet-sdk-py login
Email: your-email@example.com
Password:
```

Type your email address and press Enter. Then type your password and press Enter again. The password input is hidden for security.

```{note}
The login flow runs in a headless Chromium browser, so you won't see a window. If you want to watch what's happening, add `--no-headless`:

    $ gamesheet-sdk-py --no-headless login
```

## Step 2 — Wait for the login to complete

The SDK navigates to the login page, fills in the form, and waits for GameSheet to redirect to the dashboard. This takes a few seconds. When it finishes, you'll
see:

```console
Login successful. Tokens saved to /home/you/.config/gamesheet-sdk-py/
```

The exact path depends on your operating system. On Linux it's `~/.config/gamesheet-sdk-py/`, on macOS it's `~/Library/Application Support/gamesheet-sdk-py/`,
and on Windows it's `%LOCALAPPDATA%\gamesheet-sdk-py\`.

## Step 3 — Verify the tokens were saved

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

## Step 4 — Use the access token from the CLI

Now that you're logged in, try listing your associations. This command reads the saved access token and makes an authenticated API request:

```console
(.venv) $ gamesheet-sdk-py associations list
ID      TITLE                    CREATED AT
12345   Springfield Youth Hockey 2024-01-15 08:23:45
67890   Tournament Series 2024   2024-03-22 14:12:03
```

The output format depends on your associations. If the list is empty, your account doesn't have access to any associations yet.

## Step 5 — Use the access token from Python

The Python API has the same authentication story. Import the `load_access_token` function and use it to create an authenticated session:

```console
(.venv) $ python
>>> from gamesheet_sdk.auth import load_access_token
>>> from gamesheet_sdk.session import Session
>>> from gamesheet_sdk.associations import list_associations
>>>
>>> token = load_access_token()
>>> session = Session(base_url="https://gamesheet.app")
>>> session.set_bearer_token(token)
>>>
>>> associations = list_associations(session)
>>> for a in associations:
...     print(f"{a.title} (ID: {a.id})")
...
Springfield Youth Hockey (ID: 12345)
Tournament Series 2024 (ID: 67890)
>>> exit()
```

If the code above printed your associations, authentication is working from Python too.

## Step 6 — Use environment variables instead of interactive prompts

If you're running the SDK in a script or CI environment, you can skip the interactive prompts by setting two environment variables:

```console
(.venv) $ export GAMESHEET_USERNAME=your-email@example.com
(.venv) $ export GAMESHEET_PASSWORD=your-password
(.venv) $ gamesheet-sdk-py login
Login successful. Tokens saved to /home/you/.config/gamesheet-sdk-py/
```

The `login` command reads `GAMESHEET_USERNAME` and `GAMESHEET_PASSWORD` first. If they're set, it skips the prompts. If they're not set, it falls back to asking
you.

```{warning}
Do not hardcode your password in a shell script or commit it to version control. Use a secret manager or environment file instead.
```

## You're done

You have logged in to GameSheet, stored your authentication tokens, and verified that they work from both the CLI and Python. The access token expires after a
few hours, but the SDK refreshes it automatically using the refresh token whenever you run a command.

## Where to go next

- {doc}`using-cli-commands` — explore the other CLI commands for associations, leagues, seasons, and more.
- {doc}`working-with-api` — build Python scripts that automate GameSheet workflows.
- {doc}`../reference/index` — detailed documentation of every module, function, and option.
