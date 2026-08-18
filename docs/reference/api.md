# API Reference

<!--TOC-->

______________________________________________________________________

- [1. Module index](#1-module-index)
- [2. Common infrastructure](#2-common-infrastructure)
- [3. Authentication package](#3-authentication-package)
- [4. Shared utilities](#4-shared-utilities)
- [5. Common CLI infrastructure](#5-common-cli-infrastructure)
- [6. Admin domain modules](#6-admin-domain-modules)
- [7. Admin games package](#7-admin-games-package)
- [8. Admin roster package](#8-admin-roster-package)
- [9. Admin CLI](#9-admin-cli)
- [10. Teams domain and CLI](#10-teams-domain-and-cli)

______________________________________________________________________

<!--TOC-->

The {mod}`gamesheet_sdk` package exposes Pythonic wrappers around the GameSheet platform. Complete API documentation for all modules, packages, and subpackages
is generated automatically from source on every documentation build using `sphinx-apidoc`.

The package is organized into three pillars:

- **`common`** — Shared infrastructure (auth, config, session, browser, output, errors)
- **`admin`** — Admin dashboard domain modules and CLI
- **`teams`** — Teams dashboard domain modules and CLI

## 1. Module index

All Python modules are automatically discovered and documented. Click any module name to view its complete API documentation.

```{eval-rst}
.. autosummary::
    :toctree: _autosummary
    :recursive:

    gamesheet_sdk
    gamesheet_sdk.common
    gamesheet_sdk.common.auth
    gamesheet_sdk.common.browser
    gamesheet_sdk.common.cli
    gamesheet_sdk.common.config
    gamesheet_sdk.common.constants
    gamesheet_sdk.common.errors
    gamesheet_sdk.common.exceptions
    gamesheet_sdk.common.output
    gamesheet_sdk.common.security
    gamesheet_sdk.common.session
    gamesheet_sdk.common.shared
    gamesheet_sdk.admin
    gamesheet_sdk.admin.associations
    gamesheet_sdk.admin.divisions
    gamesheet_sdk.admin.games
    gamesheet_sdk.admin.ipad_keys
    gamesheet_sdk.admin.leagues
    gamesheet_sdk.admin.referees
    gamesheet_sdk.admin.roster
    gamesheet_sdk.admin.seasons
    gamesheet_sdk.admin.shared
    gamesheet_sdk.admin.teams
    gamesheet_sdk.admin.cli
    gamesheet_sdk.teams
    gamesheet_sdk.teams.login
    gamesheet_sdk.teams.lookups
    gamesheet_sdk.teams.seasons
    gamesheet_sdk.teams.session
    gamesheet_sdk.teams.shared
    gamesheet_sdk.teams.cli
```

## 2. Common infrastructure

Shared modules used by both admin and teams CLIs.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.common
    _autosummary/gamesheet_sdk.common.browser
    _autosummary/gamesheet_sdk.common.config
    _autosummary/gamesheet_sdk.common.constants
    _autosummary/gamesheet_sdk.common.errors
    _autosummary/gamesheet_sdk.common.exceptions
    _autosummary/gamesheet_sdk.common.output
    _autosummary/gamesheet_sdk.common.security
    _autosummary/gamesheet_sdk.common.session
```

## 3. Authentication package

Authentication flows, token management, and authenticated HTTP session.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.common.auth
    _autosummary/gamesheet_sdk.common.auth.constants
    _autosummary/gamesheet_sdk.common.auth.credentials
    _autosummary/gamesheet_sdk.common.auth.firebase
    _autosummary/gamesheet_sdk.common.auth.flow
    _autosummary/gamesheet_sdk.common.auth.login
    _autosummary/gamesheet_sdk.common.auth.session
    _autosummary/gamesheet_sdk.common.auth.storage
    _autosummary/gamesheet_sdk.common.auth.tokens
```

## 4. Shared utilities

Shared utilities and helpers used across the SDK.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.common.shared
    _autosummary/gamesheet_sdk.common.shared.constants
    _autosummary/gamesheet_sdk.common.shared.gamesheet_http
    _autosummary/gamesheet_sdk.common.shared.image_upload
    _autosummary/gamesheet_sdk.admin.shared
    _autosummary/gamesheet_sdk.admin.shared.jsonapi
```

## 5. Common CLI infrastructure

Shared CLI framework used by both admin and teams CLIs.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.common.cli
    _autosummary/gamesheet_sdk.common.cli.constants
    _autosummary/gamesheet_sdk.common.cli.core
    _autosummary/gamesheet_sdk.common.cli.decorators
    _autosummary/gamesheet_sdk.common.cli.helpers
    _autosummary/gamesheet_sdk.common.cli.rendering
    _autosummary/gamesheet_sdk.common.cli.rich_config
```

## 6. Admin domain modules

Domain modules for the admin dashboard.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.admin
    _autosummary/gamesheet_sdk.admin.associations
    _autosummary/gamesheet_sdk.admin.divisions
    _autosummary/gamesheet_sdk.admin.ipad_keys
    _autosummary/gamesheet_sdk.admin.leagues
    _autosummary/gamesheet_sdk.admin.referees
    _autosummary/gamesheet_sdk.admin.seasons
    _autosummary/gamesheet_sdk.admin.teams
```

## 7. Admin games package

Game retrieval and management for scheduled, completed, and bracket games.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.admin.games
    _autosummary/gamesheet_sdk.admin.games.brackets
    _autosummary/gamesheet_sdk.admin.games.broadcasters
    _autosummary/gamesheet_sdk.admin.games.completed
    _autosummary/gamesheet_sdk.admin.games.helpers
    _autosummary/gamesheet_sdk.admin.games.locations
    _autosummary/gamesheet_sdk.admin.games.models
    _autosummary/gamesheet_sdk.admin.games.scheduled
```

## 8. Admin roster package

Player and coach roster management.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.admin.roster
    _autosummary/gamesheet_sdk.admin.roster.coaches
    _autosummary/gamesheet_sdk.admin.roster.helpers
    _autosummary/gamesheet_sdk.admin.roster.models
    _autosummary/gamesheet_sdk.admin.roster.players
```

## 9. Admin CLI

Admin CLI framework and command implementations.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.admin.cli
    _autosummary/gamesheet_sdk.admin.cli.constants
    _autosummary/gamesheet_sdk.admin.cli.helpers
    _autosummary/gamesheet_sdk.admin.cli.main
    _autosummary/gamesheet_sdk.admin.cli.shared
    _autosummary/gamesheet_sdk.admin.cli.shared.datetime_helpers
    _autosummary/gamesheet_sdk.admin.cli.shared.decorators
    _autosummary/gamesheet_sdk.admin.cli.shared.rendering
    _autosummary/gamesheet_sdk.admin.cli.commands
    _autosummary/gamesheet_sdk.admin.cli.commands.associations
    _autosummary/gamesheet_sdk.admin.cli.commands.completion
    _autosummary/gamesheet_sdk.admin.cli.commands.divisions
    _autosummary/gamesheet_sdk.admin.cli.commands.games
    _autosummary/gamesheet_sdk.admin.cli.commands.games_brackets
    _autosummary/gamesheet_sdk.admin.cli.commands.games_completed
    _autosummary/gamesheet_sdk.admin.cli.commands.games_scheduled
    _autosummary/gamesheet_sdk.admin.cli.commands.ipad_keys
    _autosummary/gamesheet_sdk.admin.cli.commands.leagues
    _autosummary/gamesheet_sdk.admin.cli.commands.locations
    _autosummary/gamesheet_sdk.admin.cli.commands.login
    _autosummary/gamesheet_sdk.admin.cli.commands.referees
    _autosummary/gamesheet_sdk.admin.cli.commands.roster
    _autosummary/gamesheet_sdk.admin.cli.commands.roster_coaches
    _autosummary/gamesheet_sdk.admin.cli.commands.roster_players
    _autosummary/gamesheet_sdk.admin.cli.commands.seasons
    _autosummary/gamesheet_sdk.admin.cli.commands.teams
    _autosummary/gamesheet_sdk.admin.cli.commands.teams_roster
    _autosummary/gamesheet_sdk.admin.cli.commands.teams_roster_coaches
    _autosummary/gamesheet_sdk.admin.cli.commands.teams_roster_players
```

## 10. Teams domain and CLI

Teams domain models, auth, and CLI command implementations.

```{eval-rst}
.. toctree::
    :maxdepth: 2

    _autosummary/gamesheet_sdk.teams
    _autosummary/gamesheet_sdk.teams.login
    _autosummary/gamesheet_sdk.teams.lookups
    _autosummary/gamesheet_sdk.teams.seasons
    _autosummary/gamesheet_sdk.teams.session
    _autosummary/gamesheet_sdk.teams.shared
    _autosummary/gamesheet_sdk.teams.shared.constants
    _autosummary/gamesheet_sdk.teams.cli
    _autosummary/gamesheet_sdk.teams.cli.helpers
    _autosummary/gamesheet_sdk.teams.cli.main
    _autosummary/gamesheet_sdk.teams.cli.commands
    _autosummary/gamesheet_sdk.teams.cli.commands.completion
    _autosummary/gamesheet_sdk.teams.cli.commands.login
    _autosummary/gamesheet_sdk.teams.cli.commands.lookups
    _autosummary/gamesheet_sdk.teams.cli.commands.seasons
```
