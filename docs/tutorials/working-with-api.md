# Working with the API

By the end of this tutorial you will have written a Python script that authenticates against GameSheet, retrieves data from multiple resources (associations,
leagues, seasons), and processes the results programmatically.

The whole walkthrough should take about twenty minutes.

## What you will need

- A **working `gamesheet-sdk-py` installation** with a valid login. Complete {doc}`getting-started` and {doc}`authentication-workflow` first if you haven't
  already.
- A **GameSheet account with access to at least one association**. If your account is new and has no associations, some examples in this tutorial will return
  empty results, but you can still follow the structure.
- **Basic Python knowledge** — you should be comfortable with functions, loops, and list comprehensions.

That is the complete list.

## Step 1 — Create a script file

Create a new Python file named `fetch_associations.py`:

```console
(.venv) $ touch fetch_associations.py
```

Open it in your editor. You'll add code to it step by step.

## Step 2 — Import the SDK modules

Start with the imports. You need three modules: `auth` for loading the access token, `session` for making authenticated HTTP requests, and `associations` for
the association-specific logic.

```python
from gamesheet_sdk.auth import load_access_token
from gamesheet_sdk.session import Session
from gamesheet_sdk.associations import list_associations
```

Add this to the top of `fetch_associations.py`.

## Step 3 — Load the access token

The `load_access_token()` function reads the saved token from disk (the one you created in {doc}`authentication-workflow`). Call it and store the result:

```python
token = load_access_token()
```

This will raise an `AuthenticationError` if the token file doesn't exist. If that happens, run `gamesheet-sdk-py login` first.

## Step 4 — Create an authenticated session

The `Session` class is a thin wrapper around `requests.Session` with a `set_bearer_token()` method. Create an instance and attach the token:

```python
session = Session(base_url="https://gamesheet.app")
session.set_bearer_token(token)
```

Now the session carries your credentials on every request.

## Step 5 — Fetch and print associations

Call `list_associations()` with the session, then loop over the results and print them:

```python
associations = list_associations(session)

for assoc in associations:
    print(f"{assoc.title} (ID: {assoc.id})")
```

Your script should now look like this:

```python
from gamesheet_sdk.auth import load_access_token
from gamesheet_sdk.session import Session
from gamesheet_sdk.associations import list_associations

token = load_access_token()
session = Session(base_url="https://gamesheet.app")
session.set_bearer_token(token)

associations = list_associations(session)

for assoc in associations:
    print(f"{assoc.title} (ID: {assoc.id})")
```

## Step 6 — Run the script

Make sure your virtual environment is active, then run the script:

```console
(.venv) $ python fetch_associations.py
Springfield Youth Hockey (ID: 12345)
Tournament Series 2024 (ID: 67890)
```

If it prints your associations, the script is working. If you see `AuthenticationError`, run `gamesheet-sdk-py login` to refresh your tokens.

## Step 7 — Fetch leagues for each association

Now extend the script to fetch leagues for each association. Import the `list_leagues()` function and call it inside the loop:

```python
from gamesheet_sdk.auth import load_access_token
from gamesheet_sdk.session import Session
from gamesheet_sdk.associations import list_associations
from gamesheet_sdk.leagues import list_leagues

token = load_access_token()
session = Session(base_url="https://gamesheet.app")
session.set_bearer_token(token)

associations = list_associations(session)

for assoc in associations:
    print(f"\n{assoc.title} (ID: {assoc.id})")

    leagues = list_leagues(session, association_id=assoc.id)
    for league in leagues:
        print(f"  - {league.name} (League ID: {league.id})")
```

Run it again:

```console
(.venv) $ python fetch_associations.py

Springfield Youth Hockey (ID: 12345)
  - Bantam AA 2024-2025 (League ID: 111)
  - Midget AAA 2024-2025 (League ID: 222)

Tournament Series 2024 (ID: 67890)
  - Elite Division (League ID: 333)
```

