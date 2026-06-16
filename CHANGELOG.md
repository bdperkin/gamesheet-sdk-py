# CHANGELOG

<!--next-version-placeholder-->

## v0.1.45 (2026-06-16)

### Bug Fixes

- Populate missing field values in get commands ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **divisions**: Populate team_count field in get_division ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **spider**: Add unused-ignore to type ignore for version compatibility ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **spider**: Queue all discovered links, not just the first one ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **spider**: Remove login requirement - use BrowserSession auto-load ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **spider**: Wait for networkidle instead of domcontentloaded ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **teams**: Correctly match invitation code via relationship ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **teams**: Populate invitation_code field in get_team ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **teams**: Use list endpoint to populate invitation_code in get_team ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

### Chores

- Remove accidentally committed __pycache__ files ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **deps**: Update pre-commit hooks ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **spider**: Clean up vulture warnings ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **spider**: Improve code quality and linter compliance ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

### Code Style

- Apply linter/formatter fixes from pre-commit hooks ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **divisions**: Reformat docstring line wrapping ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **tests**: Fix autopep8 indentation conflicts ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **tests**: Fix editorconfig indentation issues ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

### Documentation

- **tests**: Add docstrings to test package __init__ files ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

### Features

- **cli**: Add get sub-command for associations, leagues, divisions, teams, games, and roster ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **spider**: Add season web spider utility ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **spider**: Add season web spider utility with comprehensive tooling ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **spider**: Add URL pattern deduplication and network artifacts ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

### Testing

- **cli**: Achieve 100% test coverage for get commands ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

