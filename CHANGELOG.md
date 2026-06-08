# CHANGELOG

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
