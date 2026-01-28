"""
Console display with minimal CPU usage.
"""

import sys
import time
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ConsoleDisplay:
    """
    Minimal console display for radio listener.
    Uses ANSI escape codes for efficient updates.
    Throttled to minimize CPU usage.
    """

    def __init__(self, refresh_rate: float = 0.5):
        """
        Initialize console display.

        Args:
            refresh_rate: Minimum time between updates in seconds
        """
        self.refresh_rate = refresh_rate
        self._last_update = 0.0
        self._initialized = False

        # Display state
        self._session_id: Optional[str] = None
        self._current_block = 0
        self._transcription = ""
        self._stats = {}

    def initialize(self, session_id: str) -> None:
        """
        Initialize the display.

        Args:
            session_id: Session identifier to display
        """
        self._session_id = session_id
        self._initialized = True
        self._clear_screen()
        self._draw_header()

    def update_status(
        self, current_block: int, transcription: str, stats: dict
    ) -> None:
        """
        Update the display with new information.

        Args:
            current_block: Current block number
            transcription: Latest transcription text
            stats: Statistics dictionary (cpu, ram, etc.)
        """
        # Throttle updates
        now = time.time()
        if now - self._last_update < self.refresh_rate:
            return

        self._current_block = current_block
        self._transcription = transcription
        self._stats = stats

        self._redraw()
        self._last_update = now

    def show_error(self, error: str) -> None:
        """
        Display an error message.

        Args:
            error: Error message
        """
        print(f"\n{self._red('ERROR')}: {error}", file=sys.stderr)

    def show_info(self, message: str) -> None:
        """
        Display an info message.

        Args:
            message: Info message
        """
        print(f"\n{self._blue('INFO')}: {message}")

    def clear(self) -> None:
        """Clear the display."""
        self._clear_screen()

    def _redraw(self) -> None:
        """Redraw the entire display."""
        if not self._initialized:
            return

        # Move cursor to top
        self._move_cursor_home()

        # Draw header
        self._draw_header()

        # Draw status
        self._draw_status()

        # Draw transcription
        self._draw_transcription()

        # Flush output
        sys.stdout.flush()

    def _draw_header(self) -> None:
        """Draw the header section."""
        header = f" Radio Listener - {self._session_id or 'N/A'} "
        width = 60
        border = "═" * width

        print(f"╔{border}╗")
        print(f"║{header:^{width}}║")
        print(f"╠{border}╣")

    def _draw_status(self) -> None:
        """Draw the status section."""
        width = 60

        # Block info
        block_info = f" Block: {self._current_block:04d}"
        print(f"║{block_info:<{width}}║")

        # Stats
        if self._stats:
            bytes_read = self._stats.get("bytes_read", 0)
            buffer_size = self._stats.get("buffer_size", 0)
            errors = self._stats.get("errors", 0)

            stats_line = f" Bytes: {self._format_bytes(bytes_read)} | Buffer: {buffer_size} | Errors: {errors}"
            print(f"║{stats_line:<{width}}║")

        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_line = f" Time: {timestamp}"
        print(f"║{time_line:<{width}}║")

        border = "─" * width
        print(f"╠{border}╣")

    def _draw_transcription(self) -> None:
        """Draw the transcription section."""
        width = 60

        print(f"║ {'Transcription:':<{width - 1}}║")

        # Wrap transcription text
        if self._transcription:
            lines = self._wrap_text(self._transcription, width - 4)
            for line in lines[:10]:  # Limit to 10 lines
                print(f"║ {line:<{width - 1}}║")
        else:
            print(f"║ {'(waiting for audio...)':<{width - 1}}║")

        border = "═" * width
        print(f"╚{border}╝")

    def _wrap_text(self, text: str, width: int) -> list:
        """
        Wrap text to specified width.

        Args:
            text: Text to wrap
            width: Maximum line width

        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    # Word is too long, split it
                    lines.append(word[:width])
                    current_line = []
                    current_length = 0
            else:
                current_line.append(word)
                current_length += word_length

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _format_bytes(self, bytes_count: int) -> str:
        """
        Format byte count in human-readable format.

        Args:
            bytes_count: Number of bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"

    def _clear_screen(self) -> None:
        """Clear the terminal screen."""
        print("\033[2J", end="")

    def _move_cursor_home(self) -> None:
        """Move cursor to top-left."""
        print("\033[H", end="")

    def _red(self, text: str) -> str:
        """Color text red."""
        return f"\033[91m{text}\033[0m"

    def _blue(self, text: str) -> str:
        """Color text blue."""
        return f"\033[94m{text}\033[0m"

    def _green(self, text: str) -> str:
        """Color text green."""
        return f"\033[92m{text}\033[0m"
