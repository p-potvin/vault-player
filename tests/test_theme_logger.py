import sys
import io
import pytest
from agents.theme_logger import VaultLogger

def test_log_valid_token(monkeypatch):
    """Test that a valid token applies the correct ANSI prefix and suffix."""
    mock_stdout = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', mock_stdout)

    result = VaultLogger.log("Test message", "vault.gold")

    output = mock_stdout.getvalue()
    assert result is True
    assert VaultLogger.THEME_TOKENS["vault.gold"] in output
    assert VaultLogger.THEME_TOKENS["reset"] in output
    assert "Test message" in output

def test_log_invalid_token(monkeypatch):
    """Test that an unrecognized token falls back to the reset ANSI sequence."""
    mock_stdout = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', mock_stdout)

    result = VaultLogger.log("Fallback message", "non.existent.token")

    output = mock_stdout.getvalue()
    assert result is True
    # The prefix should be the reset sequence since it wasn't found
    assert output.startswith(VaultLogger.THEME_TOKENS["reset"])
    assert "Fallback message" in output

def test_log_io_error(monkeypatch):
    """Test that an IOError is caught, logged to stderr, and handled without crashing."""

    class BrokenStdout:
        def write(self, text):
            raise IOError("Broken pipe")
        def flush(self):
            pass

    monkeypatch.setattr(sys, 'stdout', BrokenStdout())
    mock_stderr = io.StringIO()
    monkeypatch.setattr(sys, 'stderr', mock_stderr)

    result = VaultLogger.log("This will fail")

    assert result is False
    assert "[ThemeLogger Error]" in mock_stderr.getvalue()
    assert "Broken pipe" in mock_stderr.getvalue()
