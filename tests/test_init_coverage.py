# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for __init__.py version handling."""

from __future__ import annotations


def test_version_fallback_when_package_not_found() -> None:
    """Test that __version__ falls back to '0+unknown' when package not found."""
    # Need to reload the module to trigger the try/except block
    import sys
    from unittest.mock import patch

    import gamesheet_sdk

    # Save the original version
    original_version = gamesheet_sdk.__version__

    # Remove the module from sys.modules to force reimport
    if "gamesheet_sdk" in sys.modules:
        del sys.modules["gamesheet_sdk"]

    # Mock the version() function to raise PackageNotFoundError
    with patch("importlib.metadata.version") as mock_version:
        from importlib.metadata import PackageNotFoundError

        mock_version.side_effect = PackageNotFoundError("gamesheet-sdk-py")

        # Re-import the module, which will trigger the except block
        import gamesheet_sdk as gs

        # The fallback version should be set
        assert gs.__version__ == "0+unknown"

    # Clean up: remove from sys.modules again
    if "gamesheet_sdk" in sys.modules:
        del sys.modules["gamesheet_sdk"]

    # Re-import normally to restore state
    import gamesheet_sdk

    # Verify it's back to normal
    assert gamesheet_sdk.__version__ == original_version
