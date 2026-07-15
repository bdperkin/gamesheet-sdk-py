# Getting Help with gamesheet-sdk-py

This document provides resources for getting help with the GameSheet SDK for Python.

## Documentation

Before opening an issue, please check our comprehensive documentation:

- **[Getting Started Tutorial](https://bdperkin.github.io/gamesheet-sdk-py/tutorials/getting-started.html)** — Installation and first steps
- **[API Reference](https://bdperkin.github.io/gamesheet-sdk-py/reference/api.html)** — Complete module, class, and function documentation
- **[CLI Reference](https://bdperkin.github.io/gamesheet-sdk-py/reference/cli.html)** — Command-line interface documentation
- **[How-To Guides](https://bdperkin.github.io/gamesheet-sdk-py/how-to/)** — Task-oriented recipes for common workflows
- **[Explanation Guides](https://bdperkin.github.io/gamesheet-sdk-py/explanation/)** — Background on design decisions and architecture

## Common Issues

### Authentication Problems

**Issue**: `gamesheet-admin login` fails or returns HTTP 401/403 errors.

**Solutions**:

1. Ensure you have valid GameSheet credentials
2. Re-run `gamesheet-admin login` to refresh your session
3. Check that cookies and tokens are being saved to `~/.gamesheet/`
4. Try `gamesheet-admin --no-headless login` to see the browser flow
5. Clear old session data: `rm -rf ~/.gamesheet/` and log in again

See [Authentication Workflow Tutorial](https://bdperkin.github.io/gamesheet-sdk-py/tutorials/authentication-workflow.html) for details.

### Installation Issues

**Issue**: `pip install gamesheet-sdk-py` fails or Playwright browsers don't install.

**Solutions**:

1. Verify Python version: `python --version` (must be 3.11–3.14)
2. Upgrade pip: `pip install --upgrade pip`
3. Install Playwright browsers: `python -m playwright install chromium`
4. Check [Installation Guide](https://github.com/bdperkin/gamesheet-sdk-py#installation) for platform-specific instructions

### Import Errors

**Issue**: `ModuleNotFoundError: No module named 'gamesheet_sdk'`

**Solutions**:

1. Ensure you're in the correct virtual environment: `which python`
2. Reinstall the package: `pip install --force-reinstall gamesheet-sdk-py`
3. For development installs: `pip install -e ".[all]"` from the repo root

### Test Failures

**Issue**: Tests fail locally or in CI.

**Solutions**:

1. Install test dependencies: `pip install -e ".[pytest]"`
2. Install Playwright browsers: `python -m playwright install chromium`
3. Run subset of tests: `pytest -m "not browser"` (skips slow browser tests)
4. Check [Development Setup](https://bdperkin.github.io/gamesheet-sdk-py/how-to/development-setup.html) for full guidance

## Asking Questions

### GitHub Discussions (Preferred)

For general questions, usage help, and community discussion:

**[Open a Discussion](https://github.com/bdperkin/gamesheet-sdk-py/discussions)**

GitHub Discussions is the best place for:

- "How do I...?" questions
- Feature requests and ideas
- Sharing workflows and scripts
- Community support

### GitHub Issues

For bug reports, security vulnerabilities, and confirmed issues:

**[Open an Issue](https://github.com/bdperkin/gamesheet-sdk-py/issues/new)**

**Before opening an issue**:

1. Search existing issues to avoid duplicates
2. Check the [documentation](https://bdperkin.github.io/gamesheet-sdk-py/)
3. Provide a minimal reproducible example
4. Include version info: `gamesheet-admin --version` or `python -c "import gamesheet_sdk; print(gamesheet_sdk.__version__)"`
5. Include Python version: `python --version`
6. Include OS and platform information

**For security vulnerabilities**, see [SECURITY.md](SECURITY.md) for responsible disclosure process.

## Contributing

If you'd like to contribute code, documentation, or bug fixes:

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines
2. Follow the [Code of Conduct](CODE_OF_CONDUCT.md)
3. Open a pull request following our [PR checklist](CONTRIBUTING.md#pull-request-process)

## Response Times

This is an **open-source project maintained by volunteers**. Response times vary based on maintainer availability:

- **Security vulnerabilities**: 48 hours acknowledgment (see [SECURITY.md](SECURITY.md))
- **Bug reports**: Best effort, typically within 1 week
- **Feature requests**: Reviewed during planning cycles
- **Questions/discussions**: Community-driven, response times vary

## Project Status

**Current Status**: Alpha

This project is in active development. The API surface may change between releases until 1.0.0. See the [CHANGELOG](CHANGELOG.md) for version history and
breaking changes.

## Additional Resources

- **GitHub Repository**: <https://github.com/bdperkin/gamesheet-sdk-py>
- **PyPI Package**: <https://pypi.org/project/gamesheet-sdk-py/>
- **Documentation**: <https://bdperkin.github.io/gamesheet-sdk-py/>
- **Issue Tracker**: <https://github.com/bdperkin/gamesheet-sdk-py/issues>
- **Discussions**: <https://github.com/bdperkin/gamesheet-sdk-py/discussions>

## Related Projects

- **GameSheet Platform**: <https://gamesheet.app/>
- **Playwright Python**: <https://playwright.dev/python/>
- **Pydantic**: <https://docs.pydantic.dev/>
- **Click**: <https://click.palletsprojects.com/>

______________________________________________________________________

**Thank you for using gamesheet-sdk-py!** Your feedback and contributions help make this project better for everyone.
