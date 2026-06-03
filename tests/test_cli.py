"""Tests for :mod:`gamesheet_sdk.cli`."""

# pylint: disable=redefined-outer-name,protected-access
# - redefined-outer-name: pytest fixtures share names with the params they bind
# - protected-access: tests legitimately inspect internals

from __future__ import annotations

import json
import logging
import sys
from typing import TYPE_CHECKING

# pylint: disable=wrong-import-position
if TYPE_CHECKING:
    from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import colorlog
import pytest
import yaml
from click.shell_completion import BashComplete
from click.testing import CliRunner

from gamesheet_sdk import __version__
from gamesheet_sdk.auth import LOGIN_PATH
from gamesheet_sdk.cli import (
    ResourceGroup,
    _configure_logging,
    cli,
    confirm_destructive,
    main,
)
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ---------- top-level group ----------------------------------------------


def test_main_no_args_prints_help_and_exits_zero() -> None:
    """`gamesheet-sdk-py` with no subcommand shows help and returns 0."""
    assert main([]) == 0


def test_version_flag_exits_zero(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help_flag_lists_login_subcommand(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "login" in result.output


def test_unknown_subcommand_returns_two() -> None:
    """Unknown subcommand is a usage error -> exit 2."""
    assert main(["totally-not-a-subcommand"]) == 2


# ---------- logging configuration ----------------------------------------


def test_configure_logging_default_warning_level() -> None:
    _configure_logging(0)
    assert logging.getLogger().level == logging.WARNING


def test_configure_logging_v_sets_info() -> None:
    _configure_logging(1)
    assert logging.getLogger().level == logging.INFO


def test_configure_logging_vv_sets_debug() -> None:
    _configure_logging(2)
    assert logging.getLogger().level == logging.DEBUG


def test_configure_logging_vvv_clamps_to_debug() -> None:
    _configure_logging(7)
    assert logging.getLogger().level == logging.DEBUG


# ---------- login subcommand --------------------------------------------


@patch("gamesheet_sdk.cli._login_action")
def test_login_succeeds_with_explicit_credentials(mock_login: MagicMock, runner: CliRunner) -> None:
    result = runner.invoke(
        cli,
        ["login", "--email", "alice@example.com", "--password", "hunter2"],
    )
    assert result.exit_code == 0, result.output
    assert "Login succeeded" in result.output
    mock_login.assert_called_once()
    _, kwargs = mock_login.call_args
    assert kwargs["email"] == "alice@example.com"
    assert kwargs["password"] == "hunter2"
    assert kwargs["timeout"] == 15.0


@patch("gamesheet_sdk.cli._login_action")
def test_login_failure_exits_one(mock_login: MagicMock, runner: CliRunner) -> None:
    mock_login.side_effect = AuthenticationError("bad creds")
    result = runner.invoke(
        cli,
        ["login", "--email", "a@b.c", "--password", "x"],
    )
    assert result.exit_code == 1
    assert "Login failed" in result.output
    assert "bad creds" in result.output


@patch("gamesheet_sdk.cli._login_action")
def test_login_passes_custom_timeout(mock_login: MagicMock, runner: CliRunner) -> None:
    runner.invoke(
        cli,
        [
            "login",
            "--email",
            "a@b.c",
            "--password",
            "x",
            "--timeout",
            "5",
        ],
    )
    _, kwargs = mock_login.call_args
    assert kwargs["timeout"] == 5.0


@patch("gamesheet_sdk.cli._login_action")
def test_login_reads_credentials_from_env(
    mock_login: MagicMock,
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GAMESHEET_USERNAME", "envuser@example.com")
    monkeypatch.setenv("GAMESHEET_PASSWORD", "envpw")
    result = runner.invoke(cli, ["login"])
    assert result.exit_code == 0, result.output
    _, kwargs = mock_login.call_args
    assert kwargs["email"] == "envuser@example.com"
    assert kwargs["password"] == "envpw"


@patch("gamesheet_sdk.cli._login_action")
def test_login_prompts_when_no_credentials_anywhere(mock_login: MagicMock, runner: CliRunner) -> None:
    """Without --email/--password and without env vars, click prompts."""
    result = runner.invoke(
        cli,
        ["login"],
        input="prompt-user@example.com\nprompt-pw\n",
    )
    assert result.exit_code == 0, result.output
    _, kwargs = mock_login.call_args
    assert kwargs["email"] == "prompt-user@example.com"
    assert kwargs["password"] == "prompt-pw"


# ---------- base-url / headless overrides flow into Config -------------


@patch("gamesheet_sdk.cli._login_action")
@patch("gamesheet_sdk.cli.BrowserSession")
def test_base_url_override_reaches_config(
    mock_browser: MagicMock,
    mock_login: MagicMock,
    runner: CliRunner,
) -> None:
    del mock_login  # unused; we just need to short-circuit auth
    runner.invoke(
        cli,
        [
            "--base-url",
            "https://override.example",
            "login",
            "--email",
            "a@b.c",
            "--password",
            "x",
        ],
    )
    config_arg = mock_browser.call_args[0][0]
    assert config_arg.base_url == "https://override.example"


@patch("gamesheet_sdk.cli._login_action")
@patch("gamesheet_sdk.cli.BrowserSession")
def test_no_headless_reaches_config(
    mock_browser: MagicMock,
    mock_login: MagicMock,
    runner: CliRunner,
) -> None:
    del mock_login
    runner.invoke(
        cli,
        [
            "--no-headless",
            "login",
            "--email",
            "a@b.c",
            "--password",
            "x",
        ],
    )
    config_arg = mock_browser.call_args[0][0]
    assert config_arg.browser_headless is False


# ---------- main() wrapper edge cases ------------------------------------


def test_main_propagates_systemexit_int() -> None:
    """Plain SystemExit(int) inside a click command should map to its code."""
    with patch("gamesheet_sdk.cli._login_action", side_effect=SystemExit(7)):
        rc = main(["login", "--email", "a@b.c", "--password", "x"])
    assert rc == 7


def test_main_login_path_constant_matches_auth_module() -> None:
    """Trivial smoke: LOGIN_PATH is what cli ends up wiring auth.login to."""
    assert LOGIN_PATH.startswith("/")


# ---------- associations list subcommand --------------------------------


def _stub_associations(*ids_and_titles: tuple[str, str]) -> list[MagicMock]:
    """Build fake Association objects without needing pydantic instantiation."""
    out = []
    for aid, title in ids_and_titles:
        a = MagicMock()
        a.id = aid
        a.title = title
        a.model_dump.return_value = {"id": aid, "title": title}
        out.append(a)
    return out


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_default_table_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_associations(
        ("11", "Hockey Time Productions"),
        ("40", "SuperSeries AAA"),
    )
    result = runner.invoke(cli, ["associations", "list"])
    assert result.exit_code == 0, result.output
    # Default --format is tabulate's "simple": id and title appear on the same
    # row, no fixed separator. Just assert both pairs are present.
    assert "11" in result.output
    assert "Hockey Time Productions" in result.output
    assert "40" in result.output
    assert "SuperSeries AAA" in result.output


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_json_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_associations(("11", "Hockey Time"))
    result = runner.invoke(cli, ["associations", "list", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == [{"id": "11", "title": "Hockey Time"}]


@patch("gamesheet_sdk.cli.load_refresh_token", return_value=None)
@patch("gamesheet_sdk.cli.load_access_token", return_value=None)
def test_list_associations_missing_token_exits_one(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    runner: CliRunner,
) -> None:
    result = runner.invoke(cli, ["associations", "list"])
    assert result.exit_code == 1
    assert "No saved session" in result.output
    assert "Run `gamesheet-sdk-py login`" in result.output


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_authentication_error_exits_one(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.side_effect = AuthenticationError("HTTP 401")
    result = runner.invoke(cli, ["associations", "list"])
    assert result.exit_code == 1
    assert "Authentication required" in result.output


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_other_error_exits_one(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.side_effect = GameSheetError("HTTP 500")
    result = runner.invoke(cli, ["associations", "list"])
    assert result.exit_code == 1
    assert "GameSheet error" in result.output


# ---------- color-aware logging configuration ----------------------------


def test_configure_logging_uses_colored_formatter_on_tty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True, raising=False)
    _configure_logging(0)
    handler = logging.getLogger().handlers[0]
    assert isinstance(handler.formatter, colorlog.ColoredFormatter)


def test_configure_logging_uses_plain_formatter_when_not_a_tty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(sys.stderr, "isatty", bool, raising=False)
    _configure_logging(0)
    handler = logging.getLogger().handlers[0]
    assert not isinstance(handler.formatter, colorlog.ColoredFormatter)
    assert isinstance(handler.formatter, logging.Formatter)


def test_configure_logging_honors_no_color_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A user-set NO_COLOR env var disables ANSI even on a TTY."""
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True, raising=False)
    _configure_logging(0)
    handler = logging.getLogger().handlers[0]
    assert not isinstance(handler.formatter, colorlog.ColoredFormatter)


# ---------- associations list: --format / --output / --columns ----------


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_csv_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_associations(("11", "Hockey Time"))
    result = runner.invoke(cli, ["associations", "list", "--format", "csv"])
    assert result.exit_code == 0, result.output
    lines = result.output.strip().splitlines()
    assert lines[0] == "id,title"
    assert lines[1] == "11,Hockey Time"


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_yaml_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_associations(("11", "Hockey Time"))
    result = runner.invoke(cli, ["associations", "list", "--format", "yaml"])
    assert result.exit_code == 0, result.output
    data = yaml.safe_load(result.output)
    assert data == [{"id": "11", "title": "Hockey Time"}]


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_grid_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_associations(("11", "Hockey Time"))
    result = runner.invoke(cli, ["associations", "list", "--format", "grid"])
    assert result.exit_code == 0, result.output
    # Grid uses ASCII +/-/| corners. Just check one cell.
    assert "+" in result.output
    assert "Hockey Time" in result.output


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_unknown_format_returns_two(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    del mock_list
    result = runner.invoke(cli, ["associations", "list", "--format", "not-real"])
    # click's Choice gives usage error -> 2.
    assert result.exit_code == 2


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_writes_to_output_file(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    mock_list.return_value = _stub_associations(("11", "Hockey Time"))
    out_path = tmp_path / "associations.csv"
    result = runner.invoke(
        cli,
        [
            "associations",
            "list",
            "--format",
            "csv",
            "--output",
            str(out_path),
        ],
    )
    assert result.exit_code == 0, result.output
    # Nothing on stdout (it all went to the file).
    assert result.output.strip() == ""
    contents = out_path.read_text()
    assert contents.startswith("id,title")
    assert "11,Hockey Time" in contents


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_columns_filter(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    a = MagicMock()
    a.model_dump.return_value = {"id": "11", "title": "Hockey", "logo": "x.png"}
    mock_list.return_value = [a]
    result = runner.invoke(
        cli,
        ["associations", "list", "--format", "csv", "--columns", "title,id"],
    )
    assert result.exit_code == 0, result.output
    lines = result.output.strip().splitlines()
    assert lines[0] == "title,id"
    assert lines[1] == "Hockey,11"
    assert "logo" not in result.output


# ---------- ResourceGroup: aliases + default sub-command -----------------


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_associations_no_subcommand_defaults_to_list(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    """`associations` with no sub-command implicitly runs `list`."""
    mock_list.return_value = _stub_associations(("11", "Hockey Time"))
    result = runner.invoke(cli, ["associations"])
    assert result.exit_code == 0, result.output
    assert "Hockey Time" in result.output
    mock_list.assert_called_once()


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_associations_ls_alias_runs_list(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    """`associations ls` resolves to the `list` callback."""
    mock_list.return_value = _stub_associations(("11", "Hockey Time"))
    result = runner.invoke(cli, ["associations", "ls", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == [{"id": "11", "title": "Hockey Time"}]


def test_associations_help_lists_canonical_and_aliases(runner: CliRunner) -> None:
    """`associations --help` shows the canonical name with aliases in parens."""
    result = runner.invoke(cli, ["associations", "--help"])
    assert result.exit_code == 0, result.output
    assert "list (ls)" in result.output


def test_root_help_no_longer_lists_flat_list_associations(runner: CliRunner) -> None:
    """The old flat `list-associations` command has been removed from root."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "list-associations" not in result.output
    assert "associations" in result.output


def test_unknown_associations_subcommand_returns_two(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["associations", "not-a-verb"])
    assert result.exit_code == 2


def test_resource_group_alias_table_is_flat() -> None:
    """ResourceGroup flattens {canonical: (alts,)} into {alt: canonical}."""
    grp = ResourceGroup(
        "demo",
        aliases={"list": ("ls",), "delete": ("rm", "remove")},
    )
    assert grp._aliases == {"ls": "list", "rm": "delete", "remove": "delete"}


# ---------- confirm_destructive helper -----------------------------------


def test_confirm_destructive_aborts_without_force(runner: CliRunner) -> None:
    """No `--force` and a negative prompt response aborts."""

    @click.command("delete")
    @confirm_destructive("the demo resource")
    def demo_delete() -> None:
        click.echo("deleted")

    result = runner.invoke(demo_delete, [], input="n\n")
    # Aborted confirmations exit with click's standard abort code (1).
    assert result.exit_code != 0
    assert "deleted" not in result.output
    assert "Really delete the demo resource" in result.output


def test_confirm_destructive_runs_with_force(runner: CliRunner) -> None:
    """`--force` skips the prompt and runs the wrapped command."""

    @click.command("delete")
    @confirm_destructive("the demo resource")
    def demo_delete() -> None:
        click.echo("deleted")

    result = runner.invoke(demo_delete, ["--force"])
    assert result.exit_code == 0, result.output
    assert "deleted" in result.output


def test_confirm_destructive_runs_on_yes(runner: CliRunner) -> None:
    """A 'y' at the prompt runs the wrapped command."""

    @click.command("delete")
    @confirm_destructive("the demo resource")
    def demo_delete() -> None:
        click.echo("deleted")

    result = runner.invoke(demo_delete, [], input="y\n")
    assert result.exit_code == 0, result.output
    assert "deleted" in result.output


def test_confirm_destructive_short_force_alias(runner: CliRunner) -> None:
    """`-f` is the documented short form of `--force`."""

    @click.command("delete")
    @confirm_destructive("the demo resource")
    def demo_delete() -> None:
        click.echo("deleted")

    result = runner.invoke(demo_delete, ["-f"])
    assert result.exit_code == 0, result.output
    assert "deleted" in result.output


# ---------- shell completion --------------------------------------------


def test_completion_bash_script_contains_env_var(runner: CliRunner) -> None:
    """`completion bash` prints a script that wires up the env var."""
    result = runner.invoke(cli, ["completion", "bash"])
    assert result.exit_code == 0, result.output
    assert "_GAMESHEET_SDK_PY_COMPLETE" in result.output
    assert "bash_complete" in result.output


def test_completion_zsh_script_contains_env_var(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["completion", "zsh"])
    assert result.exit_code == 0, result.output
    assert "_GAMESHEET_SDK_PY_COMPLETE" in result.output


def test_completion_fish_script_contains_env_var(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["completion", "fish"])
    assert result.exit_code == 0, result.output
    assert "_GAMESHEET_SDK_PY_COMPLETE" in result.output


def test_completion_invalid_shell_returns_two(runner: CliRunner) -> None:
    """An unsupported shell name fails Choice validation -> exit 2."""
    result = runner.invoke(cli, ["completion", "tcsh"])
    assert result.exit_code == 2
    assert "tcsh" in result.output


def test_completion_shell_arg_is_case_insensitive(runner: CliRunner) -> None:
    """``BASH`` resolves the same completion class as ``bash``."""
    result = runner.invoke(cli, ["completion", "BASH"])
    assert result.exit_code == 0, result.output
    assert "_GAMESHEET_SDK_PY_COMPLETE" in result.output


def test_resource_group_shell_complete_includes_alias() -> None:
    """`associations <TAB>` enumerates both canonical and alias names."""
    assoc = cli.commands["associations"]
    ctx = click.Context(assoc, info_name="associations", parent=click.Context(cli))
    items = assoc.shell_complete(ctx, "")
    values = {item.value for item in items}
    assert "list" in values
    assert "ls" in values


def test_resource_group_shell_complete_alias_help_marks_alias() -> None:
    """The alias completion item's help text identifies it as an alias."""
    assoc = cli.commands["associations"]
    ctx = click.Context(assoc, info_name="associations", parent=click.Context(cli))
    items = {item.value: item for item in assoc.shell_complete(ctx, "")}
    assert items["ls"].help is not None
    assert "alias for list" in items["ls"].help


def test_resource_group_shell_complete_respects_prefix() -> None:
    """`associations l<TAB>` only returns candidates that start with the prefix."""
    assoc = cli.commands["associations"]
    ctx = click.Context(assoc, info_name="associations", parent=click.Context(cli))
    items = assoc.shell_complete(ctx, "l")
    values = {item.value for item in items}
    assert values == {"list", "ls"}


def test_resource_group_shell_complete_skips_hidden_command_and_its_alias() -> None:
    """Hidden canonical commands and aliases pointing at them don't surface."""
    group = ResourceGroup(
        "demo",
        aliases={"list": ("ls",), "show": ("s",)},
    )

    @group.command("list", hidden=True)
    def _hidden_list() -> None:
        pass

    @group.command("show")
    def _visible_show() -> None:
        pass

    ctx = click.Context(group, info_name="demo")
    items = group.shell_complete(ctx, "")
    values = {item.value for item in items}
    assert values == {"show", "s"}


def test_format_choice_shell_complete_lists_every_choice() -> None:
    """`associations list --format <TAB>` suggests every Choice value."""
    assoc = cli.commands["associations"]
    assert isinstance(assoc, click.Group)
    list_cmd = assoc.commands["list"]
    format_param = next(p for p in list_cmd.params if p.name == "output_format")
    ctx = click.Context(list_cmd)
    items = format_param.shell_complete(ctx, "")
    values = {item.value for item in items}
    for fmt in ("json", "yaml", "csv", "tsv", "simple", "grid", "html", "latex"):
        assert fmt in values, f"Missing completion for {fmt}"


def test_completion_does_not_descend_into_default_subcommand() -> None:
    """`associations <TAB>` must surface the group's verbs, not list's options.

    Regression guard: ResourceGroup.parse_args injects ``default`` when
    invoked bare, but it must skip that injection during click's
    completion walk (``resilient_parsing=True``) — otherwise click
    descends into ``list`` and tab-completion silently breaks.
    """
    completions = BashComplete(cli, {}, "gamesheet-sdk-py", "_GAMESHEET_SDK_PY_COMPLETE").get_completions(
        ["associations"],
        "",
    )
    values = {c.value for c in completions}
    assert "list" in values
    assert "ls" in values


# ---------- ResourceGroup with no aliases (line 75) -------------------------


def test_resource_group_no_aliases_initializes_empty() -> None:
    """ResourceGroup without aliases should initialize with empty alias map."""
    grp = ResourceGroup("demo")  # no aliases param
    assert not grp._aliases


# ---------- _visible_command_rows with hidden command (line 118) ------------


def test_resource_group_format_commands_excludes_hidden() -> None:
    """Hidden commands should not appear in the formatted command list."""
    group = ResourceGroup("demo", aliases={"list": ("ls",)})

    @group.command("list", hidden=True)
    def _hidden() -> None:
        pass

    @group.command("show")
    def _visible() -> None:
        pass

    ctx = click.Context(group)
    formatter = click.HelpFormatter()
    group.format_commands(ctx, formatter)
    output = formatter.getvalue()
    assert "list" not in output
    assert "ls" not in output
    assert "show" in output


# ---------- format_commands with empty rows (line 124) ----------------------


def test_resource_group_format_commands_empty_group() -> None:
    """A group with no commands should not write a Commands section."""
    group = ResourceGroup("demo")
    ctx = click.Context(group)
    formatter = click.HelpFormatter()
    group.format_commands(ctx, formatter)
    output = formatter.getvalue()
    assert "Commands" not in output


# ---------- _parse_columns_spec empty result (line 452) ---------------------


@patch("gamesheet_sdk.cli._list_associations_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_associations_empty_columns_spec(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    """Empty or whitespace-only --columns should be treated as None."""
    mock_list.return_value = _stub_associations(("11", "Hockey"))
    result = runner.invoke(
        cli,
        ["associations", "list", "--format", "csv", "--columns", "  "],
    )
    assert result.exit_code == 0, result.output
    # All columns should be present when columns spec is empty
    assert "id" in result.output
    assert "title" in result.output


# ---------- _resolve_system_exit with code=None (line 510) ------------------


def test_main_systemexit_none_returns_zero() -> None:
    """SystemExit with code=None should return 0."""
    with patch("gamesheet_sdk.cli._login_action", side_effect=SystemExit(None)):
        rc = main(["login", "--email", "a@b.c", "--password", "x"])
    assert rc == 0


# ---------- _resolve_system_exit with non-int code (line 513) ---------------


def test_main_systemexit_string_returns_one() -> None:
    """SystemExit with a string code should return 1."""
    with patch("gamesheet_sdk.cli._login_action", side_effect=SystemExit("error message")):
        rc = main(["login", "--email", "a@b.c", "--password", "x"])
    assert rc == 1


# ---------- click.exceptions.Exit (line 519) --------------------------------


def test_main_click_exit_returns_code() -> None:
    """click.exceptions.Exit should return its exit_code.

    This tests the case where cli.main() itself raises Exit (not a command).
    """
    with patch.object(cli, "main", side_effect=click.exceptions.Exit(42)):
        rc = main([])
    assert rc == 42


# ---------- click.exceptions.Abort (lines 524-525) --------------------------


def test_main_click_abort_returns_one() -> None:
    """click.exceptions.Abort should return 1."""
    with patch("gamesheet_sdk.cli._login_action", side_effect=click.exceptions.Abort):
        rc = main(["login", "--email", "a@b.c", "--password", "x"])
    assert rc == 1


# ---------- __main__ block (line 549) ----------------------------------------


def test_cli_module_main_block() -> None:
    """The __name__ == '__main__' block should be executable via python -m."""
    import subprocess  # noqa: S404 # nosec B404 # pylint: disable=import-outside-toplevel

    # Run the module as __main__ with --version to verify it works
    result = subprocess.run(  # noqa: S603 # nosec B603
        [sys.executable, "-m", "gamesheet_sdk.cli", "--version"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,  # We check returncode explicitly below
    )
    assert result.returncode == 0
    assert __version__ in result.stdout


# ---------- leagues list subcommand --------------------------------------


def _stub_leagues(*id_title_pairs: tuple[str, str]) -> list[MagicMock]:
    """Build fake League objects without needing pydantic instantiation."""
    out = []
    for lid, title in id_title_pairs:
        lg = MagicMock()
        lg.id = lid
        lg.title = title
        lg.association_id = "38"
        lg.model_dump.return_value = {
            "id": lid,
            "title": title,
            "association_id": "38",
        }
        out.append(lg)
    return out


@patch("gamesheet_sdk.cli._list_leagues_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_leagues_default_table_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_leagues(
        ("101", "18U AAA"),
        ("102", "16U AA"),
    )
    result = runner.invoke(cli, ["leagues", "list", "38"])
    assert result.exit_code == 0, result.output
    assert "101" in result.output
    assert "18U AAA" in result.output
    assert "102" in result.output
    assert "16U AA" in result.output


@patch("gamesheet_sdk.cli._list_leagues_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_leagues_json_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_leagues(("101", "18U AAA"))
    result = runner.invoke(cli, ["leagues", "list", "38", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == [{"id": "101", "title": "18U AAA", "association_id": "38"}]


@patch("gamesheet_sdk.cli.load_refresh_token", return_value=None)
@patch("gamesheet_sdk.cli.load_access_token", return_value=None)
def test_list_leagues_missing_token_exits_one(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    runner: CliRunner,
) -> None:
    result = runner.invoke(cli, ["leagues", "list", "38"])
    assert result.exit_code == 1
    assert "No saved session" in result.output
    assert "Run `gamesheet-sdk-py login`" in result.output


@patch("gamesheet_sdk.cli._list_leagues_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_leagues_authentication_error_exits_one(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.side_effect = AuthenticationError("HTTP 401")
    result = runner.invoke(cli, ["leagues", "list", "38"])
    assert result.exit_code == 1
    assert "Authentication required" in result.output


@patch("gamesheet_sdk.cli._list_leagues_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_leagues_other_error_exits_one(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.side_effect = GameSheetError("HTTP 500")
    result = runner.invoke(cli, ["leagues", "list", "38"])
    assert result.exit_code == 1
    assert "GameSheet error" in result.output


@patch("gamesheet_sdk.cli._list_leagues_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_leagues_csv_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_leagues(("101", "18U AAA"))
    result = runner.invoke(cli, ["leagues", "list", "38", "--format", "csv"])
    assert result.exit_code == 0, result.output
    lines = result.output.strip().splitlines()
    assert "id" in lines[0]
    assert "title" in lines[0]
    assert "101" in lines[1]
    assert "18U AAA" in lines[1]


@patch("gamesheet_sdk.cli._list_leagues_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_leagues_yaml_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_leagues(("101", "18U AAA"))
    result = runner.invoke(cli, ["leagues", "list", "38", "--format", "yaml"])
    assert result.exit_code == 0, result.output
    data = yaml.safe_load(result.output)
    assert data == [{"id": "101", "title": "18U AAA", "association_id": "38"}]


@patch("gamesheet_sdk.cli._list_leagues_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_leagues_output_to_file(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    mock_list.return_value = _stub_leagues(("101", "18U AAA"))
    output_file = tmp_path / "leagues.json"
    result = runner.invoke(
        cli,
        ["leagues", "list", "38", "--format", "json", "--output", str(output_file)],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(output_file.read_text())
    assert data == [{"id": "101", "title": "18U AAA", "association_id": "38"}]


@patch("gamesheet_sdk.cli._list_leagues_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_leagues_columns_filter(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_leagues(("101", "18U AAA"))
    result = runner.invoke(
        cli,
        ["leagues", "list", "38", "--format", "csv", "--columns", "id,title"],
    )
    assert result.exit_code == 0, result.output
    lines = result.output.strip().splitlines()
    assert lines[0] == "id,title"
    assert lines[1] == "101,18U AAA"


def test_leagues_group_has_help_option(runner: CliRunner) -> None:
    """The leagues group should accept -h and --help."""
    result_short = runner.invoke(cli, ["leagues", "-h"])
    assert result_short.exit_code == 0
    assert "leagues" in result_short.output.lower()

    result_long = runner.invoke(cli, ["leagues", "--help"])
    assert result_long.exit_code == 0
    assert "leagues" in result_long.output.lower()


def test_leagues_list_alias_works(runner: CliRunner) -> None:
    """The 'ls' alias should invoke the list command."""
    with (
        patch("gamesheet_sdk.cli._list_leagues_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["leagues", "ls", "38"])
        assert result.exit_code == 0
        mock_list.assert_called_once()


def test_leagues_missing_association_id_shows_error(runner: CliRunner) -> None:
    """Calling 'leagues list' without an association ID should show an error."""
    result = runner.invoke(cli, ["leagues", "list"])
    assert result.exit_code == 2  # Usage error
    assert "ASSOCIATION_ID" in result.output or "Missing argument" in result.output


# ---------- seasons list subcommand --------------------------------------


def _stub_seasons(*id_title_pairs: tuple[str, str]) -> list[MagicMock]:
    """Build fake Season objects without needing pydantic instantiation."""
    out = []
    for sid, title in id_title_pairs:
        s = MagicMock()
        s.id = sid
        s.title = title
        s.league_id = "1148580"
        s.model_dump.return_value = {
            "id": sid,
            "title": title,
            "league_id": "1148580",
        }
        out.append(s)
    return out


@patch("gamesheet_sdk.cli._list_seasons_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_seasons_default_table_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_seasons(
        ("501", "2024-2025"),
        ("502", "2023-2024"),
    )
    result = runner.invoke(cli, ["seasons", "list", "1148580"])
    assert result.exit_code == 0, result.output
    assert "501" in result.output
    assert "2024-2025" in result.output
    assert "502" in result.output
    assert "2023-2024" in result.output


@patch("gamesheet_sdk.cli._list_seasons_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_seasons_json_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_seasons(("501", "2024-2025"))
    result = runner.invoke(cli, ["seasons", "list", "1148580", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == [{"id": "501", "title": "2024-2025", "league_id": "1148580"}]


@patch("gamesheet_sdk.cli.load_refresh_token", return_value=None)
@patch("gamesheet_sdk.cli.load_access_token", return_value=None)
def test_list_seasons_missing_token_exits_one(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    runner: CliRunner,
) -> None:
    result = runner.invoke(cli, ["seasons", "list", "1148580"])
    assert result.exit_code == 1
    assert "No saved session" in result.output
    assert "Run `gamesheet-sdk-py login`" in result.output


@patch("gamesheet_sdk.cli._list_seasons_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_seasons_authentication_error_exits_one(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.side_effect = AuthenticationError("HTTP 401")
    result = runner.invoke(cli, ["seasons", "list", "1148580"])
    assert result.exit_code == 1
    assert "Authentication required" in result.output


@patch("gamesheet_sdk.cli._list_seasons_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_seasons_other_error_exits_one(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.side_effect = GameSheetError("HTTP 500")
    result = runner.invoke(cli, ["seasons", "list", "1148580"])
    assert result.exit_code == 1
    assert "GameSheet error" in result.output


@patch("gamesheet_sdk.cli._list_seasons_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_seasons_csv_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_seasons(("501", "2024-2025"))
    result = runner.invoke(cli, ["seasons", "list", "1148580", "--format", "csv"])
    assert result.exit_code == 0, result.output
    lines = result.output.strip().splitlines()
    assert "title" in lines[0]
    assert "501" in lines[1]
    assert "2024-2025" in lines[1]


@patch("gamesheet_sdk.cli._list_seasons_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_seasons_yaml_format(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_seasons(("501", "2024-2025"))
    result = runner.invoke(cli, ["seasons", "list", "1148580", "--format", "yaml"])
    assert result.exit_code == 0, result.output
    data = yaml.safe_load(result.output)
    assert data == [{"id": "501", "title": "2024-2025", "league_id": "1148580"}]


@patch("gamesheet_sdk.cli._list_seasons_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_seasons_output_to_file(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    mock_list.return_value = _stub_seasons(("501", "2024-2025"))
    output_file = tmp_path / "seasons.json"
    result = runner.invoke(
        cli,
        ["seasons", "list", "1148580", "--format", "json", "--output", str(output_file)],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(output_file.read_text())
    assert data == [{"id": "501", "title": "2024-2025", "league_id": "1148580"}]


@patch("gamesheet_sdk.cli._list_seasons_action")
@patch("gamesheet_sdk.cli.load_refresh_token", return_value="refresh-tok")
@patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok")
def test_list_seasons_columns_filter(
    _mock_load_access: MagicMock,
    _mock_load_refresh: MagicMock,
    mock_list: MagicMock,
    runner: CliRunner,
) -> None:
    mock_list.return_value = _stub_seasons(("501", "2024-2025"))
    result = runner.invoke(
        cli,
        ["seasons", "list", "1148580", "--format", "csv", "--columns", "id,title"],
    )
    assert result.exit_code == 0, result.output
    lines = result.output.strip().splitlines()
    assert lines[0] == "id,title"
    assert lines[1] == "501,2024-2025"


def test_seasons_group_has_help_option(runner: CliRunner) -> None:
    """The seasons group should accept -h and --help."""
    result_short = runner.invoke(cli, ["seasons", "-h"])
    assert result_short.exit_code == 0
    assert "seasons" in result_short.output.lower()

    result_long = runner.invoke(cli, ["seasons", "--help"])
    assert result_long.exit_code == 0
    assert "seasons" in result_long.output.lower()


def test_seasons_list_alias_works(runner: CliRunner) -> None:
    """The 'ls' alias should invoke the list command."""
    with (
        patch("gamesheet_sdk.cli._list_seasons_action") as mock_list,
        patch(
            "gamesheet_sdk.cli.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["seasons", "ls", "1148580"])
        assert result.exit_code == 0
        mock_list.assert_called_once()


def test_seasons_missing_league_id_shows_error(runner: CliRunner) -> None:
    """Calling 'seasons list' without a league ID should show an error."""
    result = runner.invoke(cli, ["seasons", "list"])
    assert result.exit_code == 2  # Usage error
    assert "LEAGUE_ID" in result.output or "Missing argument" in result.output
