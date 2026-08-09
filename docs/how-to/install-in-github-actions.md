# How to install and smoke-test gamesheet-sdk-py in a GitHub Actions workflow

Drop the snippet below into a workflow file under `.github/workflows/`. On every push it sets up Python, installs `gamesheet-sdk-py`, and confirms the SDK is
reachable from both the CLI and a Python interpreter.

## 1. The workflow

```yaml
name: gamesheet-sdk-py smoke test

on:
  push:

  pull_request:
    types: [opened, reopened]

concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.ref_name }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: pyproject.toml

      - name: Install gamesheet-sdk-py
        run: pip install gamesheet-sdk-py

      - name: Verify CLI
        run: gamesheet-admin --version

      - name: Verify Python import
        run: python -c "from gamesheet_sdk import __version__; print(__version__)"
```

## 2. What each step is doing for you

- **`cache: pip`** on `setup-python` caches the pip download cache. Combined with `cache-dependency-path: pyproject.toml`, it keys the cache on the package's
  dependency specification. The SDK reinstalls quickly on subsequent runs.
- **`pull_request: types: [opened, reopened]`** scopes PR triggers to only when a PR is first opened or reopened. This prevents duplicate runs on every push to
  a PR branch (which would already fire via the `push:` trigger).
- **`concurrency` with `cancel-in-progress: true`** ensures that if a new push arrives while a workflow is running, the older run is canceled. This saves CI
  minutes and prevents stale runs from clogging the queue.

## 3. Playwright browser installation (optional)

The project includes Playwright for browser-driven workflows, but **tests in CI run with VCR cassettes** (`pytest-recording`) and do not require live browser
automation. If you need to run browser-based code paths (e.g., when testing the `login()` flow with `--no-headless` or invoking `@pytest.mark.browser` tests),
add Playwright installation:

```yaml
- name: Cache Playwright browsers
  id: playwright-cache
  uses: actions/cache@v4
  with:
    path: ~/.cache/ms-playwright
    key: playwright-chromium-${{ runner.os }}-${{ hashFiles('pyproject.toml') }}

- name: Install Playwright Chromium
  if: steps.playwright-cache.outputs.cache-hit != 'true'
  run: python -m playwright install --with-deps chromium
```

- **`actions/cache` on `~/.cache/ms-playwright`** saves real time: Chromium is ~150 MB and would otherwise be re-downloaded on every run. The cache key includes
  `runner.os` because Playwright stores OS-specific binaries.
- **`if: steps.playwright-cache.outputs.cache-hit != 'true'`** skips the Playwright install step entirely on a cache hit. The browser is already on disk;
  nothing to do.
- **`--with-deps`** asks Playwright to also install the system packages Chromium needs (`apt-get install …` on Linux runners). It needs `sudo`, which the
  GitHub-hosted runners grant by default.

## 4. Matrix testing across Python versions

The project supports Python 3.11–3.14. To test across all supported versions, use a matrix strategy:

```yaml
jobs:
  smoke:
    name: smoke (py${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13", "3.14"]
    steps:
      - uses: actions/checkout@v6

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: pyproject.toml

      - name: Install gamesheet-sdk-py
        run: pip install gamesheet-sdk-py

      - name: Verify CLI
        run: gamesheet-admin --version

      - name: Verify Python import
        run: python -c "from gamesheet_sdk import __version__; print(__version__)"
```

- **`fail-fast: false`** ensures that if one Python version fails, the others still run to completion — useful for spotting version-specific issues.
- **`name: smoke (py${{ matrix.python-version }})`** gives each job a unique display name in the GitHub Actions UI (e.g., `smoke (py3.11)`, `smoke (py3.12)`).

## 5. Common adjustments

- **Different Python version.** Change the `python-version` value. `gamesheet-sdk-py` supports 3.11, 3.12, 3.13, and 3.14.
- **macOS or Windows runners.** Change `runs-on`. `--with-deps` (for Playwright) is a Linux-only flag — drop it on macOS and Windows runners.
- **Pinning a specific SDK version.** Replace `pip install gamesheet-sdk-py` with `pip install 'gamesheet-sdk-py==0.0.1'` (or the version you want).

## 6. See also

- {doc}`../tutorials/getting-started` — the same install flow, walked through interactively on a developer workstation.
- {doc}`../reference/cli` — the full set of options the verification step can call.
