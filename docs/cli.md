# Command-line Interface

The package installs a `gamesheet-sdk-py` console script whose entry point is
{func}`gamesheet_sdk.cli.main`. The options below are rendered live from
{func}`gamesheet_sdk.cli.build_parser` by `sphinx-argparse`, so they always
match the shipped binary.

```{eval-rst}
.. argparse::
    :module: gamesheet_sdk.cli
    :func: build_parser
    :prog: gamesheet-sdk-py
```

## See also

- {mod}`gamesheet_sdk.cli` — module reference (auto-generated).
- {ref}`api:submodules` — the same parser rendered as a Python API.
