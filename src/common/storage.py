"""
Storage management for sessions.
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import json
import shutil


class StorageManager:
    """Centralized storage management for raw and processed sessions."""

    def __init__(
        self, raw_dir: str = "data/raw", processed_dir: str = "data/processed"
    ):
        """
        Initialize storage manager.

        Args:
            raw_dir: Directory for raw session data
            processed_dir: Directory for processed session data
        """
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)

        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def list_raw_sessions(self) -> List[str]:
        """
        List all raw sessions.

        Returns:
            List of session IDs (directory names)
        """
        sessions = []
        for path in self.raw_dir.iterdir():
            if path.is_dir() and (path / "metadata.json").exists():
                sessions.append(path.name)
        return sorted(sessions)

    def list_processed_sessions(self) -> List[str]:
        """
        List all processed sessions.

        Returns:
            List of session IDs (database file names without extension)
        """
        sessions = []
        for path in self.processed_dir.glob("*.db"):
            sessions.append(path.stem)
        return sorted(sessions)

    def get_raw_session_path(self, session_id: str) -> Path:
        """Get path to raw session directory."""
        return self.raw_dir / session_id

    def get_processed_session_path(self, session_id: str) -> Path:
        """Get path to processed session database."""
        return self.processed_dir / f"{session_id}.db"

    def session_exists(self, session_id: str, processed: bool = False) -> bool:
        """
        Check if a session exists.

        Args:
            session_id: Session identifier
            processed: Check processed sessions if True, raw if False

        Returns:
            True if session exists
        """
        if processed:
            return self.get_processed_session_path(session_id).exists()
        else:
            return self.get_raw_session_path(session_id).exists()

    def get_session_metadata(self, session_id: str) -> Optional[dict]:
        """
        Load metadata for a raw session.

        Args:
            session_id: Session identifier

        Returns:
            Metadata dictionary or None if not found
        """
        metadata_path = self.get_raw_session_path(session_id) / "metadata.json"
        if not metadata_path.exists():
            return None

        with open(metadata_path, "r") as f:
            return json.load(f)

    def cleanup_old_sessions(
        self, days: int = 30, processed_only: bool = False
    ) -> List[str]:
        """
        Delete sessions older than specified days.

        Args:
            days: Delete sessions older than this many days
            processed_only: Only delete processed sessions if True

        Returns:
            List of deleted session IDs
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted = []

        # Clean up raw sessions
        if not processed_only:
            for session_id in self.list_raw_sessions():
                metadata = self.get_session_metadata(session_id)
                if metadata and "start_time" in metadata:
                    start_time = datetime.fromisoformat(metadata["start_time"])
                    if start_time < cutoff_date:
                        session_path = self.get_raw_session_path(session_id)
                        shutil.rmtree(session_path)
                        deleted.append(session_id)

        # Clean up processed sessions
        for session_id in self.list_processed_sessions():
            db_path = self.get_processed_session_path(session_id)
            mtime = datetime.fromtimestamp(db_path.stat().st_mtime)
            if mtime < cutoff_date:
                db_path.unlink()
                deleted.append(f"{session_id} (processed)")

        return deleted

    def delete_session(self, session_id: str, processed: bool = False) -> bool:
        """
        Delete a specific session.

        Args:
            session_id: Session identifier
            processed: Delete processed session if True, raw if False

        Returns:
            True if session was deleted
        """
        if processed:
            path = self.get_processed_session_path(session_id)
            if path.exists():
                path.unlink()
                return True
        else:
            path = self.get_raw_session_path(session_id)
            if path.exists():
                shutil.rmtree(path)
                return True
        return False

    def generate_session_id(self) -> str:
        """
        Generate a unique session ID based on timestamp.

        Returns:
            Session ID string (e.g., "session_2026-01-28_14-30-00")
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"session_{timestamp}"
