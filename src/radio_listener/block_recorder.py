"""
Block recorder for saving audio and transcriptions.
"""

from pathlib import Path
from datetime import datetime
import json
import numpy as np
import wave
import logging
from typing import Optional
from src.common.models import TranscriptionResult

logger = logging.getLogger(__name__)


class BlockRecorder:
    """
    Records audio blocks and transcriptions to disk.
    Format optimized for fast writing (priority: performance).
    """

    def __init__(self, output_dir: str, session_id: str, sample_rate: int = 16000):
        """
        Initialize block recorder.

        Args:
            output_dir: Base output directory (e.g., 'data/raw')
            session_id: Unique session identifier
            sample_rate: Audio sample rate in Hz
        """
        self.output_dir = Path(output_dir)
        self.session_id = session_id
        self.sample_rate = sample_rate

        # Session directory structure
        self.session_dir = self.output_dir / session_id
        self.blocks_dir = self.session_dir / "blocks"

        # Create directories
        self.blocks_dir.mkdir(parents=True, exist_ok=True)

        # Metadata
        self.metadata = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "sample_rate": sample_rate,
            "total_blocks": 0,
        }

        logger.info(f"BlockRecorder initialized for session: {session_id}")

    def save_block(
        self,
        audio_data: np.ndarray,
        transcription: TranscriptionResult,
        block_number: int,
        timestamp: datetime,
        block_duration: int,
    ) -> str:
        """
        Save an audio block with its transcription.

        Args:
            audio_data: Numpy array with audio samples (float32)
            transcription: Transcription result
            block_number: Sequential block number
            timestamp: Timestamp when block was captured
            block_duration: Duration of the block in seconds

        Returns:
            Path to the saved audio file
        """
        try:
            # Generate filenames with zero-padded block number
            block_id = f"block_{block_number:04d}"
            audio_path = self.blocks_dir / f"{block_id}.wav"
            text_path = self.blocks_dir / f"{block_id}.txt"

            # Save audio as WAV file
            self._save_wav(audio_path, audio_data)

            # Save transcription as text file
            self._save_transcription(text_path, transcription, timestamp)

            # Update metadata
            self.metadata["total_blocks"] = max(
                self.metadata["total_blocks"], block_number + 1
            )

            logger.debug(f"Block {block_number} saved: {audio_path}")

            return str(audio_path)

        except Exception as e:
            logger.error(f"Failed to save block {block_number}: {e}")
            raise

    def _save_wav(self, path: Path, audio_data: np.ndarray) -> None:
        """
        Save audio data as WAV file.

        Args:
            path: Output file path
            audio_data: Audio samples (float32, normalized to [-1, 1])
        """
        # Convert float32 to int16 for WAV format
        audio_int16 = (audio_data * 32767).astype(np.int16)

        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

    def _save_transcription(
        self, path: Path, transcription: TranscriptionResult, timestamp: datetime
    ) -> None:
        """
        Save transcription to text file.

        Args:
            path: Output file path
            transcription: Transcription result
            timestamp: Block timestamp
        """
        with open(path, "w", encoding="utf-8") as f:
            # Write metadata header
            f.write(f"# Timestamp: {timestamp.isoformat()}\n")
            f.write(f"# Language: {transcription.language}\n")
            f.write(f"# Segments: {len(transcription.segments)}\n")
            f.write("\n")

            # Write full transcription
            f.write("## Full Transcription\n")
            f.write(transcription.text)
            f.write("\n\n")

            # Write segments with timestamps
            if transcription.segments:
                f.write("## Segments\n")
                for segment in transcription.segments:
                    f.write(
                        f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}\n"
                    )

    def update_metadata(self, **kwargs) -> None:
        """
        Update session metadata.

        Args:
            **kwargs: Metadata fields to update
        """
        self.metadata.update(kwargs)

    def finalize_session(self) -> None:
        """
        Finalize the session by writing final metadata.
        Call this when the recording session is complete.
        """
        logger.info(f"Finalizing session: {self.session_id}")

        # Set end time
        self.metadata["end_time"] = datetime.now().isoformat()

        # Write metadata to file
        metadata_path = self.session_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2)

        logger.info(
            f"Session finalized: {self.metadata['total_blocks']} blocks recorded"
        )

    def get_session_dir(self) -> Path:
        """
        Get the session directory path.

        Returns:
            Path to session directory
        """
        return self.session_dir
