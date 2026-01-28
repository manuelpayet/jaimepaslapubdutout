"""
Tests for console display.
"""

import pytest
import time
from io import StringIO
import sys

from src.radio_listener.console_display import ConsoleDisplay


class TestConsoleDisplay:
    """Tests for ConsoleDisplay."""

    @pytest.fixture
    def display(self):
        """Create a ConsoleDisplay instance."""
        return ConsoleDisplay(refresh_rate=0.1)

    def test_initialization(self, display):
        """Test display initialization."""
        assert display.refresh_rate == 0.1
        assert display._last_update == 0.0
        assert display._initialized is False

    def test_initialize(self, display):
        """Test initializing the display."""
        display.initialize("test_session_123")

        assert display._session_id == "test_session_123"
        assert display._initialized is True

    def test_update_status_throttling(self, display):
        """Test that updates are throttled."""
        display.initialize("test_session")

        # First update should go through
        display.update_status(0, "First", {})
        first_update_time = display._last_update

        # Immediate second update should be throttled
        display.update_status(1, "Second", {})
        assert display._last_update == first_update_time

        # After refresh_rate, update should go through
        time.sleep(0.15)
        display.update_status(2, "Third", {})
        assert display._last_update > first_update_time

    def test_format_bytes(self, display):
        """Test byte formatting."""
        assert display._format_bytes(512) == "512.0 B"
        assert display._format_bytes(1024) == "1.0 KB"
        assert display._format_bytes(1024 * 1024) == "1.0 MB"
        assert display._format_bytes(1024 * 1024 * 1024) == "1.0 GB"

    def test_wrap_text_short(self, display):
        """Test wrapping short text."""
        text = "Hello world"
        lines = display._wrap_text(text, 50)

        assert len(lines) == 1
        assert lines[0] == "Hello world"

    def test_wrap_text_long(self, display):
        """Test wrapping long text."""
        text = "This is a very long text that should be wrapped into multiple lines"
        lines = display._wrap_text(text, 20)

        assert len(lines) > 1
        for line in lines:
            assert len(line) <= 20

    def test_wrap_text_very_long_word(self, display):
        """Test wrapping text with very long word."""
        text = "verylongwordthatcannotbewrapped"
        lines = display._wrap_text(text, 10)

        assert len(lines) >= 1
        assert lines[0] == text[:10]

    def test_show_error(self, display, capsys):
        """Test showing error message."""
        display.show_error("Test error message")

        captured = capsys.readouterr()
        assert "ERROR" in captured.err
        assert "Test error message" in captured.err

    def test_show_info(self, display, capsys):
        """Test showing info message."""
        display.show_info("Test info message")

        captured = capsys.readouterr()
        assert "INFO" in captured.out
        assert "Test info message" in captured.out

    def test_color_methods(self, display):
        """Test color formatting methods."""
        red_text = display._red("error")
        assert "error" in red_text
        assert "\033[" in red_text  # ANSI escape code

        blue_text = display._blue("info")
        assert "info" in blue_text
        assert "\033[" in blue_text

        green_text = display._green("success")
        assert "success" in green_text
        assert "\033[" in green_text
