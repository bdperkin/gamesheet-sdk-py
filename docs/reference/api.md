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
    gamesheet_sdk.constants
    gamesheet_sdk.divisions
    gamesheet_sdk.errors
    gamesheet_sdk.exceptions
    gamesheet_sdk.games
    gamesheet_sdk.ipad_keys
    gamesheet_sdk.leagues
    gamesheet_sdk.output
    gamesheet_sdk.referees
    gamesheet_sdk.roster
    gamesheet_sdk.seasons
    gamesheet_sdk.session
    gamesheet_sdk.shared
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
    _autosummary/gamesheet_sdk.constants
    _autosummary/gamesheet_sdk.divisions
    _autosummary/gamesheet_sdk.errors
    _autosummary/gamesheet_sdk.exceptions
    _autosummary/gamesheet_sdk.ipad_keys
    _autosummary/gamesheet_sdk.leagues
    _autosummary/gamesheet_sdk.output
    _autosummary/gamesheet_sdk.referees
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

## Games package

Game retrieval and management for scheduled, completed, and bracket games.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.games
    _autosummary/gamesheet_sdk.games.brackets
    _autosummary/gamesheet_sdk.games.broadcasters
    _autosummary/gamesheet_sdk.games.completed
    _autosummary/gamesheet_sdk.games.helpers
    _autosummary/gamesheet_sdk.games.locations
    _autosummary/gamesheet_sdk.games.models
    _autosummary/gamesheet_sdk.games.scheduled
```

## Roster package

Player and coach roster management.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.roster
    _autosummary/gamesheet_sdk.roster.coaches
    _autosummary/gamesheet_sdk.roster.helpers
    _autosummary/gamesheet_sdk.roster.models
    _autosummary/gamesheet_sdk.roster.players
```

## Shared utilities

Shared utilities and helpers used across the SDK.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.shared
    _autosummary/gamesheet_sdk.shared.constants
    _autosummary/gamesheet_sdk.shared.gamesheet_http
    _autosummary/gamesheet_sdk.shared.image_upload
    _autosummary/gamesheet_sdk.shared.jsonapi
```

## Command-line interface

CLI framework, resource groups, and command implementations.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.cli
    _autosummary/gamesheet_sdk.cli.constants
    _autosummary/gamesheet_sdk.cli.core
    _autosummary/gamesheet_sdk.cli.helpers
    _autosummary/gamesheet_sdk.cli.main
    _autosummary/gamesheet_sdk.cli.shared
    _autosummary/gamesheet_sdk.cli.shared.datetime_helpers
    _autosummary/gamesheet_sdk.cli.shared.decorators
    _autosummary/gamesheet_sdk.cli.shared.rendering
    _autosummary/gamesheet_sdk.cli.commands
    _autosummary/gamesheet_sdk.cli.commands.associations
    _autosummary/gamesheet_sdk.cli.commands.completion
    _autosummary/gamesheet_sdk.cli.commands.divisions
    _autosummary/gamesheet_sdk.cli.commands.games
    _autosummary/gamesheet_sdk.cli.commands.games_brackets
    _autosummary/gamesheet_sdk.cli.commands.games_completed
    _autosummary/gamesheet_sdk.cli.commands.games_scheduled
    _autosummary/gamesheet_sdk.cli.commands.ipad_keys
    _autosummary/gamesheet_sdk.cli.commands.leagues
    _autosummary/gamesheet_sdk.cli.commands.locations
    _autosummary/gamesheet_sdk.cli.commands.login
    _autosummary/gamesheet_sdk.cli.commands.referees
    _autosummary/gamesheet_sdk.cli.commands.roster
    _autosummary/gamesheet_sdk.cli.commands.roster_coaches
    _autosummary/gamesheet_sdk.cli.commands.roster_players
    _autosummary/gamesheet_sdk.cli.commands.season
    _autosummary/gamesheet_sdk.cli.commands.seasons
    _autosummary/gamesheet_sdk.cli.commands.teams
    _autosummary/gamesheet_sdk.cli.commands.teams_roster
    _autosummary/gamesheet_sdk.cli.commands.teams_roster_coaches
    _autosummary/gamesheet_sdk.cli.commands.teams_roster_players
```
