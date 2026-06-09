# Using CLI commands

By the end of this tutorial you will have explored the `gamesheet-sdk-py` CLI's resource-oriented command structure, retrieved data from multiple GameSheet
resources, and formatted the output in different ways.

The whole walkthrough should take about fifteen minutes.

## What you will need

- A **working `gamesheet-sdk-py` installation** with a valid login. Complete {doc}`getting-started` and {doc}`authentication-workflow` first if you haven't
  already.
- A **GameSheet account with access to at least one association**. If your account is new and has no associations, some commands in this tutorial will return
  empty results.

That is the complete list.

## Step 1 — Understand the command structure

The CLI is organized around **resources** (nouns) and **verbs** (actions on those resources). Every command follows the pattern:

```console
gamesheet-sdk-py [global-options] <resource> <verb> [arguments]
```

For example, to list associations, you would run:

```console
(.venv) $ gamesheet-sdk-py associations list
```

The resource is `associations`, and the verb is `list`. Most resources support these verbs:

- `list` (alias: `ls`) — Show all items.
- `get` (alias: `show`, `view`) — Show details of a single item by ID.
- `create` (alias: `add`, `new`) — Create a new item (not yet implemented for most resources).
- `update` (alias: `set`, `edit`) — Update an existing item (not yet implemented for most resources).
- `delete` (alias: `rm`, `remove`) — Delete an item (not yet implemented for most resources).

## Step 2 — List your associations

Start with the top-level resource: associations. An association is the highest organizational unit in GameSheet (a league operator, a tournament series, etc.).

```console
(.venv) $ gamesheet-sdk-py associations list
ID      TITLE                    CREATED AT
12345   Springfield Youth Hockey 2024-01-15 08:23:45
67890   Tournament Series 2024   2024-03-22 14:12:03
```

The default output is a simple table. If your account has no associations, the output will be empty. That's fine — you can still follow the rest of this
tutorial to see how the commands work.

## Step 3 — Use an alias for list

Most verbs have short aliases to save typing. The `list` verb has an alias `ls`, so these two commands are identical:

```console
(.venv) $ gamesheet-sdk-py associations ls
ID      TITLE                    CREATED AT
12345   Springfield Youth Hockey 2024-01-15 08:23:45
67890   Tournament Series 2024   2024-03-22 14:12:03
```

The output is the same. You can use whichever form you prefer.

## Step 4 — Change the output format

The SDK supports thirteen different table formats (via the `tabulate` library), plus JSON, YAML, CSV, and TSV. Change the format with `--format`:

```console
(.venv) $ gamesheet-sdk-py associations list --format json
[
  {
    "id": "12345",
    "title": "Springfield Youth Hockey",
    "logo": "",
    "created_at": "2024-01-15T08:23:45",
    "updated_at": "2024-01-15T08:23:45"
  },
  {
    "id": "67890",
    "title": "Tournament Series 2024",
    "logo": "",
    "created_at": "2024-03-22T14:12:03",
    "updated_at": "2024-03-22T14:12:03"
  }
]
```

JSON output includes all fields, not just the ones shown in the table. Try `--format yaml` or `--format csv` to see other formats.

## Step 5 — List leagues under an association

Associations contain leagues. To list the leagues in an association, you need the association ID from the previous step. Pick one and run:

```console
(.venv) $ gamesheet-sdk-py leagues list --association-id 12345
ID      NAME                     SEASON
111     Bantam AA 2024-2025      2024-2025
222     Midget AAA 2024-2025     2024-2025
```

The `--association-id` argument is required. If you omit it, the command will fail with an error message.

## Step 6 — List seasons under a league

Leagues contain seasons. To list the seasons in a league, you need the league ID from the previous step:

```console
(.venv) $ gamesheet-sdk-py seasons list --league-id 111
ID      NAME          START DATE   END DATE
555     2024-2025     2024-09-01   2025-04-30
```

The `--league-id` argument is required.

## Step 7 — Get detailed season information

Once you have a season ID, you can retrieve detailed information about that season with the `seasons get` command:

```console
(.venv) $ gamesheet-sdk-py seasons get --season-id 555
ID: 555
Name: 2024-2025
Start: 2024-09-01
End: 2025-04-30
League ID: 111
```

The `get` verb shows more detail than `list`, and the output is formatted for readability rather than compactness.

## Step 8 — Retrieve iPad Scoring Access Keys

GameSheet provides Scoring Access Keys (numeric PINs) for scorekeepers using iPads at the rink. To retrieve the keys for a season, use the `ipad-keys` command:

```console
(.venv) $ gamesheet-sdk-py ipad-keys list --season-id 555
TEAM NAME                PIN
Red Wings U15            1234
Blue Stars U15           5678
```

This command requires a browser (it scrapes the keys from the WebUI), so it may take a few seconds longer than the JSON:API commands.

## Step 9 — Use verbose logging to debug

If a command fails or takes longer than expected, add `-v` (or `-vv` for even more detail) to see what the SDK is doing:

```console
(.venv) $ gamesheet-sdk-py -v associations list
INFO:gamesheet_sdk.session:GET https://gamesheet.app/api/associations
INFO:gamesheet_sdk.session:Response: 200 OK
ID      TITLE                    CREATED AT
12345   Springfield Youth Hockey 2024-01-15 08:23:45
67890   Tournament Series 2024   2024-03-22 14:12:03
```

The `-v` flag goes **before** the resource name, because it's a global option. Use `-vv` to enable debug-level logging, which shows request headers, response
bodies, and Playwright browser events.

## Step 10 — Save output to a file

The SDK writes to stdout by default, so you can redirect the output to a file with standard shell redirection:

```console
(.venv) $ gamesheet-sdk-py associations list --format csv > associations.csv
(.venv) $ cat associations.csv
id,title,logo,created_at,updated_at
12345,Springfield Youth Hockey,,2024-01-15T08:23:45,2024-01-15T08:23:45
67890,Tournament Series 2024,,2024-03-22T14:12:03,2024-03-22T14:12:03
```

This works with any output format. Use `--format json > data.json` to save JSON, `--format yaml > data.yaml` to save YAML, etc.

## You're done

You have explored the CLI's resource-oriented command structure, retrieved data from associations, leagues, seasons, and iPad keys, and formatted the output in
multiple ways. The CLI is designed to be predictable: once you know the pattern for one resource, you know the pattern for all of them.

## Where to go next

- {doc}`working-with-api` — use the Python API to build scripts that automate multi-step workflows.
- {doc}`../reference/index` — the full CLI reference, including every option and every output format.
- {doc}`../explanation/index` — background on why the SDK uses both HTTP and headless browsers, and how authentication works.