Now you're fetching data from two levels of the hierarchy.

## Step 8 — Fetch seasons for each league

Add one more level: seasons. Import `list_seasons()` and call it inside the league loop:

```python
from gamesheet_sdk.auth import load_access_token
from gamesheet_sdk.session import Session
from gamesheet_sdk.associations import list_associations
from gamesheet_sdk.leagues import list_leagues
from gamesheet_sdk.seasons import list_seasons

token = load_access_token()
session = Session(base_url="https://gamesheet.app")
session.set_bearer_token(token)

associations = list_associations(session)

for assoc in associations:
    print(f"\n{assoc.title} (ID: {assoc.id})")

    leagues = list_leagues(session, association_id=assoc.id)
    for league in leagues:
        print(f"  - {league.name} (League ID: {league.id})")

        seasons = list_seasons(session, league_id=league.id)
        for season in seasons:
            print(f"      {season.name} (Season ID: {season.id})")
```

Run it:

```console
(.venv) $ python fetch_associations.py

Springfield Youth Hockey (ID: 12345)
  - Bantam AA 2024-2025 (League ID: 111)
      2024-2025 (Season ID: 555)
  - Midget AAA 2024-2025 (League ID: 222)
      2024-2025 (Season ID: 666)

Tournament Series 2024 (ID: 67890)
  - Elite Division (League ID: 333)
      2024 Summer (Season ID: 777)
```

You've now walked the full hierarchy from associations to leagues to seasons, all with authenticated API calls.

## Step 9 — Access model attributes

Every resource is returned as a Pydantic model, so you can access its attributes by name. For example, the `Association` model has `id`, `title`, `logo`,
`created_at`, and `updated_at` fields. Try printing more details:

```python
for assoc in associations:
    print(f"\n{assoc.title}")
    print(f"  ID: {assoc.id}")
    print(f"  Created: {assoc.created_at}")
    print(f"  Logo: {assoc.logo or '(none)'}")
```

The models are fully typed, so your editor will autocomplete the field names.

## Step 10 — Handle errors

If a request fails (expired token, network error, etc.), the SDK raises an exception. Wrap your API calls in a try-except block to handle errors gracefully:

```python
from gamesheet_sdk.auth import load_access_token
from gamesheet_sdk.session import Session
from gamesheet_sdk.associations import list_associations
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError

try:
    token = load_access_token()
    session = Session(base_url="https://gamesheet.app")
    session.set_bearer_token(token)

    associations = list_associations(session)

    for assoc in associations:
        print(f"{assoc.title} (ID: {assoc.id})")

except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    print("Run 'gamesheet-sdk-py login' to refresh your tokens.")

except GameSheetError as e:
    print(f"API error: {e}")
```

Now if the access token expires, the script prints a helpful message instead of crashing.

## Step 11 — Use the Config class

If you want to customize the base URL or other settings, use the `Config` class instead of hardcoding them:

```python
from gamesheet_sdk.auth import load_access_token
from gamesheet_sdk.session import Session
from gamesheet_sdk.associations import list_associations
from gamesheet_sdk.config import Config

config = Config()  # Reads from environment variables and defaults

token = load_access_token()
session = Session(base_url=config.base_url)
session.set_bearer_token(token)

associations = list_associations(session)

for assoc in associations:
    print(f"{assoc.title} (ID: {assoc.id})")
```

Now if you set `GAMESHEET_BASE_URL` in the environment, the script picks it up automatically.

## You're done

You have written a Python script that authenticates against GameSheet, retrieves data from multiple resources, and processes the results programmatically. The
same pattern works for every resource: load the token, create a session, call the resource-specific function, loop over the results.

## Where to go next

- {doc}`../reference/index` — the full Python API reference, including every module, class, and function.
- {doc}`../how-to/index` — recipes for solving specific tasks, like automating workflows or integrating with other tools.
- {doc}`../explanation/index` — background on why the SDK uses both HTTP and headless browsers, and how the authentication flow works.
