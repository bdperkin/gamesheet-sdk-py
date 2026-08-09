# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Read pip configuration (config files + environment variables) for HTTP settings."""

from __future__ import annotations

import configparser
from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
import ssl
import sys
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_SYSTEM_CA_PATHS = (
    "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",
    "/etc/pki/tls/certs/ca-bundle.crt",
    "/etc/ssl/certs/ca-certificates.crt",
)


@dataclass(frozen=True)
class PipConfig:
    """Resolved pip configuration for HTTP requests."""

    index_url: str | None = None
    extra_index_urls: tuple[str, ...] = field(default_factory=tuple)
    trusted_hosts: tuple[str, ...] = field(default_factory=tuple)
    cert: str | None = None
    client_cert: str | None = None


def _pip_config_paths() -> list[Path]:
    """Return pip config file paths in precedence order (lowest first).

    Returns:
        list[Path]: List of paths to check, lowest precedence first.
    """
    paths: list[Path] = []

    paths.append(Path("/etc/pip.conf"))

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(Path(appdata) / "pip" / "pip.ini")
    else:
        paths.append(Path.home() / ".pip" / "pip.conf")
        xdg_config = os.environ.get("XDG_CONFIG_HOME", "")
        if xdg_config:
            paths.append(Path(xdg_config) / "pip" / "pip.conf")
        else:
            paths.append(Path.home() / ".config" / "pip" / "pip.conf")

    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        paths.append(Path(venv) / "pip.conf")

    explicit = os.environ.get("PIP_CONFIG_FILE")
    if explicit:
        paths.append(Path(explicit))

    return paths


def _split_multi_value(value: str) -> list[str]:
    """Split a pip config multi-value string (newline or space separated).

    Returns:
        list[str]: Non-empty stripped values.
    """
    parts = value.replace("\n", " ").split()
    return [p.strip() for p in parts if p.strip()]


def _read_config_files(paths: list[Path]) -> configparser.ConfigParser:
    """Read pip config files in precedence order (lowest first, later overrides).

    Returns:
        configparser.ConfigParser: Merged ConfigParser with all discovered settings.
    """
    parser = configparser.ConfigParser()
    for path in paths:
        if path.is_file():
            try:
                parser.read(str(path), encoding="utf-8")
                logger.debug("Read pip config from %s", path)
            except (configparser.Error, OSError) as exc:
                logger.debug("Skipping unreadable pip config %s: %s", path, exc)

    return parser


def _read_global_section(
    parser: configparser.ConfigParser,
) -> tuple[str | None, list[str], list[str], str | None, str | None]:
    """Extract pip settings from the [global] section of parsed config files.

    Args:
        parser (configparser.ConfigParser): Merged config parser with all discovered pip config files.

    Returns:
        tuple[str | None, list[str], list[str], str | None, str | None]: Tuple of (index_url,
            extra_index_urls, trusted_hosts, cert, client_cert).
    """
    if not parser.has_section("global"):
        return None, [], [], None, None

    index_url = parser.get("global", "index-url", fallback=None)
    extra_raw = parser.get("global", "extra-index-url", fallback=None)
    extra_index_urls = _split_multi_value(extra_raw) if extra_raw else []
    trusted_raw = parser.get("global", "trusted-host", fallback=None)
    trusted_hosts = _split_multi_value(trusted_raw) if trusted_raw else []
    cert = parser.get("global", "cert", fallback=None)
    client_cert = parser.get("global", "client-cert", fallback=None)
    return index_url, extra_index_urls, trusted_hosts, cert, client_cert


def load_pip_config() -> PipConfig:
    """Load pip configuration from config files and environment variables.

    Config files are read in standard pip precedence order (global → user → venv → explicit). Environment
    variables override file values.

    Returns:
        PipConfig: Resolved pip configuration.
    """
    paths = _pip_config_paths()
    parser = _read_config_files(paths)
    index_url, extra_index_urls, trusted_hosts, cert, client_cert = _read_global_section(parser)

    env_index = os.environ.get("PIP_INDEX_URL")
    if env_index:
        index_url = env_index

    env_extra = os.environ.get("PIP_EXTRA_INDEX_URL")
    if env_extra:
        extra_index_urls = _split_multi_value(env_extra)

    env_trusted = os.environ.get("PIP_TRUSTED_HOST")
    if env_trusted:
        trusted_hosts = _split_multi_value(env_trusted)

    env_cert = os.environ.get("PIP_CERT")
    if env_cert:
        cert = env_cert

    env_client_cert = os.environ.get("PIP_CLIENT_CERT")
    if env_client_cert:
        client_cert = env_client_cert

    if index_url:
        index_url = index_url.strip()

    config = PipConfig(
        index_url=index_url or None,
        extra_index_urls=tuple(extra_index_urls),
        trusted_hosts=tuple(trusted_hosts),
        cert=cert,
        client_cert=client_cert,
    )

    if config != PipConfig():
        logger.debug(
            "Loaded pip config: index_url=%s, extras=%d, trusted=%d, cert=%s, client_cert=%s",
            config.index_url,
            len(config.extra_index_urls),
            len(config.trusted_hosts),
            config.cert,
            config.client_cert,
        )

    return config


def _get_system_ca_bundle() -> str | bool:
    """Resolve the system CA bundle path.

    Returns:
        str | bool: Path to the system CA file, or True to use the default certifi bundle.
    """
    paths = ssl.get_default_verify_paths()
    if paths.cafile:
        return paths.cafile

    for ca_path in _SYSTEM_CA_PATHS:
        if Path(ca_path).is_file():
            return ca_path

    return True


def resolve_verify(url: str, config: PipConfig | None = None) -> str | bool:
    """Determine the ``verify`` parameter for a requests call.

    Mirrors pip's ``--trusted-host`` semantics: hosts listed in pip's ``trusted-host`` config skip certificate
    validation. This is intentional for enterprise environments with internal package indexes that use self-
    signed or private CA certificates. CodeQL flags the resulting ``verify=False`` as ``py/request-without-
    cert-validation``; dismiss those findings as false positives in the Security UI after merge.

    Args:
        url (str): The URL being requested.
        config (PipConfig | None): Pip configuration, or None for defaults.

    Returns:
        str | bool: False for trusted hosts, cert path if configured, or system CA bundle.
    """
    if config and config.trusted_hosts:
        hostname = urlparse(url).hostname or ""
        if hostname in config.trusted_hosts:
            return False

    if config and config.cert:
        return config.cert

    return _get_system_ca_bundle()
