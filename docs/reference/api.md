# API Reference

The {mod}`gamesheet_sdk` package exposes Pythonic wrappers around the GameSheet platform. Complete API documentation for all modules, packages, and subpackages
is generated automatically from source on every documentation build using `sphinx-apidoc`.

## Module index

All Python modules are automatically discovered and documented. Click any module name to view its complete API documentation.

```{eval-rst}
.. autosummary::
    :toctree: _autosummary
    :recursive:

    gamesheet_sdk
    gamesheet_sdk.associations
    gamesheet_sdk.auth
    gamesheet_sdk.browser
    gamesheet_sdk.cli
    gamesheet_sdk.config
    gamesheet_sdk.divisions
    gamesheet_sdk.exceptions
    gamesheet_sdk.ipad_keys
    gamesheet_sdk.leagues
    gamesheet_sdk.output
    gamesheet_sdk.seasons
    gamesheet_sdk.session
    gamesheet_sdk.teams
```

## Core modules

Top-level domain modules and utilities.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk
    _autosummary/gamesheet_sdk.associations
    _autosummary/gamesheet_sdk.browser
    _autosummary/gamesheet_sdk.config
    _autosummary/gamesheet_sdk.divisions
    _autosummary/gamesheet_sdk.exceptions
    _autosummary/gamesheet_sdk.ipad_keys
    _autosummary/gamesheet_sdk.leagues
    _autosummary/gamesheet_sdk.output
    _autosummary/gamesheet_sdk.seasons
    _autosummary/gamesheet_sdk.session
    _autosummary/gamesheet_sdk.teams
```

## Authentication package

Authentication flows, token management, and authenticated HTTP session.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.auth
    _autosummary/gamesheet_sdk.auth.constants
    _autosummary/gamesheet_sdk.auth.login
    _autosummary/gamesheet_sdk.auth.session
    _autosummary/gamesheet_sdk.auth.storage
    _autosummary/gamesheet_sdk.auth.tokens
```

## Command-line interface

CLI framework, resource groups, and command implementations.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.cli
    _autosummary/gamesheet_sdk.cli.core
    _autosummary/gamesheet_sdk.cli.helpers
    _autosummary/gamesheet_sdk.cli.main
    _autosummary/gamesheet_sdk.cli.commands
    _autosummary/gamesheet_sdk.cli.commands.associations
    _autosummary/gamesheet_sdk.cli.commands.completion
    _autosummary/gamesheet_sdk.cli.commands.divisions
    _autosummary/gamesheet_sdk.cli.commands.ipad_keys
    _autosummary/gamesheet_sdk.cli.commands.leagues
    _autosummary/gamesheet_sdk.cli.commands.login
    _autosummary/gamesheet_sdk.cli.commands.season
    _autosummary/gamesheet_sdk.cli.commands.seasons
    _autosummary/gamesheet_sdk.cli.commands.teams
```
