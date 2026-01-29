"""
Simple audio player for playback during annotation.
"""

import pygame
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AudioPlayer:
    """
    Simple audio player using pygame.mixer.
    Non-blocking playback for annotation interface.
    Works in headless environments (devcontainer).
    """

    def __init__(self):
        """Initialize pygame mixer with fallback for headless environments."""
        self._is_initialized = False
        self._current_file: Optional[Path] = None

        # Try to initialize with different audio drivers
        drivers_to_try = [
            None,  # Default driver
            "pulse",  # PulseAudio (common on Linux)
            "alsa",  # ALSA (Linux)
            "dummy",  # Dummy driver (no audio output but works)
        ]

        for driver in drivers_to_try:
            try:
                if driver:
                    # Set SDL audio driver environment variable
                    os.environ["SDL_AUDIODRIVER"] = driver
                    logger.debug(f"Trying audio driver: {driver}")

                # Initialize pygame
                pygame.mixer.quit()  # Quit any previous initialization
                pygame.mixer.init(frequency=16000, size=-16, channels=1, buffer=512)

                self._is_initialized = True
                driver_name = driver or pygame.mixer.get_init()
                logger.info(
                    f"AudioPlayer initialized successfully with driver: {driver_name}"
                )
                break

            except Exception as e:
                logger.debug(f"Failed to initialize with driver {driver}: {e}")
                continue

        if not self._is_initialized:
            logger.error(
                "Failed to initialize AudioPlayer with any driver. Audio playback disabled."
            )
            logger.info(
                "Note: In devcontainer, this is expected. Install pulseaudio or use dummy driver."
            )

    def play(self, audio_path: str) -> bool:
        """
        Play an audio file.

        Args:
            audio_path: Path to WAV file

        Returns:
            True if playback started successfully
        """
        if not self._is_initialized:
            logger.warning("AudioPlayer not initialized")
            return False

        try:
            path = Path(audio_path)
            if not path.exists():
                logger.error(f"Audio file not found: {audio_path}")
                return False

            # Stop any current playback
            self.stop()

            # Load and play
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play()
            self._current_file = path

            logger.debug(f"Playing: {audio_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            return False

    def stop(self) -> None:
        """Stop current playback."""
        if self._is_initialized and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            logger.debug("Playback stopped")

    def pause(self) -> None:
        """Pause current playback."""
        if self._is_initialized and pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            logger.debug("Playback paused")

    def unpause(self) -> None:
        """Resume paused playback."""
        if self._is_initialized:
            pygame.mixer.music.unpause()
            logger.debug("Playback resumed")

    def is_playing(self) -> bool:
        """
        Check if audio is currently playing.

        Returns:
            True if playing
        """
        if not self._is_initialized:
            return False
        return pygame.mixer.music.get_busy()

    def get_current_file(self) -> Optional[Path]:
        """
        Get currently loaded file.

        Returns:
            Path to current file or None
        """
        return self._current_file

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._is_initialized:
            self.stop()
            pygame.mixer.quit()
            logger.info("AudioPlayer cleaned up")
