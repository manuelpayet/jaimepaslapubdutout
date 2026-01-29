"""
Configuration management for the radio transcription system.
"""

from dataclasses import dataclass, field
from typing import Optional
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv


@dataclass
class RadioListenerConfig:
    """Configuration for the radio listener module."""

    stream_url: str  # URL of audio stream (RTSP, HTTP, HLS, etc.)
    block_duration: int = 10  # seconds
    sample_rate: int = 16000  # Hz (Whisper expects 16kHz)
    whisper_model: str = "base"  # tiny, base, small, medium, large
    whisper_language: str = "fr"
    output_dir: str = "data/raw"
    session_id: Optional[str] = None  # Auto-generated if not provided

    def __post_init__(self):
        """Validate configuration."""
        if self.block_duration <= 0:
            raise ValueError("block_duration must be positive")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if self.whisper_model not in ["tiny", "base", "small", "medium", "large"]:
            raise ValueError(f"Invalid whisper_model: {self.whisper_model}")


@dataclass
class ClassifierConfig:
    """Configuration for the classifier module."""

    input_dir: str = "data/raw"
    output_dir: str = "data/processed"

    def __post_init__(self):
        """Ensure directories exist."""
        Path(self.input_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


class ConfigLoader:
    """Load configuration from various sources."""

    @staticmethod
    def load_radio_listener_config(
        config_file: Optional[str] = None, **kwargs
    ) -> RadioListenerConfig:
        """
        Load RadioListenerConfig from multiple sources.

        Priority order:
        1. Explicit kwargs
        2. Config file (YAML)
        3. Environment variables
        4. Default values

        Args:
            config_file: Path to YAML config file
            **kwargs: Explicit configuration values

        Returns:
            RadioListenerConfig instance
        """
        load_dotenv()  # Load .env file if present

        config = {}

        # Load from environment variables (lowest priority)
        env_mapping = {
            "STREAM_URL": "stream_url",
            "RTSP_URL": "stream_url",  # Backward compatibility
            "BLOCK_DURATION": "block_duration",
            "SAMPLE_RATE": "sample_rate",
            "WHISPER_MODEL": "whisper_model",
            "WHISPER_LANGUAGE": "whisper_language",
            "OUTPUT_DIR": "output_dir",
            "SESSION_ID": "session_id",
        }

        for env_var, config_key in env_mapping.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                # Convert numeric values
                if config_key in ["block_duration", "sample_rate"]:
                    value = int(value)
                config[config_key] = value

        # Load from config file if provided (overrides env vars)
        if config_file and os.path.exists(config_file):
            with open(config_file, "r") as f:
                file_config = yaml.safe_load(f)
                if file_config and "radio_listener" in file_config:
                    config.update(file_config["radio_listener"])

        # Override with explicit kwargs (highest priority)
        config.update(kwargs)

        return RadioListenerConfig(**config)

    @staticmethod
    def load_classifier_config(
        config_file: Optional[str] = None, **kwargs
    ) -> ClassifierConfig:
        """
        Load ClassifierConfig from multiple sources.

        Args:
            config_file: Path to YAML config file
            **kwargs: Explicit configuration values

        Returns:
            ClassifierConfig instance
        """
        load_dotenv()

        config = {}

        # Load from config file if provided
        if config_file and os.path.exists(config_file):
            with open(config_file, "r") as f:
                file_config = yaml.safe_load(f)
                if file_config and "classifier" in file_config:
                    config.update(file_config["classifier"])

        # Load from environment variables
        if "INPUT_DIR" in os.environ:
            config["input_dir"] = os.environ["INPUT_DIR"]
        if "OUTPUT_DIR" in os.environ:
            config["output_dir"] = os.environ["OUTPUT_DIR"]

        # Override with explicit kwargs
        config.update(kwargs)

        return ClassifierConfig(**config)
