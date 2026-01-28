"""
Audio transcription using Whisper.
"""

import whisper
import numpy as np
from typing import Optional
import logging
from src.common.models import TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)


class Transcriber:
    """
    Transcribes audio to text using OpenAI Whisper.
    Supports different model sizes for performance/accuracy tradeoff.
    """

    def __init__(self, model_name: str = "base", language: str = "fr"):
        """
        Initialize transcriber with Whisper model.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            language: Language code for transcription (e.g., 'fr', 'en')
        """
        self.model_name = model_name
        self.language = language
        self._model: Optional[whisper.Whisper] = None

        logger.info(f"Initializing Whisper transcriber with model '{model_name}'")
        self._load_model()

    def _load_model(self) -> None:
        """Load the Whisper model into memory."""
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self._model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(self, audio_data: np.ndarray) -> TranscriptionResult:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Numpy array with audio samples (float32, normalized to [-1, 1])

        Returns:
            TranscriptionResult with text, segments, and language

        Raises:
            RuntimeError: If model is not loaded
        """
        if self._model is None:
            raise RuntimeError("Whisper model not loaded")

        try:
            logger.debug(f"Transcribing audio chunk of length {len(audio_data)}")

            # Run Whisper transcription
            result = self._model.transcribe(
                audio_data,
                language=self.language,
                fp16=False,  # Use FP32 for CPU compatibility
                verbose=False,
            )

            # Extract segments with timing
            segments = []
            for i, segment in enumerate(result.get("segments", [])):
                segments.append(
                    TranscriptionSegment(
                        id=i,
                        start=segment["start"],
                        end=segment["end"],
                        text=segment["text"].strip(),
                    )
                )

            # Get full text
            text = result.get("text", "").strip()

            # Get detected language
            detected_language = result.get("language", self.language)

            logger.debug(f"Transcription complete: {len(text)} characters")

            return TranscriptionResult(
                text=text, segments=segments, language=detected_language
            )

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def unload_model(self) -> None:
        """
        Unload the model from memory.
        Useful for freeing up RAM when not transcribing.
        """
        logger.info("Unloading Whisper model")
        self._model = None

    def is_loaded(self) -> bool:
        """
        Check if the model is loaded.

        Returns:
            True if model is loaded in memory
        """
        return self._model is not None
