# Getting started

By the end of this tutorial you will have `gamesheet-sdk-py` installed into a fresh virtual environment, and you will have verified that it works both
from the command line and from Python.

The whole walkthrough should take about five minutes.

## What you will need

- **Python 3.11, 3.12, 3.13, or 3.14** on your PATH. Check with:

  ```console
  $ python --version
  Python 3.12.5
  ```

  If `python` reports an older version, install a supported one before continuing. Other versions are not supported by this SDK.

- A working terminal (any shell will do).

That is the complete list. You do not need a GameSheet account for this tutorial.

## Step 1 — Create an isolated environment

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

## Step 2 — Install the SDK

Install `gamesheet-sdk-py` from PyPI:

```console
(.venv) $ pip install gamesheet-sdk-py
```

Pip will pull in `requests`, `playwright`, `pydantic`, and `click`. Wait for it to finish.

## Step 3 — Install the Playwright browser

Some SDK workflows drive a headless browser, so you also need the Chromium binary that Playwright manages. Install it now so it's ready when you need
it:

```console
(.venv) $ python -m playwright install chromium
```

```{note}
This downloads about 150 MB into your user cache (`~/.cache/ms-playwright/`
on Linux, the analogous location on other OSes). It only happens once per
machine, not per project.
```

## Step 4 — Verify the CLI works

The package installs a console script named `gamesheet-sdk-py`. Ask it for its version:

```console
(.venv) $ gamesheet-sdk-py --version
gamesheet-sdk-py 0.0.1
```

Then ask for its help text:

```console
(.venv) $ gamesheet-sdk-py --help
usage: gamesheet-sdk-py [-h] [--version]

Unofficial CLI for the GameSheet Inc. platform.

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
```

If both commands print output and exit cleanly, the CLI is installed correctly.

## Step 5 — Verify the Python API works

The SDK also imports as a Python package. Start the interpreter and ask it for the same version:

```console
(.venv) $ python
>>> from gamesheet_sdk import __version__
>>> __version__
'0.0.1'
>>> exit()
```

If the import succeeded and printed a version string, the package is installed correctly for Python use too.

## You're done

You have a working `gamesheet-sdk-py` installation. Both the CLI and the Python API are reachable. The version you saw will increase as the SDK gains
functionality.

## Where to go next

- {doc}`../how-to/index` — recipes for solving specific tasks against the GameSheet platform.
- {doc}`../reference/index` — the full module-by-module and option-by-option technical description.
- {doc}`../explanation/index` — background on the design choices and the constraints the SDK works within.
