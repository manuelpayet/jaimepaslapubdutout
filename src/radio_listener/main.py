"""
Main entry point for the radio listener module.
"""

import argparse
import logging
import signal
import sys
from datetime import datetime
from typing import Optional

from src.common.config import ConfigLoader
from src.common.storage import StorageManager
from src.radio_listener.audio_capture import AudioCapture
from src.radio_listener.transcriber import Transcriber
from src.radio_listener.block_recorder import BlockRecorder
from src.radio_listener.console_display import ConsoleDisplay

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("radio_listener.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class RadioListener:
    """
    Main orchestrator for the radio listener module.
    Manages the complete lifecycle: capture -> transcribe -> record.
    """

    def __init__(self, config):
        """
        Initialize radio listener with configuration.

        Args:
            config: RadioListenerConfig instance
        """
        self.config = config

        # Generate session ID if not provided
        if not config.session_id:
            storage = StorageManager(raw_dir=config.output_dir)
            config.session_id = storage.generate_session_id()

        # Initialize components
        self.audio_capture = AudioCapture(
            stream_url=config.stream_url, sample_rate=config.sample_rate
        )

        self.transcriber = Transcriber(
            model_name=config.whisper_model, language=config.whisper_language
        )

        self.block_recorder = BlockRecorder(
            output_dir=config.output_dir,
            session_id=config.session_id,
            sample_rate=config.sample_rate,
        )

        self.display = ConsoleDisplay()

        # State
        self._running = False
        self._block_count = 0

        logger.info(f"RadioListener initialized for session: {config.session_id}")

    def start(self) -> None:
        """Start the radio listener."""
        logger.info("Starting radio listener")

        try:
            # Initialize display
            self.display.initialize(self.config.session_id)
            self.display.show_info("Starting audio capture...")

            # Start audio capture
            self.audio_capture.start_capture()

            # Update metadata
            self.block_recorder.update_metadata(
                stream_url=self.config.stream_url,
                block_duration=self.config.block_duration,
                whisper_model=self.config.whisper_model,
            )

            self.display.show_info("Audio capture started, beginning transcription...")

            # Start processing loop
            self._running = True
            self._process_loop()

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            self.display.show_info("Stopping...")
        except Exception as e:
            logger.error(f"Error during execution: {e}", exc_info=True)
            self.display.show_error(str(e))
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the radio listener gracefully."""
        logger.info("Stopping radio listener")

        self._running = False

        # Stop audio capture
        if self.audio_capture.is_alive():
            self.audio_capture.stop_capture()

        # Finalize recording
        self.block_recorder.finalize_session()

        self.display.show_info(f"Session saved: {self.config.session_id}")
        self.display.show_info(f"Total blocks recorded: {self._block_count}")

        logger.info("Radio listener stopped")

    def _process_loop(self) -> None:
        """
        Main processing loop:
        1. Capture N seconds of audio
        2. Transcribe
        3. Record
        4. Display
        5. Repeat
        """
        while self._running and self.audio_capture.is_alive():
            try:
                # 1. Capture audio chunk
                logger.debug(f"Reading {self.config.block_duration}s audio chunk")
                audio_data = self.audio_capture.read_chunk(self.config.block_duration)

                if audio_data is None:
                    logger.warning("No audio data received")
                    continue

                # 2. Transcribe
                logger.debug("Transcribing audio")
                transcription = self.transcriber.transcribe(audio_data)

                # 3. Record
                timestamp = datetime.now()
                self.block_recorder.save_block(
                    audio_data=audio_data,
                    transcription=transcription,
                    block_number=self._block_count,
                    timestamp=timestamp,
                    block_duration=self.config.block_duration,
                )

                # 4. Display
                stats = self.audio_capture.get_stats()
                self.display.update_status(
                    current_block=self._block_count,
                    transcription=transcription.text,
                    stats=stats,
                )

                logger.info(
                    f"Block {self._block_count} processed: {len(transcription.text)} chars"
                )

                self._block_count += 1

            except Exception as e:
                logger.error(
                    f"Error processing block {self._block_count}: {e}", exc_info=True
                )
                self.display.show_error(f"Error processing block: {e}")
                # Continue processing despite errors


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Radio Listener - Real-time audio transcription from RTSP stream"
    )

    parser.add_argument(
        "--stream-url", required=True, help="Audio stream URL (RTSP, HTTP, HLS, etc.)"
    )
    parser.add_argument(
        "--rtsp-url", dest="stream_url", help="(Deprecated) Use --stream-url instead"
    )

    parser.add_argument(
        "--block-duration",
        type=int,
        default=10,
        help="Duration of each audio block in seconds (default: 10)",
    )

    parser.add_argument(
        "--whisper-model",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        help="Whisper model size (default: base)",
    )

    parser.add_argument(
        "--language", default="fr", help="Language code for transcription (default: fr)"
    )

    parser.add_argument(
        "--output-dir",
        default="data/raw",
        help="Output directory for recordings (default: data/raw)",
    )

    parser.add_argument(
        "--session-id", help="Custom session ID (auto-generated if not provided)"
    )

    parser.add_argument("--config", help="Path to YAML config file")

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Load configuration
    config = ConfigLoader.load_radio_listener_config(
        config_file=args.config,
        stream_url=args.stream_url,
        block_duration=args.block_duration,
        whisper_model=args.whisper_model,
        whisper_language=args.language,
        output_dir=args.output_dir,
        session_id=args.session_id,
    )

    # Create listener
    listener = RadioListener(config)

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        listener.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start listener
    listener.start()


if __name__ == "__main__":
    main()
