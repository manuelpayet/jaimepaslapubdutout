"""
Session converter for converting raw sessions to structured format.
"""

import sqlite3
from pathlib import Path
import logging
from typing import Optional

from src.classifier.session_reader import SessionReader
from src.common.storage import StorageManager

logger = logging.getLogger(__name__)


class SessionConverter:
    """
    Converts raw sessions (optimized for fast write) to structured format (optimized for read/annotation).
    Uses SQLite for efficient querying and annotation.
    """

    def __init__(self, input_dir: str = "data/raw", output_dir: str = "data/processed"):
        """
        Initialize session converter.

        Args:
            input_dir: Directory containing raw sessions
            output_dir: Directory for processed sessions
        """
        self.storage = StorageManager(raw_dir=input_dir, processed_dir=output_dir)
        logger.info(f"SessionConverter initialized")

    def convert_session(self, session_id: str, force: bool = False) -> str:
        """
        Convert a raw session to structured SQLite format.

        Args:
            session_id: Session identifier
            force: Force conversion even if processed session already exists

        Returns:
            Path to the created .db file

        Raises:
            FileNotFoundError: If raw session doesn't exist
        """
        # Check if raw session exists
        raw_session_path = self.storage.get_raw_session_path(session_id)
        if not raw_session_path.exists():
            raise FileNotFoundError(f"Raw session not found: {session_id}")

        # Check if processed session already exists
        processed_path = self.storage.get_processed_session_path(session_id)
        if processed_path.exists() and not force:
            logger.info(f"Session already converted: {session_id}")
            return str(processed_path)

        logger.info(f"Converting session: {session_id}")

        # Load raw session
        reader = SessionReader(str(raw_session_path))
        metadata = reader.load_metadata()

        # Create SQLite database
        self._create_database(processed_path, metadata, reader)

        logger.info(f"Session converted successfully: {processed_path}")
        return str(processed_path)

    def _create_database(
        self, db_path: Path, metadata: dict, reader: SessionReader
    ) -> None:
        """
        Create SQLite database with session data.

        Args:
            db_path: Path to database file
            metadata: Session metadata
            reader: SessionReader instance
        """
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing database if present
        if db_path.exists():
            db_path.unlink()

        # Create connection
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        try:
            # Create schema
            self._create_schema(cursor)

            # Insert metadata
            self._insert_metadata(cursor, metadata)

            # Insert blocks
            block_count = 0
            for block in reader.iter_blocks():
                self._insert_block(cursor, block)
                block_count += 1

            conn.commit()
            logger.info(f"Inserted {block_count} blocks into database")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating database: {e}")
            raise
        finally:
            conn.close()

    def _create_schema(self, cursor: sqlite3.Cursor) -> None:
        """
        Create database schema.

        Args:
            cursor: SQLite cursor
        """
        # Metadata table
        cursor.execute("""
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Blocks table
        cursor.execute("""
            CREATE TABLE blocks (
                block_number INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                audio_path TEXT NOT NULL,
                transcription TEXT,
                category TEXT DEFAULT 'A classifier'
            )
        """)

        # Index for efficient category filtering
        cursor.execute("""
            CREATE INDEX idx_category ON blocks(category)
        """)

        logger.debug("Database schema created")

    def _insert_metadata(self, cursor: sqlite3.Cursor, metadata: dict) -> None:
        """
        Insert metadata into database.

        Args:
            cursor: SQLite cursor
            metadata: Metadata dictionary
        """
        for key, value in metadata.items():
            cursor.execute(
                "INSERT INTO metadata (key, value) VALUES (?, ?)", (key, str(value))
            )

        logger.debug(f"Inserted {len(metadata)} metadata entries")

    def _insert_block(self, cursor: sqlite3.Cursor, block) -> None:
        """
        Insert a block into the database.

        Args:
            cursor: SQLite cursor
            block: Block object
        """
        cursor.execute(
            """
            INSERT INTO blocks (block_number, timestamp, audio_path, transcription, category)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                block.block_number,
                block.timestamp.isoformat(),
                block.audio_path,
                block.transcription,
                "A classifier",  # Default category
            ),
        )

    def list_unconverted_sessions(self) -> list:
        """
        List all raw sessions that haven't been converted yet.

        Returns:
            List of session IDs
        """
        raw_sessions = set(self.storage.list_raw_sessions())
        processed_sessions = set(self.storage.list_processed_sessions())

        unconverted = list(raw_sessions - processed_sessions)
        logger.info(f"Found {len(unconverted)} unconverted sessions")

        return sorted(unconverted)

    def convert_all_sessions(self, force: bool = False) -> list:
        """
        Convert all unconverted sessions.

        Args:
            force: Force conversion even if already processed

        Returns:
            List of converted session paths
        """
        if force:
            sessions = self.storage.list_raw_sessions()
        else:
            sessions = self.list_unconverted_sessions()

        converted = []
        for session_id in sessions:
            try:
                db_path = self.convert_session(session_id, force=force)
                converted.append(db_path)
            except Exception as e:
                logger.error(f"Failed to convert session {session_id}: {e}")

        logger.info(f"Converted {len(converted)}/{len(sessions)} sessions")
        return converted