- **cli,units**: Add comprehensive test coverage for get commands ([#102](https://github.com/bdperkin/gamesheet-sdk-py/pull/102),
  [`d971336`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d971336726916a0834be3498adac0da963f1546b))

## v0.1.44 (2026-06-16)

### Bug Fixes

- Populate missing field values in get commands ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

- **divisions**: Populate team_count field in get_division ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

- **teams**: Correctly match invitation code via relationship ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

- **teams**: Populate invitation_code field in get_team ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

- **teams**: Use list endpoint to populate invitation_code in get_team ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

### Chores

- Remove accidentally committed __pycache__ files ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

### Code Style

- Apply linter/formatter fixes from pre-commit hooks ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

- **divisions**: Reformat docstring line wrapping ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

- **tests**: Fix autopep8 indentation conflicts ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

- **tests**: Fix editorconfig indentation issues ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

### Documentation

- **tests**: Add docstrings to test package __init__ files ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

### Features

- **cli**: Add get sub-command for associations, leagues, divisions, teams, games, and roster ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

### Testing

- **cli**: Achieve 100% test coverage for get commands ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

- **cli,units**: Add comprehensive test coverage for get commands ([#104](https://github.com/bdperkin/gamesheet-sdk-py/pull/104),
  [`dff9679`](https://github.com/bdperkin/gamesheet-sdk-py/commit/dff967953ab4db0f0679c7e9479af0a432b7a997))

## v0.1.43 (2026-06-16)

### Bug Fixes

- **spider**: Add unused-ignore to type ignore for version compatibility ([#103](https://github.com/bdperkin/gamesheet-sdk-py/pull/103),
  [`0959456`](https://github.com/bdperkin/gamesheet-sdk-py/commit/09594567bd9461c2dc0f6652f42137a233feef69))

- **spider**: Queue all discovered links, not just the first one ([#103](https://github.com/bdperkin/gamesheet-sdk-py/pull/103),
  [`0959456`](https://github.com/bdperkin/gamesheet-sdk-py/commit/09594567bd9461c2dc0f6652f42137a233feef69))

- **spider**: Remove login requirement - use BrowserSession auto-load ([#103](https://github.com/bdperkin/gamesheet-sdk-py/pull/103),
  [`0959456`](https://github.com/bdperkin/gamesheet-sdk-py/commit/09594567bd9461c2dc0f6652f42137a233feef69))

- **spider**: Wait for networkidle instead of domcontentloaded ([#103](https://github.com/bdperkin/gamesheet-sdk-py/pull/103),
  [`0959456`](https://github.com/bdperkin/gamesheet-sdk-py/commit/09594567bd9461c2dc0f6652f42137a233feef69))

### Chores

- **spider**: Clean up vulture warnings ([#103](https://github.com/bdperkin/gamesheet-sdk-py/pull/103),
  [`0959456`](https://github.com/bdperkin/gamesheet-sdk-py/commit/09594567bd9461c2dc0f6652f42137a233feef69))

- **spider**: Improve code quality and linter compliance ([#103](https://github.com/bdperkin/gamesheet-sdk-py/pull/103),
  [`0959456`](https://github.com/bdperkin/gamesheet-sdk-py/commit/09594567bd9461c2dc0f6652f42137a233feef69))

### Features

- **spider**: Add season web spider utility ([#103](https://github.com/bdperkin/gamesheet-sdk-py/pull/103),
  [`0959456`](https://github.com/bdperkin/gamesheet-sdk-py/commit/09594567bd9461c2dc0f6652f42137a233feef69))

- **spider**: Add season web spider utility with comprehensive tooling ([#103](https://github.com/bdperkin/gamesheet-sdk-py/pull/103),
  [`0959456`](https://github.com/bdperkin/gamesheet-sdk-py/commit/09594567bd9461c2dc0f6652f42137a233feef69))

- **spider**: Add URL pattern deduplication and network artifacts ([#103](https://github.com/bdperkin/gamesheet-sdk-py/pull/103),
  [`0959456`](https://github.com/bdperkin/gamesheet-sdk-py/commit/09594567bd9461c2dc0f6652f42137a233feef69))

## v0.1.42 (2026-06-15)

### Features

- **referees**: Implement full CRUD operations with comprehensive test suite ([#101](https://github.com/bdperkin/gamesheet-sdk-py/pull/101),
  [`cc95486`](https://github.com/bdperkin/gamesheet-sdk-py/commit/cc954861189520b7441caf4fe257069f916d9d2f))

## v0.1.41 (2026-06-15)

### Bug Fixes

- **cli**: Remove redundant default=None in click options ([#100](https://github.com/bdperkin/gamesheet-sdk-py/pull/100),
  [`4450638`](https://github.com/bdperkin/gamesheet-sdk-py/commit/4450638fb7c6efa7bed8e8b5b706c292c8a4e2b8))

- **cli**: Remove redundant readable=True from Path options ([#100](https://github.com/bdperkin/gamesheet-sdk-py/pull/100),
  [`4450638`](https://github.com/bdperkin/gamesheet-sdk-py/commit/4450638fb7c6efa7bed8e8b5b706c292c8a4e2b8))

- **teams**: Correct API field names and compute roster counts ([#100](https://github.com/bdperkin/gamesheet-sdk-py/pull/100),
  [`4450638`](https://github.com/bdperkin/gamesheet-sdk-py/commit/4450638fb7c6efa7bed8e8b5b706c292c8a4e2b8))

### Features

- **teams**: Add create, update, delete commands with comprehensive tests ([#100](https://github.com/bdperkin/gamesheet-sdk-py/pull/100),
  [`4450638`](https://github.com/bdperkin/gamesheet-sdk-py/commit/4450638fb7c6efa7bed8e8b5b706c292c8a4e2b8))

- **teams**: Extract invitation codes from JSON:API included data ([#100](https://github.com/bdperkin/gamesheet-sdk-py/pull/100),
  [`4450638`](https://github.com/bdperkin/gamesheet-sdk-py/commit/4450638fb7c6efa7bed8e8b5b706c292c8a4e2b8))

- **teams**: Request additional fields in teams list API call ([#100](https://github.com/bdperkin/gamesheet-sdk-py/pull/100),
  [`4450638`](https://github.com/bdperkin/gamesheet-sdk-py/commit/4450638fb7c6efa7bed8e8b5b706c292c8a4e2b8))

### Testing

- **teams**: Add coverage for invitation code edge cases ([#100](https://github.com/bdperkin/gamesheet-sdk-py/pull/100),
  [`4450638`](https://github.com/bdperkin/gamesheet-sdk-py/commit/4450638fb7c6efa7bed8e8b5b706c292c8a4e2b8))

## v0.1.40 (2026-06-13)

### Bug Fixes

- **ci**: Format CodeQL permission comments for zizmor compliance ([#99](https://github.com/bdperkin/gamesheet-sdk-py/pull/99),
  [`1ed8a28`](https://github.com/bdperkin/gamesheet-sdk-py/commit/1ed8a283ae5a90ea134e613272666a12270bf1e0))

## v0.1.39 (2026-06-13)

### Bug Fixes

- **ci**: Harden workflow security per zizmor recommendations ([#98](https://github.com/bdperkin/gamesheet-sdk-py/pull/98),
  [`a419a6c`](https://github.com/bdperkin/gamesheet-sdk-py/commit/a419a6c8e43954a1b2b88177424927d7b054aaed))

## v0.1.38 (2026-06-13)

### Bug Fixes

- **security**: Suppress false positive credential logging alerts ([#97](https://github.com/bdperkin/gamesheet-sdk-py/pull/97),
  [`489e740`](https://github.com/bdperkin/gamesheet-sdk-py/commit/489e7401396eb64cdc75d57476e6f0bbb5ab840c))

## v0.1.37 (2026-06-13)

### Bug Fixes

- **build**: Remove hatchling version pin, PyPI now supports metadata 2.4 ([#96](https://github.com/bdperkin/gamesheet-sdk-py/pull/96),
  [`d1fe9fd`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d1fe9fd449d51d7d122c2241a5675f337fc02177))

### Build System

- **deps**: Bump actions/github-script ([#94](https://github.com/bdperkin/gamesheet-sdk-py/pull/94),
  [`61a0702`](https://github.com/bdperkin/gamesheet-sdk-py/commit/61a070279abdfc94574601084a4367853393307a))

## v0.1.36 (2026-06-13)

### Bug Fixes

- **ci**: Exclude Dependabot PRs from GitGuardian scan ([#95](https://github.com/bdperkin/gamesheet-sdk-py/pull/95),
  [`fe066ed`](https://github.com/bdperkin/gamesheet-sdk-py/commit/fe066ed32b616fb819fcf0ed5750467e8bfb75f5))

## v0.1.35 (2026-06-12)

### Bug Fixes

- **ci**: Resolve workflow failures in GitGuardian and Dependabot ([#93](https://github.com/bdperkin/gamesheet-sdk-py/pull/93),
  [`ef5edec`](https://github.com/bdperkin/gamesheet-sdk-py/commit/ef5edec63d00c819b9b626b65e5f9d59c6b2c212))

### Build System

- **deps**: Bump the actions group with 11 updates ([#92](https://github.com/bdperkin/gamesheet-sdk-py/pull/92),
  [`3c28bf4`](https://github.com/bdperkin/gamesheet-sdk-py/commit/3c28bf4c3162cb30ca690d477b855f377146dbca))

## v0.1.34 (2026-06-10)

### Bug Fixes

- **ci**: Correct all Docker-related action SHAs ([#90](https://github.com/bdperkin/gamesheet-sdk-py/pull/90),
  [`988a144`](https://github.com/bdperkin/gamesheet-sdk-py/commit/988a144a36ee195831aca15c93fec85239966aaa))

## v0.1.33 (2026-06-10)

### Bug Fixes

- **build**: Pin hatchling \<1.26 for PyPI compatibility ([#89](https://github.com/bdperkin/gamesheet-sdk-py/pull/89),
  [`08bd2fa`](https://github.com/bdperkin/gamesheet-sdk-py/commit/08bd2fa64a580e7bb288af6987f48645483784af))

## v0.1.32 (2026-06-10)

### Bug Fixes

- **ci**: Disable PyPI metadata verification for Metadata-Version 2.4 ([#88](https://github.com/bdperkin/gamesheet-sdk-py/pull/88),
  [`3a7dbff`](https://github.com/bdperkin/gamesheet-sdk-py/commit/3a7dbffddcb3c5a984a78bf0ec19a903a56a4cae))

## v0.1.31 (2026-06-10)

### Bug Fixes

- **ci**: Correct deploy-pages SHA to valid v5.0.0 ([#87](https://github.com/bdperkin/gamesheet-sdk-py/pull/87),
  [`482c7ec`](https://github.com/bdperkin/gamesheet-sdk-py/commit/482c7ec6f9fa68389780804836e7aa15ba488b89))

## v0.1.30 (2026-06-10)

### Bug Fixes

- **ci**: Correct download-artifact SHA to valid v4.2.0 ([#86](https://github.com/bdperkin/gamesheet-sdk-py/pull/86),
  [`74da108`](https://github.com/bdperkin/gamesheet-sdk-py/commit/74da108e0e730191ead11cecd48356b26efb7b1f))

## v0.1.29 (2026-06-10)

### Bug Fixes

- **ci**: Correct dependency-review-action SHA to valid v5.0.0 ([#84](https://github.com/bdperkin/gamesheet-sdk-py/pull/84),
  [`18a74f0`](https://github.com/bdperkin/gamesheet-sdk-py/commit/18a74f0c0d1f4182e4a39e10a18ae5c3c9f66bc6))

- **ci**: Correct upload-pages-artifact SHA to valid v5.0.0 ([#85](https://github.com/bdperkin/gamesheet-sdk-py/pull/85),
  [`d82de10`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d82de1033a3b0c4d093b7ec71910af06f082d5f6))

## v0.1.28 (2026-06-10)

### Bug Fixes

- **ci**: Correct upload-artifact SHA to valid v4.6.1 commit ([#83](https://github.com/bdperkin/gamesheet-sdk-py/pull/83),
  [`821a64f`](https://github.com/bdperkin/gamesheet-sdk-py/commit/821a64fd1811b53a0acb7ab5ab44b6869ee1a4b8))

## v0.1.27 (2026-06-10)

### Bug Fixes

- **ci**: Replace OSV scanner with pip-audit for Python dependencies ([#82](https://github.com/bdperkin/gamesheet-sdk-py/pull/82),
  [`43af5f9`](https://github.com/bdperkin/gamesheet-sdk-py/commit/43af5f9e48bda054f49b8056b68cc3d36e096edb))

## v0.1.26 (2026-06-10)

### Bug Fixes

- **ci**: Generate lockfile for OSV scanner instead of using pyproject.toml ([#79](https://github.com/bdperkin/gamesheet-sdk-py/pull/79),
  [`f1b8705`](https://github.com/bdperkin/gamesheet-sdk-py/commit/f1b87058b248182d23f14a265e61ad4c6cc13858))

- **ci**: Make OSV scanner fail on errors and use pip freeze ([#81](https://github.com/bdperkin/gamesheet-sdk-py/pull/81),
  [`4ab3808`](https://github.com/bdperkin/gamesheet-sdk-py/commit/4ab3808faf9d8422b867f274b5364ca62bd665f0))

- **ci**: Make zizmor workflow fail on HIGH severity issues only ([#80](https://github.com/bdperkin/gamesheet-sdk-py/pull/80),
  [`831740b`](https://github.com/bdperkin/gamesheet-sdk-py/commit/831740b699f40b0443a93b355512518bec328345))

## v0.1.25 (2026-06-10)

### Bug Fixes

- **ci**: Handle OSV scanner when no lockfiles exist ([#77](https://github.com/bdperkin/gamesheet-sdk-py/pull/77),
  [`c5f8db7`](https://github.com/bdperkin/gamesheet-sdk-py/commit/c5f8db70b02e4c8c5cbb754a5e8d1a5f55ede6df))

- **ci**: Move workflow-level write permissions to job-level ([#78](https://github.com/bdperkin/gamesheet-sdk-py/pull/78),
  [`521f6dc`](https://github.com/bdperkin/gamesheet-sdk-py/commit/521f6dcf3da8c04ce628fd8f2c2e68b5fed70788))

## v0.1.24 (2026-06-10)

### Bug Fixes

- **ci**: Sanitize template variables to prevent injection ([#76](https://github.com/bdperkin/gamesheet-sdk-py/pull/76),
  [`07c6192`](https://github.com/bdperkin/gamesheet-sdk-py/commit/07c6192b6b203305374bb8494f710b79f130f869))

## v0.1.23 (2026-06-10)

### Bug Fixes

- **ci**: Correct OSV scanner command and ensure SARIF output ([#75](https://github.com/bdperkin/gamesheet-sdk-py/pull/75),
  [`12440da`](https://github.com/bdperkin/gamesheet-sdk-py/commit/12440da168edb6a44eb91fde35fb060af07e1ec4))

## v0.1.22 (2026-06-10)

### Bug Fixes

- **ci**: Pin all GitHub Actions and fix 202 zizmor findings ([#74](https://github.com/bdperkin/gamesheet-sdk-py/pull/74),
  [`1430bbf`](https://github.com/bdperkin/gamesheet-sdk-py/commit/1430bbfc58a1982fbc0d7a3a0ae15ae5350b7cd8))

## v0.1.21 (2026-06-10)

### Bug Fixes

- **ci**: Show zizmor exit code while still reporting findings ([#73](https://github.com/bdperkin/gamesheet-sdk-py/pull/73),
  [`19badb9`](https://github.com/bdperkin/gamesheet-sdk-py/commit/19badb914e8da23335d886d7b18e68a7628191fe))

## v0.1.20 (2026-06-10)

### Bug Fixes

- **ci**: Add security-events permission to workflow linter ([#71](https://github.com/bdperkin/gamesheet-sdk-py/pull/71),
  [`2eba146`](https://github.com/bdperkin/gamesheet-sdk-py/commit/2eba14686f77d842cce84701cd18fb0b66b7356e))

- **ci**: Replace broken OSV action with direct CLI usage ([#72](https://github.com/bdperkin/gamesheet-sdk-py/pull/72),
  [`3d0f6d1`](https://github.com/bdperkin/gamesheet-sdk-py/commit/3d0f6d13a4f97a9f893aaf4d925b51f7222df7d6))

## v0.1.19 (2026-06-10)

### Bug Fixes

- **ci**: Pin Trivy workflow actions and add explicit token ([#70](https://github.com/bdperkin/gamesheet-sdk-py/pull/70),
  [`82eec43`](https://github.com/bdperkin/gamesheet-sdk-py/commit/82eec43241c46ab84e8b06943acfd5c42f4869e0))

## v0.1.18 (2026-06-10)

### Bug Fixes

- **ci**: Correct OSV scanner action path and update to v2.2.4 ([#69](https://github.com/bdperkin/gamesheet-sdk-py/pull/69),
  [`c418899`](https://github.com/bdperkin/gamesheet-sdk-py/commit/c41889967e0fd6790f063fdf4cd4ba7a4e87ceb2))

- **ci**: Update GitGuardian action to valid commit SHA ([#68](https://github.com/bdperkin/gamesheet-sdk-py/pull/68),
  [`94e755d`](https://github.com/bdperkin/gamesheet-sdk-py/commit/94e755d57670fec84c4a1f061136a788fae044ac))

### Documentation

- **security**: Convert bare URLs to proper markdown links ([#66](https://github.com/bdperkin/gamesheet-sdk-py/pull/66),
  [`56b29f2`](https://github.com/bdperkin/gamesheet-sdk-py/commit/56b29f26d87cfdab19d245b41887e494442eaba7))

- **security**: Improve list formatting in API keys setup guides ([#67](https://github.com/bdperkin/gamesheet-sdk-py/pull/67),
  [`54f8381`](https://github.com/bdperkin/gamesheet-sdk-py/commit/54f8381cfd89d4e864e1616ad8cb67ea5db14e8b))

## v0.1.17 (2026-06-10)

### Build System

- **deps**: Bump the actions group with 4 updates ([#62](https://github.com/bdperkin/gamesheet-sdk-py/pull/62),
  [`c1d2e01`](https://github.com/bdperkin/gamesheet-sdk-py/commit/c1d2e0163007617ad06387cfb0868f196b4b40e1))

### Documentation

- **security**: Fix linkcheck error for X.org/X11 package name ([#64](https://github.com/bdperkin/gamesheet-sdk-py/pull/64),
  [`98dcbdc`](https://github.com/bdperkin/gamesheet-sdk-py/commit/98dcbdc2fc0d362b848407d9f62fef5ec3e8061f))

- **security**: Implement Priority 4 vulnerability evaluation and acceptance ([#63](https://github.com/bdperkin/gamesheet-sdk-py/pull/63),
  [`ffac284`](https://github.com/bdperkin/gamesheet-sdk-py/commit/ffac284c037a467981f298e6fbf8fafabdb1bc9e))

### Features

- **security**: Implement comprehensive security scanning pipeline ([#65](https://github.com/bdperkin/gamesheet-sdk-py/pull/65),
  [`a677cf4`](https://github.com/bdperkin/gamesheet-sdk-py/commit/a677cf47f763f3a8ff2829275db056e72f98537d))

## v0.1.16 (2026-06-10)

### Bug Fixes

- **security**: Make pip-audit non-blocking for known vulnerabilities ([#61](https://github.com/bdperkin/gamesheet-sdk-py/pull/61),
  [`db7befe`](https://github.com/bdperkin/gamesheet-sdk-py/commit/db7befe331690d21b85d9c532c1b0d6313d7f2e3))

### Features

- **security**: Implement Priority 3 CI security scanning ([#61](https://github.com/bdperkin/gamesheet-sdk-py/pull/61),
  [`db7befe`](https://github.com/bdperkin/gamesheet-sdk-py/commit/db7befe331690d21b85d9c532c1b0d6313d7f2e3))

## v0.1.15 (2026-06-10)

### Bug Fixes

- **security**: Upgrade pip/setuptools/wheel to address CVEs ([#60](https://github.com/bdperkin/gamesheet-sdk-py/pull/60),
  [`abf7423`](https://github.com/bdperkin/gamesheet-sdk-py/commit/abf7423206bd50aaf25aed6c7901d3d80d5a0c1a))

## v0.1.14 (2026-06-10)

### Bug Fixes

- **cli**: Correct divisions teams endpoint to /api/divisions/{id}/teams ([#59](https://github.com/bdperkin/gamesheet-sdk-py/pull/59),
  [`085e3fa`](https://github.com/bdperkin/gamesheet-sdk-py/commit/085e3fa98eb66ce2c41b2781e0a9bac17e98f427))

### Features

- **cli**: Add divisions create command ([#59](https://github.com/bdperkin/gamesheet-sdk-py/pull/59),
  [`085e3fa`](https://github.com/bdperkin/gamesheet-sdk-py/commit/085e3fa98eb66ce2c41b2781e0a9bac17e98f427))

- **cli**: Add divisions update command ([#59](https://github.com/bdperkin/gamesheet-sdk-py/pull/59),
  [`085e3fa`](https://github.com/bdperkin/gamesheet-sdk-py/commit/085e3fa98eb66ce2c41b2781e0a9bac17e98f427))

- **cli**: Add team count to divisions list output ([#59](https://github.com/bdperkin/gamesheet-sdk-py/pull/59),
  [`085e3fa`](https://github.com/bdperkin/gamesheet-sdk-py/commit/085e3fa98eb66ce2c41b2781e0a9bac17e98f427))

- **cli**: Add teams sub-sub-command to divisions command ([#59](https://github.com/bdperkin/gamesheet-sdk-py/pull/59),
  [`085e3fa`](https://github.com/bdperkin/gamesheet-sdk-py/commit/085e3fa98eb66ce2c41b2781e0a9bac17e98f427))

- **divisions**: Implement complete CRUD operations with CLI commands ([#59](https://github.com/bdperkin/gamesheet-sdk-py/pull/59),
  [`085e3fa`](https://github.com/bdperkin/gamesheet-sdk-py/commit/085e3fa98eb66ce2c41b2781e0a9bac17e98f427))

## v0.1.13 (2026-06-09)

### Bug Fixes

- **ci**: Add version job to needs chain for container build ([#58](https://github.com/bdperkin/gamesheet-sdk-py/pull/58),
  [`b0ddc7c`](https://github.com/bdperkin/gamesheet-sdk-py/commit/b0ddc7c0005302a13bdfa898ef2aa29afdef43c2))

## v0.1.12 (2026-06-09)

### Bug Fixes

- **ci**: Restore dependency-review to pull_request-only trigger ([#57](https://github.com/bdperkin/gamesheet-sdk-py/pull/57),
  [`d72c2f6`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d72c2f6861563e91c33962e7ca00e1eb4fd263df))

### Continuous Integration

- Use path filters instead of commit message checks to skip release workflows ([#56](https://github.com/bdperkin/gamesheet-sdk-py/pull/56),
  [`c2e7076`](https://github.com/bdperkin/gamesheet-sdk-py/commit/c2e707609f20bd2e6eca77bb26597077459df81a))

### Refactoring

- **cli**: Merge season command into seasons group ([#56](https://github.com/bdperkin/gamesheet-sdk-py/pull/56),
  [`c2e7076`](https://github.com/bdperkin/gamesheet-sdk-py/commit/c2e707609f20bd2e6eca77bb26597077459df81a))

- **tests**: Split seasons tests into separate list and get files ([#56](https://github.com/bdperkin/gamesheet-sdk-py/pull/56),
  [`c2e7076`](https://github.com/bdperkin/gamesheet-sdk-py/commit/c2e707609f20bd2e6eca77bb26597077459df81a))

## v0.1.11 (2026-06-09)

### Bug Fixes

- **ci**: Add security-events permission and update CodeQL action ([#55](https://github.com/bdperkin/gamesheet-sdk-py/pull/55),
  [`1dac7af`](https://github.com/bdperkin/gamesheet-sdk-py/commit/1dac7af235fc43db91d78855d18255dac50f5595))

## v0.1.10 (2026-06-09)

### Bug Fixes

- **ci**: Correct GitHub Actions version tags in container workflow ([#54](https://github.com/bdperkin/gamesheet-sdk-py/pull/54),
  [`2bb6728`](https://github.com/bdperkin/gamesheet-sdk-py/commit/2bb672844f0f515b32a18185fad862d31e2c3b28))

## v0.1.9 (2026-06-09)

### Bug Fixes

- **ci**: Update trivy-action to 0.29.0 to address security advisory ([#53](https://github.com/bdperkin/gamesheet-sdk-py/pull/53),
  [`976834b`](https://github.com/bdperkin/gamesheet-sdk-py/commit/976834b7dbe015b489544519ce9c9acae0c118eb))

- **ci**: Update trivy-action to latest version 0.36.0 ([#53](https://github.com/bdperkin/gamesheet-sdk-py/pull/53),
  [`976834b`](https://github.com/bdperkin/gamesheet-sdk-py/commit/976834b7dbe015b489544519ce9c9acae0c118eb))

### Features

- **ci**: Add Docker container build and publish workflow ([#53](https://github.com/bdperkin/gamesheet-sdk-py/pull/53),
  [`976834b`](https://github.com/bdperkin/gamesheet-sdk-py/commit/976834b7dbe015b489544519ce9c9acae0c118eb))

## v0.1.8 (2026-06-09)

### Bug Fixes

- **ci**: Add missing dependencies to release workflow
  ([`9ca44f3`](https://github.com/bdperkin/gamesheet-sdk-py/commit/9ca44f3a3c87f84b2dccb3c066a1a6653b3ae3e1))

- **ci**: Improve release workflow Python setup and ignore Claude Code data ([#52](https://github.com/bdperkin/gamesheet-sdk-py/pull/52),
  [`fd3b8d1`](https://github.com/bdperkin/gamesheet-sdk-py/commit/fd3b8d1a6be09963096632468695c90e14de14ce))

- **pre-commit**: Add args to pretty-format-json for prettier compatibility ([#51](https://github.com/bdperkin/gamesheet-sdk-py/pull/51),
  [`9026992`](https://github.com/bdperkin/gamesheet-sdk-py/commit/902699258a111cf42f0f2700ffefe69299b8c695))

### Build System

- **deps**: Bump codecov/codecov-action in the actions group ([#48](https://github.com/bdperkin/gamesheet-sdk-py/pull/48),
  [`62fa5bc`](https://github.com/bdperkin/gamesheet-sdk-py/commit/62fa5bc9504ed7b8450beacd01063023c4757ee9))

### Chores

- Apply pre-commit formatting to PSR-generated CHANGELOG ([#49](https://github.com/bdperkin/gamesheet-sdk-py/pull/49),
  [`d2ee2d4`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d2ee2d493346e3c3ef118c4ffda9edee23311aed))

### Features

- **cli**: Add games and roster commands with nested sub-groups ([#50](https://github.com/bdperkin/gamesheet-sdk-py/pull/50),
  [`3e6d355`](https://github.com/bdperkin/gamesheet-sdk-py/commit/3e6d355c1fca3347d28125c9873c4d51ac660c8d))

- **cli**: Add games and roster commands with nested sub-groups
  ([`1698485`](https://github.com/bdperkin/gamesheet-sdk-py/commit/1698485832332cd6888fcf5afa0b0d5ed037b2bf))

## v0.1.7 (2026-06-08)

### Bug Fixes

- **ci**: Add changelog insertion_flag for PSR update mode ([#47](https://github.com/bdperkin/gamesheet-sdk-py/pull/47),
  [`d79de88`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d79de886ae9ab20f5464e260f6752af420e2290b))

- **ci**: Complete CI optimization - eliminate all duplicate workflow runs ([#47](https://github.com/bdperkin/gamesheet-sdk-py/pull/47),
  [`d79de88`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d79de886ae9ab20f5464e260f6752af420e2290b))

- **ci**: Fix CHANGELOG generation and GitHub Release creation ([#47](https://github.com/bdperkin/gamesheet-sdk-py/pull/47),
  [`d79de88`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d79de886ae9ab20f5464e260f6752af420e2290b))

- **ci**: Scope workflow triggers to eliminate duplicate runs ([#47](https://github.com/bdperkin/gamesheet-sdk-py/pull/47),
  [`d79de88`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d79de886ae9ab20f5464e260f6752af420e2290b))

- **ci**: Skip all workflows on release commits to prevent duplicate runs ([#47](https://github.com/bdperkin/gamesheet-sdk-py/pull/47),
  [`d79de88`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d79de886ae9ab20f5464e260f6752af420e2290b))

### Documentation

- **changelog**: Add missing v0.1.5 entry ([#47](https://github.com/bdperkin/gamesheet-sdk-py/pull/47),
  [`d79de88`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d79de886ae9ab20f5464e260f6752af420e2290b))

- **changelog**: Add missing v0.1.6 entry ([#47](https://github.com/bdperkin/gamesheet-sdk-py/pull/47),
  [`d79de88`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d79de886ae9ab20f5464e260f6752af420e2290b))

## v0.1.6 (2026-06-08)

### Bug Fixes

- **ci**: Fix CHANGELOG generation and GitHub Release creation ([#46](https://github.com/bdperkin/gamesheet-sdk-py/pull/46),
  [`5a74da2`](https://github.com/bdperkin/gamesheet-sdk-py/commit/5a74da2821d456929eb710eed0a2d58e2a4170c8))

### Documentation

- **changelog**: Add missing v0.1.5 entry ([#46](https://github.com/bdperkin/gamesheet-sdk-py/pull/46),
  [`5a74da2`](https://github.com/bdperkin/gamesheet-sdk-py/commit/5a74da2821d456929eb710eed0a2d58e2a4170c8))

## v0.1.5 (2026-06-08)

### Documentation

- Fix broken link in configure-release-token.md ([#45](https://github.com/bdperkin/gamesheet-sdk-py/pull/45),
  [`61e1b66`](https://github.com/bdperkin/gamesheet-sdk-py/commit/61e1b66e2690b125cf7609e5265a8c421273a8a8))

- **changelog**: Regenerate CHANGELOG with missing v0.1.1-v0.1.4 entries ([#44](https://github.com/bdperkin/gamesheet-sdk-py/pull/44),
  [`8527c4f`](https://github.com/bdperkin/gamesheet-sdk-py/commit/8527c4fdd28ba5b579fee64f20cf50f058b7fa35))

### Features

- **ci**: Add PAT support for releases with branch protection ([#45](https://github.com/bdperkin/gamesheet-sdk-py/pull/45),
  [`61e1b66`](https://github.com/bdperkin/gamesheet-sdk-py/commit/61e1b66e2690b125cf7609e5265a8c421273a8a8))

## v0.1.4 (2026-06-08)

### Bug Fixes

- **ci**: Explicitly enable changelog generation in PSR version command ([#43](https://github.com/bdperkin/gamesheet-sdk-py/pull/43),
  [`fa43910`](https://github.com/bdperkin/gamesheet-sdk-py/commit/fa439104c19f6810c3552fe31d2739b9125fd7d1))

## v0.1.3 (2026-06-08)

### Bug Fixes

- **build**: Remove non-existent changelog template_dir from PSR config ([#42](https://github.com/bdperkin/gamesheet-sdk-py/pull/42),
  [`aa02b76`](https://github.com/bdperkin/gamesheet-sdk-py/commit/aa02b7627e9a520c45e91f528834e4e5b0e5529c))

## v0.1.2 (2026-06-08)

### Bug Fixes

- **build**: Switch from hatch-vcs to PSR-managed static versioning ([#39](https://github.com/bdperkin/gamesheet-sdk-py/pull/39),
  [`90dc6b7`](https://github.com/bdperkin/gamesheet-sdk-py/commit/90dc6b7c97fd7fd9161077c4e0a62e3042e589b6))

- **ci**: Rename workflow back to release.yml for PyPI Trusted Publishing ([#39](https://github.com/bdperkin/gamesheet-sdk-py/pull/39),
  [`90dc6b7`](https://github.com/bdperkin/gamesheet-sdk-py/commit/90dc6b7c97fd7fd9161077c4e0a62e3042e589b6))

### Chores

- Test PSR release automation ([#40](https://github.com/bdperkin/gamesheet-sdk-py/pull/40),
  [`e0120ce`](https://github.com/bdperkin/gamesheet-sdk-py/commit/e0120ceabf46dff21359014023fd0421c08e4893))

### Documentation

- Update workflow filename reference in release-process.md ([#39](https://github.com/bdperkin/gamesheet-sdk-py/pull/39),
  [`90dc6b7`](https://github.com/bdperkin/gamesheet-sdk-py/commit/90dc6b7c97fd7fd9161077c4e0a62e3042e589b6))

## v0.1.1 (2026-06-08)

### Bug Fixes

- **config**: Configure PSR for patch-only bumps until 1.0.0 ([#38](https://github.com/bdperkin/gamesheet-sdk-py/pull/38),
  [`ff42a45`](https://github.com/bdperkin/gamesheet-sdk-py/commit/ff42a45f6ebe6f501c87c3d5b7ce9f729c04f7bf))

## v0.1.0 (2026-06-08)

### Code Style

- Apply automatic formatting from linters ([`3170674`](https://github.com/bdperkin/gamesheet-sdk-py/commit/3170674d0df313a65de1572a9536212928362f28))

### Features

- Implement full PSR automation for releases ([`3170674`](https://github.com/bdperkin/gamesheet-sdk-py/commit/3170674d0df313a65de1572a9536212928362f28))

## v0.0.8 (2026-06-08)

### Bug Fixes

- Actually run python-semantic-release to generate CHANGELOG
  ([`67273b4`](https://github.com/bdperkin/gamesheet-sdk-py/commit/67273b4de1fd0c23a9a29930baf7d87a8c3bc264))

- Checkout main branch for PSR changelog generation ([`8fcebee`](https://github.com/bdperkin/gamesheet-sdk-py/commit/8fcebeeb59724f1e216f0144f8172be34bb272d0))

### Documentation

- Update CHANGELOG.md with v0.0.7 release notes ([`67273b4`](https://github.com/bdperkin/gamesheet-sdk-py/commit/67273b4de1fd0c23a9a29930baf7d87a8c3bc264))

## v0.0.7 (2026-06-08)

### Bug Fixes

- Add pragma no cover for defensive shell_complete fallback ([#32](https://github.com/bdperkin/gamesheet-sdk-py/pull/32),
  [`06a3a88`](https://github.com/bdperkin/gamesheet-sdk-py/commit/06a3a885bead88a8b8a95ffe76dd59ed857e0851))

- Add unused-ignore to type ignore for RichGroup ([#31](https://github.com/bdperkin/gamesheet-sdk-py/pull/31),
  [`ab534fd`](https://github.com/bdperkin/gamesheet-sdk-py/commit/ab534fdcc995aee2300574741de5c98b2d06d33b))

- Clean up CLI help text by removing Sphinx directives ([#30](https://github.com/bdperkin/gamesheet-sdk-py/pull/30),
  [`d2ac1de`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d2ac1ded5ed1b99c5d3b18d35df08d571b52bc1a))

### Chores

- Update pre-commit tool versions and improve Makefile clean targets ([#29](https://github.com/bdperkin/gamesheet-sdk-py/pull/29),
  [`7d2603d`](https://github.com/bdperkin/gamesheet-sdk-py/commit/7d2603dc1c662143b87a57dfc80400349195e08a))

### Code Style

- Apply automatic formatting from pre-commit hooks ([`ff29634`](https://github.com/bdperkin/gamesheet-sdk-py/commit/ff29634ca6fb05ef45dd5b2ad075ecd5f4cf0ddb))

### Features

- Add automated changelog and release process with python-semantic-release
  ([`ff29634`](https://github.com/bdperkin/gamesheet-sdk-py/commit/ff29634ca6fb05ef45dd5b2ad075ecd5f4cf0ddb))

- Add rich-click for enhanced CLI help rendering ([#31](https://github.com/bdperkin/gamesheet-sdk-py/pull/31),
  [`ab534fd`](https://github.com/bdperkin/gamesheet-sdk-py/commit/ab534fdcc995aee2300574741de5c98b2d06d33b))

### Refactoring

- Improve type hints with TYPE_CHECKING imports ([#32](https://github.com/bdperkin/gamesheet-sdk-py/pull/32),
  [`06a3a88`](https://github.com/bdperkin/gamesheet-sdk-py/commit/06a3a885bead88a8b8a95ffe76dd59ed857e0851))

- Modernize pydantic-settings Config syntax ([#33](https://github.com/bdperkin/gamesheet-sdk-py/pull/33),
  [`6ec7a70`](https://github.com/bdperkin/gamesheet-sdk-py/commit/6ec7a70dd7fd694681a51adc0a3983e9a4ec23ef))

- Streamline README and improve PSR configuration ([`ff29634`](https://github.com/bdperkin/gamesheet-sdk-py/commit/ff29634ca6fb05ef45dd5b2ad075ecd5f4cf0ddb))

## v0.0.6 (2026-06-05)

### Features

- Add divisions, teams, and referees sub-commands ([`7348826`](https://github.com/bdperkin/gamesheet-sdk-py/commit/73488264615a44337676dbed8a80177c11f66eda))

- Add ipad-keys sub-command for retrieving Scoring Access Keys ([#25](https://github.com/bdperkin/gamesheet-sdk-py/pull/25),
  [`b4b7d36`](https://github.com/bdperkin/gamesheet-sdk-py/commit/b4b7d36c75e88694baf9199276a81d7111dd14c7))

- Add season get sub-command for detailed season information ([#24](https://github.com/bdperkin/gamesheet-sdk-py/pull/24),
  [`52c8395`](https://github.com/bdperkin/gamesheet-sdk-py/commit/52c8395d1d28c7ce14cb5a79546be7cb77fc57dd))

### Refactoring

- Convert ID args to options with env fallback and improve documentation ([#27](https://github.com/bdperkin/gamesheet-sdk-py/pull/27),
  [`2f96ee6`](https://github.com/bdperkin/gamesheet-sdk-py/commit/2f96ee6fed38f7e278c4016bb7790c95c273612e))

- Modularize codebase into focused packages ([#26](https://github.com/bdperkin/gamesheet-sdk-py/pull/26),
  [`ddc20a1`](https://github.com/bdperkin/gamesheet-sdk-py/commit/ddc20a1b25ec6da8454112bff85cb4c543e6419e))

## v0.0.5 (2026-06-03)

### Features

- Add seasons sub-command for listing seasons by league ([#23](https://github.com/bdperkin/gamesheet-sdk-py/pull/23),
  [`d77eb51`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d77eb51c4265517b8723f5df477aac644980530f))

## v0.0.4 (2026-06-03)

### Bug Fixes

- **codecov**: One flag per upload + changes status informational ([#20](https://github.com/bdperkin/gamesheet-sdk-py/pull/20),
  [`56fc300`](https://github.com/bdperkin/gamesheet-sdk-py/commit/56fc300c8597e41149fec65516f8b8a1b36eda61))

- **coverage**: Add [tool.coverage] config so pytest instruments src/ ([#19](https://github.com/bdperkin/gamesheet-sdk-py/pull/19),
  [`6c69895`](https://github.com/bdperkin/gamesheet-sdk-py/commit/6c698959ba877deffaabce2c3c127ecf85f0b261))

- **docs**: Fetch tags in docs.yml so hatch-vcs reports the real version ([#18](https://github.com/bdperkin/gamesheet-sdk-py/pull/18),
  [`f57e77c`](https://github.com/bdperkin/gamesheet-sdk-py/commit/f57e77ccd187a61d70e741a6100481faa39d2248))

### Build System

- **deps**: Bump actions/github-script from 7 to 9 in the actions group ([#17](https://github.com/bdperkin/gamesheet-sdk-py/pull/17),
  [`fa81737`](https://github.com/bdperkin/gamesheet-sdk-py/commit/fa81737766a04cc58f175562af6ca20a0031ef85))

### Chores

- **ci+deps**: Trigger workflows on every push, simplify hook deps ([#14](https://github.com/bdperkin/gamesheet-sdk-py/pull/14),
  [`de0ebc6`](https://github.com/bdperkin/gamesheet-sdk-py/commit/de0ebc65ccb65553494b80f327e7b5f946b12010))

### Code Style

- Apply automated formatting fixes ([#21](https://github.com/bdperkin/gamesheet-sdk-py/pull/21),
  [`9a6143d`](https://github.com/bdperkin/gamesheet-sdk-py/commit/9a6143d4e9e458cee697a0e25e8afcbcdf32fdb1))

### Continuous Integration

- **codecov**: Add Codecov coverage + test-analytics integration ([#15](https://github.com/bdperkin/gamesheet-sdk-py/pull/15),
  [`fec2d8e`](https://github.com/bdperkin/gamesheet-sdk-py/commit/fec2d8e04c32ff080a97415244b79d7367b932f2))

- **codecov**: Organize coverage by component + flag and validate schema ([#16](https://github.com/bdperkin/gamesheet-sdk-py/pull/16),
  [`9575b6e`](https://github.com/bdperkin/gamesheet-sdk-py/commit/9575b6e78396d3213719f480ea3ecd2d4ddb78d7))

- **codecov**: Raise coverage requirements to 100% across all gates ([#21](https://github.com/bdperkin/gamesheet-sdk-py/pull/21),
  [`9a6143d`](https://github.com/bdperkin/gamesheet-sdk-py/commit/9a6143d4e9e458cee697a0e25e8afcbcdf32fdb1))

### Documentation

- Update coverage requirements to 100% in documentation ([#21](https://github.com/bdperkin/gamesheet-sdk-py/pull/21),
  [`9a6143d`](https://github.com/bdperkin/gamesheet-sdk-py/commit/9a6143d4e9e458cee697a0e25e8afcbcdf32fdb1))

### Features

- Add leagues sub-command for listing leagues by association ([#22](https://github.com/bdperkin/gamesheet-sdk-py/pull/22),
  [`eeb775c`](https://github.com/bdperkin/gamesheet-sdk-py/commit/eeb775cf16e3e4accc7b17b5f62d9aeafbc6e64b))

### Testing

- Achieve 100% test coverage across all modules ([#21](https://github.com/bdperkin/gamesheet-sdk-py/pull/21),
  [`9a6143d`](https://github.com/bdperkin/gamesheet-sdk-py/commit/9a6143d4e9e458cee697a0e25e8afcbcdf32fdb1))

## v0.0.3 (2026-06-02)

### Bug Fixes

- **auth**: Silence CodeQL false-positive by splitting credential resolver ([#10](https://github.com/bdperkin/gamesheet-sdk-py/pull/10),
  [`49d304a`](https://github.com/bdperkin/gamesheet-sdk-py/commit/49d304a73be30ba7b182aeb629bc4e853c18fb45))

### Chores

- Overhaul pre-commit suite, consolidate tox into tox.ini, reformat pyproject ([#4](https://github.com/bdperkin/gamesheet-sdk-py/pull/4),
  [`b4bd212`](https://github.com/bdperkin/gamesheet-sdk-py/commit/b4bd212f528f9fdb54ea325f5de58c3739fbdb3c))

- **ci**: Pin workflow setup-python to 3.11 + fix codeql matrix indent ([#4](https://github.com/bdperkin/gamesheet-sdk-py/pull/4),
  [`b4bd212`](https://github.com/bdperkin/gamesheet-sdk-py/commit/b4bd212f528f9fdb54ea325f5de58c3739fbdb3c))

- **quality**: Comprehensive pre-commit/tox/CI overhaul and Makefile ([#13](https://github.com/bdperkin/gamesheet-sdk-py/pull/13),
  [`118f0c5`](https://github.com/bdperkin/gamesheet-sdk-py/commit/118f0c53ea5700aced1e4f38aea2a16f85049efc))

### Continuous Integration

- Skip no-commit-to-branch hook in GitHub Actions ([#5](https://github.com/bdperkin/gamesheet-sdk-py/pull/5),
  [`72244d5`](https://github.com/bdperkin/gamesheet-sdk-py/commit/72244d5d69497bb1fee231df2d5eeadb19897ed5))

### Documentation

- **claude**: Note radon/xenon complexity gates in CLAUDE.md ([#11](https://github.com/bdperkin/gamesheet-sdk-py/pull/11),
  [`e712efa`](https://github.com/bdperkin/gamesheet-sdk-py/commit/e712efa8192b37d21024436aa0217e72bf6e5a5b))

- **claude**: Note shell completion in CLAUDE.md ([#9](https://github.com/bdperkin/gamesheet-sdk-py/pull/9),
  [`29792c3`](https://github.com/bdperkin/gamesheet-sdk-py/commit/29792c35db239bfd23c7bfb4583bc5ec1ae777b5))

- **claude**: Refresh CLAUDE.md to reflect current state ([#7](https://github.com/bdperkin/gamesheet-sdk-py/pull/7),
  [`e2cf843`](https://github.com/bdperkin/gamesheet-sdk-py/commit/e2cf843f187bf5626d0eec6aaf5755f62e53c647))

- **readme**: Add comprehensive badges grouped by category ([#5](https://github.com/bdperkin/gamesheet-sdk-py/pull/5),
  [`72244d5`](https://github.com/bdperkin/gamesheet-sdk-py/commit/72244d5d69497bb1fee231df2d5eeadb19897ed5))

- **readme**: Overhaul to match current state and best practices ([#5](https://github.com/bdperkin/gamesheet-sdk-py/pull/5),
  [`72244d5`](https://github.com/bdperkin/gamesheet-sdk-py/commit/72244d5d69497bb1fee231df2d5eeadb19897ed5))

### Features

- **cli**: Native shell completion via `completion` subcommand ([#8](https://github.com/bdperkin/gamesheet-sdk-py/pull/8),
  [`8666810`](https://github.com/bdperkin/gamesheet-sdk-py/commit/8666810fa1965e58cb90bf0afae152147465f7d0))

- **quality**: Add radon/xenon metrics gates and refactor to grade A ([#10](https://github.com/bdperkin/gamesheet-sdk-py/pull/10),
  [`49d304a`](https://github.com/bdperkin/gamesheet-sdk-py/commit/49d304a73be30ba7b182aeb629bc4e853c18fb45))

### Refactoring

- **cli**: Adopt resource-oriented sub-command tree ([#6](https://github.com/bdperkin/gamesheet-sdk-py/pull/6),
  [`01a3ff1`](https://github.com/bdperkin/gamesheet-sdk-py/commit/01a3ff1d7c5d9f09333269bc7a2fd1f271748003))

## v0.0.2 (2026-05-25)

### Bug Fixes

- **auth**: Detect login outcome from Firebase API responses, not URL change
  ([`74278d2`](https://github.com/bdperkin/gamesheet-sdk-py/commit/74278d25acb7366be8bb034bec6fadb05f3a9f24))

- **auth**: Drive form on the same SPA route the dashboard renders on
  ([`bdced83`](https://github.com/bdperkin/gamesheet-sdk-py/commit/bdced836cf4e127b6731e4353739f8a720f5de33))

- **auth**: Navigate to /associations after auth so the SPA actually settles
  ([`5540c3d`](https://github.com/bdperkin/gamesheet-sdk-py/commit/5540c3de5c527f49f56b19141bf31c047def0929))

- **auth**: Short-circuit login when the saved session already authenticates
  ([`cbec0c9`](https://github.com/bdperkin/gamesheet-sdk-py/commit/cbec0c9bb7448402de8224fba98cb4037a81a6a8))

- **cli**: Remove dead `return` after ctx.exit() + add click to mypy hook deps
  ([`f5043c2`](https://github.com/bdperkin/gamesheet-sdk-py/commit/f5043c21fc19d82083b8173a396c2d4f2ec49d91))

### Build System

- Switch to hatch-vcs dynamic versioning from git tags
  ([`ec88da7`](https://github.com/bdperkin/gamesheet-sdk-py/commit/ec88da7118bb3c8896d69916fdd31f86c60cf015))

- **deps**: Bump the actions group with 7 updates ([#1](https://github.com/bdperkin/gamesheet-sdk-py/pull/1),
  [`163e596`](https://github.com/bdperkin/gamesheet-sdk-py/commit/163e5960f8c350bb67cd287db8ba4745d339a178))

### Chores

- Pin isort pre-commit hook to stable 8.0.1 ([#3](https://github.com/bdperkin/gamesheet-sdk-py/pull/3),
  [`d97d0e4`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d97d0e4f4db4fbf7ba255b70c26d793d7aec6c07))

- Pin isort pre-commit hook to stable 8.0.1 ([`9fdc552`](https://github.com/bdperkin/gamesheet-sdk-py/commit/9fdc55283965c5ea2fe18e54846eac2ce0dd8b93))

- **deps**: Pre-commit autoupdate ([#3](https://github.com/bdperkin/gamesheet-sdk-py/pull/3),
  [`d97d0e4`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d97d0e4f4db4fbf7ba255b70c26d793d7aec6c07))

### Documentation

- **explanation**: Document branch-protection rationale
  ([`b31fb11`](https://github.com/bdperkin/gamesheet-sdk-py/commit/b31fb111668f50faa833775b34bcd7a41e5e6603))

- **how-to**: Cover the pending-publisher flow in cut-a-release
  ([`d92af49`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d92af495a2b522e28a76c60adf4ac6e9296d6869))

### Features

- Add BrowserSession Playwright foundation (real code, slice 2)
  ([`0c3ec56`](https://github.com/bdperkin/gamesheet-sdk-py/commit/0c3ec56e63d138b51cf094bc7985394188ebcc95))

- Add Config + Session foundation (real code, slice 1)
  ([`ed8d5a5`](https://github.com/bdperkin/gamesheet-sdk-py/commit/ed8d5a59520b14886af9fd8e452b0c3e4ead5abd))

- Add list-associations workflow (real code, slice 5)
  ([`28c06fb`](https://github.com/bdperkin/gamesheet-sdk-py/commit/28c06fbac54ee54f8d551ce14d7e98b995f8f418))

- **auth**: Add AuthenticatedSession with transparent token refresh on 401
  ([`d9463b3`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d9463b3115e92ee014c26652454a67a68c5be374))

- **auth**: Add login() against the GameSheet WebUI (real code, slice 3)
  ([`4d1cadd`](https://github.com/bdperkin/gamesheet-sdk-py/commit/4d1cadd89cbc58cc1a8e86d4192c221db1f1021c))

- **cli**: Colorize log levels with colorlog (TTY + NO_COLOR aware)
  ([`11cad33`](https://github.com/bdperkin/gamesheet-sdk-py/commit/11cad3334751ad3b09548b7d510b45d1eeade8a6))

- **cli**: Restructure to a click subcommand tree with `login` (slice 4)
  ([`88f4561`](https://github.com/bdperkin/gamesheet-sdk-py/commit/88f45619995e9688fe1b6009202512a34b738332))

- **cli**: Tune the colorlog format string for legibility ([#3](https://github.com/bdperkin/gamesheet-sdk-py/pull/3),
  [`d97d0e4`](https://github.com/bdperkin/gamesheet-sdk-py/commit/d97d0e4f4db4fbf7ba255b70c26d793d7aec6c07))

- **cli**: Tune the colorlog format string for legibility
  ([`bca15f5`](https://github.com/bdperkin/gamesheet-sdk-py/commit/bca15f5175dde92cb6dcee63cbc95bd4d2df049c))

- **output**: Unified multi-format renderer with tabulate + rich
  ([`126f558`](https://github.com/bdperkin/gamesheet-sdk-py/commit/126f558e718ec88b2f2c787d96b452253aa98e4b))

## v0.0.1 (2026-05-24)

- Initial Release
