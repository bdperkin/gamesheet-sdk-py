# Command-line Interface

The package installs a `gamesheet-sdk-py` console script whose entry point is {func}`gamesheet_sdk.cli.main`. The subcommand tree below is rendered
live from the click group {data}`gamesheet_sdk.cli.cli` by `sphinx-click`, so the options always match the shipped binary.

```{eval-rst}
.. click:: gamesheet_sdk.cli:cli
    :prog: gamesheet-sdk-py
    :nested: full
```

## See also

- {mod}`gamesheet_sdk.cli` — module reference (auto-generated).
- {ref}`reference/api:submodules` — the click group rendered as a Python API.
