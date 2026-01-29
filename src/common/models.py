"""
Shared data models.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class TranscriptionSegment:
    """A segment of transcribed text with timing information."""

    id: int
    start: float  # seconds
    end: float  # seconds
    text: str


@dataclass
class TranscriptionResult:
    """Result of audio transcription."""

    text: str
    segments: List[TranscriptionSegment]
    language: str


@dataclass
class Block:
    """A single audio block with transcription."""

    block_number: int
    timestamp: datetime
    audio_path: str
    transcription: str
    category: str = "A classifier"  # Default category
