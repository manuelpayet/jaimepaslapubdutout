"""
Tests for transcriber.
Note: These tests mock Whisper to avoid heavy model loading during testing.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from src.radio_listener.transcriber import Transcriber
from src.common.models import TranscriptionResult


class TestTranscriber:
    """Tests for Transcriber."""

    @pytest.fixture
    def mock_whisper_model(self):
        """Create a mock Whisper model."""
        model = Mock()
        model.transcribe = Mock(
            return_value={
                "text": "This is a test transcription.",
                "language": "en",
                "segments": [
                    {"start": 0.0, "end": 2.5, "text": "This is a test"},
                    {"start": 2.5, "end": 5.0, "text": "transcription."},
                ],
            }
        )
        return model

    @pytest.fixture
    def sample_audio(self):
        """Create sample audio data."""
        # 1 second of audio at 16kHz
        return np.random.randn(16000).astype(np.float32)

    @patch("src.radio_listener.transcriber.whisper.load_model")
    def test_initialization(self, mock_load_model, mock_whisper_model):
        """Test transcriber initialization."""
        mock_load_model.return_value = mock_whisper_model

        transcriber = Transcriber(model_name="base", language="fr")

        assert transcriber.model_name == "base"
        assert transcriber.language == "fr"
        assert transcriber._model is not None

        # Check that model was loaded
        mock_load_model.assert_called_once_with("base")

    @patch("src.radio_listener.transcriber.whisper.load_model")
    def test_transcribe(self, mock_load_model, mock_whisper_model, sample_audio):
        """Test audio transcription."""
        mock_load_model.return_value = mock_whisper_model

        transcriber = Transcriber(model_name="base", language="en")
        result = transcriber.transcribe(sample_audio)

        # Check result type
        assert isinstance(result, TranscriptionResult)

        # Check result content
        assert result.text == "This is a test transcription."
        assert result.language == "en"
        assert len(result.segments) == 2

        # Check segments
        assert result.segments[0].text == "This is a test"
        assert result.segments[0].start == 0.0
        assert result.segments[0].end == 2.5

        assert result.segments[1].text == "transcription."
        assert result.segments[1].start == 2.5
        assert result.segments[1].end == 5.0

        # Check that Whisper was called correctly
        mock_whisper_model.transcribe.assert_called_once()
        call_args = mock_whisper_model.transcribe.call_args
        assert call_args[1]["language"] == "en"
        assert call_args[1]["fp16"] is False
        assert call_args[1]["verbose"] is False

    @patch("src.radio_listener.transcriber.whisper.load_model")
    def test_transcribe_without_model(self, mock_load_model):
        """Test transcription fails when model is not loaded."""
        mock_load_model.return_value = None

        transcriber = Transcriber(model_name="base")
        transcriber._model = None

        with pytest.raises(RuntimeError, match="Whisper model not loaded"):
            transcriber.transcribe(np.zeros(16000))

    @patch("src.radio_listener.transcriber.whisper.load_model")
    def test_unload_model(self, mock_load_model, mock_whisper_model):
        """Test unloading the model."""
        mock_load_model.return_value = mock_whisper_model

        transcriber = Transcriber(model_name="base")

        assert transcriber.is_loaded() is True

        transcriber.unload_model()

        assert transcriber._model is None
        assert transcriber.is_loaded() is False

    @patch("src.radio_listener.transcriber.whisper.load_model")
    def test_is_loaded(self, mock_load_model, mock_whisper_model):
        """Test checking if model is loaded."""
        mock_load_model.return_value = mock_whisper_model

        transcriber = Transcriber(model_name="base")

        assert transcriber.is_loaded() is True

        transcriber._model = None
        assert transcriber.is_loaded() is False

    @patch("src.radio_listener.transcriber.whisper.load_model")
    def test_transcribe_empty_segments(self, mock_load_model, sample_audio):
        """Test transcription with no segments."""
        model = Mock()
        model.transcribe = Mock(
            return_value={"text": "Simple text", "language": "en", "segments": []}
        )
        mock_load_model.return_value = model

        transcriber = Transcriber(model_name="base")
        result = transcriber.transcribe(sample_audio)

        assert result.text == "Simple text"
        assert len(result.segments) == 0
