"""
Tests for storage management.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta

from src.common.storage import StorageManager


class TestStorageManager:
    """Tests for StorageManager."""

    @pytest.fixture
    def storage_manager(self, tmp_path):
        """Create a StorageManager with temporary directories."""
        raw_dir = tmp_path / "raw"
        processed_dir = tmp_path / "processed"
        return StorageManager(raw_dir=str(raw_dir), processed_dir=str(processed_dir))

    def test_initialization(self, storage_manager, tmp_path):
        """Test that directories are created on initialization."""
        assert (tmp_path / "raw").exists()
        assert (tmp_path / "processed").exists()

    def test_generate_session_id(self, storage_manager):
        """Test session ID generation."""
        session_id = storage_manager.generate_session_id()

        assert session_id.startswith("session_")
        assert len(session_id) > 8  # Should contain timestamp

    def test_list_raw_sessions_empty(self, storage_manager):
        """Test listing raw sessions when none exist."""
        sessions = storage_manager.list_raw_sessions()
        assert sessions == []

    def test_list_raw_sessions(self, storage_manager):
        """Test listing raw sessions."""
        # Create some test sessions
        for i in range(3):
            session_dir = storage_manager.raw_dir / f"session_{i}"
            session_dir.mkdir()

            # Create metadata.json
            metadata = {"session_id": f"session_{i}"}
            with open(session_dir / "metadata.json", "w") as f:
                json.dump(metadata, f)

        sessions = storage_manager.list_raw_sessions()
        assert len(sessions) == 3
        assert "session_0" in sessions
        assert "session_1" in sessions
        assert "session_2" in sessions

    def test_list_processed_sessions_empty(self, storage_manager):
        """Test listing processed sessions when none exist."""
        sessions = storage_manager.list_processed_sessions()
        assert sessions == []

    def test_list_processed_sessions(self, storage_manager):
        """Test listing processed sessions."""
        # Create some test sessions
        for i in range(3):
            db_file = storage_manager.processed_dir / f"session_{i}.db"
            db_file.touch()

        sessions = storage_manager.list_processed_sessions()
        assert len(sessions) == 3
        assert "session_0" in sessions
        assert "session_1" in sessions
        assert "session_2" in sessions

    def test_get_raw_session_path(self, storage_manager):
        """Test getting path to raw session."""
        path = storage_manager.get_raw_session_path("test_session")
        assert path == storage_manager.raw_dir / "test_session"

    def test_get_processed_session_path(self, storage_manager):
        """Test getting path to processed session."""
        path = storage_manager.get_processed_session_path("test_session")
        assert path == storage_manager.processed_dir / "test_session.db"

    def test_session_exists_raw(self, storage_manager):
        """Test checking if raw session exists."""
        session_id = "test_session"
        session_dir = storage_manager.raw_dir / session_id

        # Session doesn't exist
        assert not storage_manager.session_exists(session_id, processed=False)

        # Create session
        session_dir.mkdir()

        # Session exists
        assert storage_manager.session_exists(session_id, processed=False)

    def test_session_exists_processed(self, storage_manager):
        """Test checking if processed session exists."""
        session_id = "test_session"
        db_file = storage_manager.processed_dir / f"{session_id}.db"

        # Session doesn't exist
        assert not storage_manager.session_exists(session_id, processed=True)

        # Create session
        db_file.touch()

        # Session exists
        assert storage_manager.session_exists(session_id, processed=True)

    def test_get_session_metadata(self, storage_manager):
        """Test loading session metadata."""
        session_id = "test_session"
        session_dir = storage_manager.raw_dir / session_id
        session_dir.mkdir()

        # Create metadata
        metadata = {
            "session_id": session_id,
            "start_time": "2026-01-28T14:30:00",
            "total_blocks": 42,
        }

        with open(session_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)

        # Load metadata
        loaded_metadata = storage_manager.get_session_metadata(session_id)

        assert loaded_metadata is not None
        assert loaded_metadata["session_id"] == session_id
        assert loaded_metadata["total_blocks"] == 42

    def test_get_session_metadata_not_found(self, storage_manager):
        """Test loading metadata for non-existent session."""
        metadata = storage_manager.get_session_metadata("nonexistent")
        assert metadata is None

    def test_delete_raw_session(self, storage_manager):
        """Test deleting a raw session."""
        session_id = "test_session"
        session_dir = storage_manager.raw_dir / session_id
        session_dir.mkdir()

        # Create some files
        (session_dir / "test.txt").touch()

        # Delete session
        result = storage_manager.delete_session(session_id, processed=False)

        assert result is True
        assert not session_dir.exists()

    def test_delete_processed_session(self, storage_manager):
        """Test deleting a processed session."""
        session_id = "test_session"
        db_file = storage_manager.processed_dir / f"{session_id}.db"
        db_file.touch()

        # Delete session
        result = storage_manager.delete_session(session_id, processed=True)

        assert result is True
        assert not db_file.exists()

    def test_delete_nonexistent_session(self, storage_manager):
        """Test deleting a non-existent session."""
        result = storage_manager.delete_session("nonexistent", processed=False)
        assert result is False

    def test_cleanup_old_sessions(self, storage_manager):
        """Test cleaning up old sessions."""
        # Create old raw session
        old_session = storage_manager.raw_dir / "old_session"
        old_session.mkdir()

        old_time = datetime.now() - timedelta(days=40)
        metadata = {"session_id": "old_session", "start_time": old_time.isoformat()}

        with open(old_session / "metadata.json", "w") as f:
            json.dump(metadata, f)

        # Create recent raw session
        recent_session = storage_manager.raw_dir / "recent_session"
        recent_session.mkdir()

        recent_time = datetime.now() - timedelta(days=10)
        metadata = {
            "session_id": "recent_session",
            "start_time": recent_time.isoformat(),
        }

        with open(recent_session / "metadata.json", "w") as f:
            json.dump(metadata, f)

        # Cleanup sessions older than 30 days
        deleted = storage_manager.cleanup_old_sessions(days=30, processed_only=False)

        # Old session should be deleted, recent one should remain
        assert "old_session" in deleted
        assert not old_session.exists()
        assert recent_session.exists()
