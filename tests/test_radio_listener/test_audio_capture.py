"""
Tests for audio capture.
Note: These tests mock subprocess/FFmpeg to avoid requiring actual RTSP streams.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import subprocess

from src.radio_listener.audio_capture import AudioCapture


class TestAudioCapture:
    """Tests for AudioCapture."""

    @pytest.fixture
    def audio_capture(self):
        """Create an AudioCapture instance."""
        return AudioCapture(
            stream_url="rtsp://test.com/stream", sample_rate=16000, buffer_size=10
        )

    def test_initialization(self, audio_capture):
        """Test audio capture initialization."""
        assert audio_capture.stream_url == "rtsp://test.com/stream"
        assert audio_capture.sample_rate == 16000
        assert audio_capture.buffer_size == 10
        assert audio_capture._process is None
        assert audio_capture._capture_thread is None

    @patch("subprocess.Popen")
    def test_start_capture(self, mock_popen, audio_capture):
        """Test starting audio capture."""
        # Mock FFmpeg process
        mock_process = Mock()
        # Mock stdout to return empty bytes (simulate stream end)
        mock_process.stdout = Mock()
        mock_process.stdout.read = Mock(return_value=b"")
        mock_process.stderr = Mock()
        mock_popen.return_value = mock_process

        audio_capture.start_capture()

        # Check that subprocess was called
        assert mock_popen.called

        # Check FFmpeg command
        call_args = mock_popen.call_args[0][0]
        assert "ffmpeg" in call_args
        assert "rtsp://test.com/stream" in call_args
        assert "-ar" in call_args
        assert "16000" in call_args

        # Check that thread was started
        assert audio_capture._capture_thread is not None
        # Note: Thread may stop quickly if no data, so we just check it was created

        # Cleanup
        audio_capture.stop_capture()

    @patch("subprocess.Popen")
    def test_start_capture_already_started(self, mock_popen, audio_capture):
        """Test that starting capture twice doesn't create multiple processes."""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_popen.return_value = mock_process

        audio_capture.start_capture()
        first_process = audio_capture._process

        audio_capture.start_capture()

        # Should still be the same process
        assert audio_capture._process is first_process

        # Cleanup
        audio_capture.stop_capture()

    def test_is_alive_not_started(self, audio_capture):
        """Test is_alive when capture not started."""
        assert audio_capture.is_alive() is False

    @patch("subprocess.Popen")
    def test_is_alive_started(self, mock_popen, audio_capture):
        """Test is_alive when capture is running."""
        import time

        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        # Mock stdout to provide continuous data
        mock_process.stdout = Mock()

        # Create a generator that yields audio data continuously
        def generate_audio_data(size):
            # Return valid audio data (16-bit PCM samples)
            return np.random.randint(-32768, 32767, size, dtype=np.int16).tobytes()

        mock_process.stdout.read = Mock(
            side_effect=lambda size: generate_audio_data(size)
        )
        mock_process.stderr = Mock()
        mock_popen.return_value = mock_process

        audio_capture.start_capture()

        # Give the thread a moment to start processing
        time.sleep(0.1)

        assert audio_capture.is_alive() is True

        # Cleanup
        audio_capture.stop_capture()

    @patch("subprocess.Popen")
    def test_stop_capture(self, mock_popen, audio_capture):
        """Test stopping audio capture."""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        audio_capture.start_capture()
        audio_capture.stop_capture()

        # Check that process was terminated
        mock_process.terminate.assert_called_once()

        # Check that process is None
        assert audio_capture._process is None

    @patch("subprocess.Popen")
    def test_get_stats(self, mock_popen, audio_capture):
        """Test getting capture statistics."""
        import time

        mock_process = Mock()
        mock_process.poll.return_value = None
        # Mock stdout to provide continuous data
        mock_process.stdout = Mock()

        def generate_audio_data(size):
            return np.random.randint(-32768, 32767, size, dtype=np.int16).tobytes()

        mock_process.stdout.read = Mock(
            side_effect=lambda size: generate_audio_data(size)
        )
        mock_process.stderr = Mock()
        mock_popen.return_value = mock_process

        audio_capture.start_capture()

        # Give the thread a moment to start processing
        time.sleep(0.1)

        stats = audio_capture.get_stats()

        assert "bytes_read" in stats
        assert "errors" in stats
        assert "buffer_size" in stats
        assert "is_alive" in stats

        assert stats["is_alive"] is True

        # Cleanup
        audio_capture.stop_capture()

    def test_read_chunk_not_started(self, audio_capture):
        """Test reading chunk when capture not started."""
        chunk = audio_capture.read_chunk(1)

        assert chunk is None
