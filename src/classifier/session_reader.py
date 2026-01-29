"""
Session reader for loading raw sessions.
"""

from pathlib import Path
from typing import Iterator, Optional
from datetime import datetime
import json
import logging

from src.common.models import Block

logger = logging.getLogger(__name__)


class SessionReader:
    """
    Reads raw sessions from disk.
    Provides access to session metadata and blocks.
    """

    def __init__(self, session_path: str):
        """
        Initialize session reader.

        Args:
            session_path: Path to raw session directory (e.g., data/raw/session_XXX/)
        """
        self.session_path = Path(session_path)
        self.blocks_dir = self.session_path / "blocks"
        self.metadata_file = self.session_path / "metadata.json"

        if not self.session_path.exists():
            raise FileNotFoundError(f"Session directory not found: {session_path}")

        if not self.blocks_dir.exists():
            raise FileNotFoundError(f"Blocks directory not found: {self.blocks_dir}")

        logger.info(f"SessionReader initialized for: {self.session_path.name}")

    def load_metadata(self) -> dict:
        """
        Load session metadata.

        Returns:
            Dictionary with session metadata

        Raises:
            FileNotFoundError: If metadata file doesn't exist
        """
        if not self.metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_file}")

        with open(self.metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        logger.debug(f"Loaded metadata for session: {metadata.get('session_id')}")
        return metadata

    def iter_blocks(self) -> Iterator[Block]:
        """
        Iterate over all blocks in the session.

        Yields:
            Block objects with audio_path, transcription, timestamp, etc.
        """
        # Get all WAV files and sort them
        wav_files = sorted(self.blocks_dir.glob("block_*.wav"))

        logger.info(f"Found {len(wav_files)} blocks in session")

        for wav_file in wav_files:
            # Extract block number from filename (e.g., block_0042.wav -> 42)
            block_number = int(wav_file.stem.split("_")[1])

            # Load transcription from corresponding .txt file
            txt_file = wav_file.with_suffix(".txt")
            transcription = self._load_transcription(txt_file)

            # Extract timestamp from transcription file
            timestamp = self._extract_timestamp(txt_file)

            # Create Block object
            block = Block(
                block_number=block_number,
                timestamp=timestamp,
                audio_path=str(wav_file),
                transcription=transcription,
                category="A classifier",  # Default category
            )

            yield block

    def get_block(self, block_number: int) -> Optional[Block]:
        """
        Get a specific block by number.

        Args:
            block_number: Block number to retrieve

        Returns:
            Block object or None if not found
        """
        wav_file = self.blocks_dir / f"block_{block_number:04d}.wav"

        if not wav_file.exists():
            logger.warning(f"Block {block_number} not found")
            return None

        txt_file = wav_file.with_suffix(".txt")
        transcription = self._load_transcription(txt_file)
        timestamp = self._extract_timestamp(txt_file)

        return Block(
            block_number=block_number,
            timestamp=timestamp,
            audio_path=str(wav_file),
            transcription=transcription,
            category="A classifier",
        )

    def get_block_count(self) -> int:
        """
        Get the total number of blocks in the session.

        Returns:
            Number of blocks
        """
        return len(list(self.blocks_dir.glob("block_*.wav")))

    def _load_transcription(self, txt_file: Path) -> str:
        """
        Load transcription text from file.

        Args:
            txt_file: Path to transcription text file

        Returns:
            Transcription text
        """
        if not txt_file.exists():
            logger.warning(f"Transcription file not found: {txt_file}")
            return ""

        with open(txt_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find the "## Full Transcription" section
        transcription_lines = []
        in_transcription = False

        for line in lines:
            if line.strip() == "## Full Transcription":
                in_transcription = True
                continue
            elif line.strip().startswith("##"):
                in_transcription = False
            elif in_transcription and line.strip():
                transcription_lines.append(line.strip())

        return " ".join(transcription_lines)

    def _extract_timestamp(self, txt_file: Path) -> datetime:
        """
        Extract timestamp from transcription file.

        Args:
            txt_file: Path to transcription text file

        Returns:
            Datetime object
        """
        if not txt_file.exists():
            return datetime.now()

        with open(txt_file, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()

        # Extract timestamp from first line: "# Timestamp: 2026-01-28T14:30:00"
        if first_line.startswith("# Timestamp:"):
            timestamp_str = first_line.split(":", 1)[1].strip()
            try:
                return datetime.fromisoformat(timestamp_str)
            except ValueError:
                logger.warning(f"Failed to parse timestamp: {timestamp_str}")

        return datetime.now()
