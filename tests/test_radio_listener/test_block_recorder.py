"""
Tests for block recorder.
"""

import pytest
import numpy as np
import json
import wave
from pathlib import Path
from datetime import datetime

from src.radio_listener.block_recorder import BlockRecorder
from src.common.models import TranscriptionResult, TranscriptionSegment


class TestBlockRecorder:
    """Tests for BlockRecorder."""

    @pytest.fixture
    def recorder(self, tmp_path):
        """Create a BlockRecorder with temporary directory."""
        return BlockRecorder(
            output_dir=str(tmp_path), session_id="test_session", sample_rate=16000
        )

    @pytest.fixture
    def sample_audio(self):
        """Create sample audio data."""
        # Generate 1 second of sine wave
        sample_rate = 16000
        duration = 1.0
        frequency = 440.0  # A4 note

        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)

        return audio

    @pytest.fixture
    def sample_transcription(self):
        """Create sample transcription."""
        segments = [
            TranscriptionSegment(id=0, start=0.0, end=2.5, text="Hello world"),
            TranscriptionSegment(id=1, start=2.5, end=5.0, text="This is a test"),
        ]

        return TranscriptionResult(
            text="Hello world. This is a test.", segments=segments, language="en"
        )

    def test_initialization(self, recorder, tmp_path):
        """Test recorder initialization."""
        assert recorder.session_id == "test_session"
        assert recorder.sample_rate == 16000

        # Check directories were created
        session_dir = tmp_path / "test_session"
        blocks_dir = session_dir / "blocks"

        assert session_dir.exists()
        assert blocks_dir.exists()

    def test_save_block(self, recorder, sample_audio, sample_transcription, tmp_path):
        """Test saving a block."""
        timestamp = datetime.now()
        block_number = 0

        audio_path = recorder.save_block(
            audio_data=sample_audio,
            transcription=sample_transcription,
            block_number=block_number,
            timestamp=timestamp,
            block_duration=10,
        )

        # Check audio file was created
        audio_file = Path(audio_path)
        assert audio_file.exists()
        assert audio_file.suffix == ".wav"

        # Check text file was created
        text_file = audio_file.with_suffix(".txt")
        assert text_file.exists()

        # Check audio file is valid WAV
        with wave.open(str(audio_file), "rb") as wav:
            assert wav.getnchannels() == 1  # Mono
            assert wav.getsampwidth() == 2  # 16-bit
            assert wav.getframerate() == 16000

        # Check text file content
        with open(text_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Hello world. This is a test." in content
            assert "Language: en" in content
            assert "[0.00s - 2.50s] Hello world" in content

    def test_save_multiple_blocks(self, recorder, sample_audio, sample_transcription):
        """Test saving multiple blocks."""
        timestamp = datetime.now()

        for i in range(5):
            audio_path = recorder.save_block(
                audio_data=sample_audio,
                transcription=sample_transcription,
                block_number=i,
                timestamp=timestamp,
                block_duration=10,
            )

            assert Path(audio_path).exists()

        # Check metadata
        assert recorder.metadata["total_blocks"] == 5

    def test_block_numbering(self, recorder, sample_audio, sample_transcription):
        """Test that blocks are numbered correctly."""
        timestamp = datetime.now()

        # Save blocks out of order
        for block_num in [0, 2, 1, 4, 3]:
            recorder.save_block(
                audio_data=sample_audio,
                transcription=sample_transcription,
                block_number=block_num,
                timestamp=timestamp,
                block_duration=10,
            )

        # Check all blocks exist with correct naming
        blocks_dir = recorder.blocks_dir

        assert (blocks_dir / "block_0000.wav").exists()
        assert (blocks_dir / "block_0001.wav").exists()
        assert (blocks_dir / "block_0002.wav").exists()
        assert (blocks_dir / "block_0003.wav").exists()
        assert (blocks_dir / "block_0004.wav").exists()

    def test_update_metadata(self, recorder):
        """Test updating metadata."""
        recorder.update_metadata(
            rtsp_url="rtsp://test.com/stream", whisper_model="base"
        )

        assert recorder.metadata["rtsp_url"] == "rtsp://test.com/stream"
        assert recorder.metadata["whisper_model"] == "base"

    def test_finalize_session(self, recorder, tmp_path):
        """Test finalizing a session."""
        recorder.update_metadata(total_blocks=10)
        recorder.finalize_session()

        # Check metadata file was created
        metadata_file = tmp_path / "test_session" / "metadata.json"
        assert metadata_file.exists()

        # Check metadata content
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

            assert metadata["session_id"] == "test_session"
            assert metadata["total_blocks"] == 10
            assert "start_time" in metadata
            assert "end_time" in metadata
            assert metadata["end_time"] is not None

    def test_get_session_dir(self, recorder, tmp_path):
        """Test getting session directory."""
        session_dir = recorder.get_session_dir()

        assert session_dir == tmp_path / "test_session"
        assert session_dir.exists()
