# How to install and smoke-test gamesheet-sdk-py in a GitHub Actions workflow

Drop the snippet below into a workflow file under `.github/workflows/`.
On every push it sets up Python, installs `gamesheet-sdk-py`, restores
the Playwright Chromium binary from cache (or downloads it on a miss),
and confirms the SDK is reachable from both the CLI and a Python
interpreter.

## The workflow

```yaml
name: gamesheet-sdk-py smoke test

on:
  push:
  pull_request:

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install gamesheet-sdk-py
        run: pip install gamesheet-sdk-py

      - name: Cache Playwright browsers
        id: playwright-cache
        uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: playwright-chromium-${{ runner.os }}-${{ hashFiles('**/pyproject.toml') }}

      - name: Install Playwright Chromium
        if: steps.playwright-cache.outputs.cache-hit != 'true'
        run: python -m playwright install --with-deps chromium

      - name: Verify CLI
        run: gamesheet-sdk-py --version

      - name: Verify Python import
        run: python -c "from gamesheet_sdk import __version__; print(__version__)"
```

## What each step is doing for you

- **`cache: pip`** on `setup-python` caches the pip download cache keyed on
  `pyproject.toml`. The SDK reinstalls quickly on subsequent runs.
- **`actions/cache` on `~/.cache/ms-playwright`** is what saves real time:
  Chromium is ~150 MB and would otherwise be re-downloaded on every run.
  The cache key includes `runner.os` because Playwright stores
  OS-specific binaries.
- **`if: steps.playwright-cache.outputs.cache-hit != 'true'`** skips the
  Playwright install step entirely on a cache hit. The browser is already
  on disk; nothing to do.
- **`--with-deps`** asks Playwright to also install the system packages
  Chromium needs (`apt-get install …` on Linux runners). It needs `sudo`,
  which the GitHub-hosted runners grant by default.

## Common adjustments

- **Different Python version.** Change the `python-version` value.
  `gamesheet-sdk-py` supports 3.11, 3.12, 3.13, and 3.14.
- **Matrix of Python versions.** Wrap `runs-on` and the `python-version`
  step in a `strategy.matrix`; the rest of the snippet is unchanged.
- **macOS or Windows runners.** Change `runs-on`. `--with-deps` is a
  Linux-only flag — drop it on macOS and Windows runners.
- **Pinning a specific SDK version.** Replace
  `pip install gamesheet-sdk-py` with
  `pip install 'gamesheet-sdk-py==0.0.1'` (or the version you want).

## See also

- {doc}`../tutorials/getting-started` — the same install flow, walked
  through interactively on a developer workstation.
- {doc}`../reference/cli` — the full set of options the verification
  step can call.
