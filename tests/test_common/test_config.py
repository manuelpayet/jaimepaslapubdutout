"""
Tests for configuration management.
"""

import pytest
import os
import tempfile
from pathlib import Path
import yaml

from src.common.config import RadioListenerConfig, ClassifierConfig, ConfigLoader


class TestRadioListenerConfig:
    """Tests for RadioListenerConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RadioListenerConfig(stream_url="rtsp://example.com/stream")

        assert config.stream_url == "rtsp://example.com/stream"
        assert config.block_duration == 10
        assert config.sample_rate == 16000
        assert config.whisper_model == "base"
        assert config.whisper_language == "fr"
        assert config.output_dir == "data/raw"
        assert config.session_id is None

    def test_custom_values(self):
        """Test custom configuration values."""
        config = RadioListenerConfig(
            stream_url="rtsp://test.com/stream",
            block_duration=30,
            sample_rate=44100,
            whisper_model="small",
            whisper_language="en",
            output_dir="/tmp/output",
            session_id="test_session",
        )

        assert config.stream_url == "rtsp://test.com/stream"
        assert config.block_duration == 30
        assert config.sample_rate == 44100
        assert config.whisper_model == "small"
        assert config.whisper_language == "en"
        assert config.output_dir == "/tmp/output"
        assert config.session_id == "test_session"

    def test_validation_block_duration(self):
        """Test validation of block_duration."""
        with pytest.raises(ValueError, match="block_duration must be positive"):
            RadioListenerConfig(stream_url="rtsp://test.com", block_duration=0)

        with pytest.raises(ValueError, match="block_duration must be positive"):
            RadioListenerConfig(stream_url="rtsp://test.com", block_duration=-10)

    def test_validation_sample_rate(self):
        """Test validation of sample_rate."""
        with pytest.raises(ValueError, match="sample_rate must be positive"):
            RadioListenerConfig(stream_url="rtsp://test.com", sample_rate=0)

    def test_validation_whisper_model(self):
        """Test validation of whisper_model."""
        with pytest.raises(ValueError, match="Invalid whisper_model"):
            RadioListenerConfig(stream_url="rtsp://test.com", whisper_model="invalid")


class TestClassifierConfig:
    """Tests for ClassifierConfig."""

    def test_default_values(self, tmp_path):
        """Test default configuration values."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"

        config = ClassifierConfig(input_dir=str(input_dir), output_dir=str(output_dir))

        assert config.input_dir == str(input_dir)
        assert config.output_dir == str(output_dir)

        # Check directories were created
        assert input_dir.exists()
        assert output_dir.exists()


class TestConfigLoader:
    """Tests for ConfigLoader."""

    def test_load_from_kwargs(self):
        """Test loading configuration from kwargs."""
        config = ConfigLoader.load_radio_listener_config(
            stream_url="rtsp://test.com/stream",
            block_duration=20,
            whisper_model="small",
        )

        assert config.stream_url == "rtsp://test.com/stream"
        assert config.block_duration == 20
        assert config.whisper_model == "small"

    def test_load_from_yaml_file(self, tmp_path):
        """Test loading configuration from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "radio_listener": {
                "stream_url": "rtsp://yaml.com/stream",
                "block_duration": 15,
                "whisper_model": "tiny",
            }
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = ConfigLoader.load_radio_listener_config(config_file=str(config_file))

        assert config.stream_url == "rtsp://yaml.com/stream"
        assert config.block_duration == 15
        assert config.whisper_model == "tiny"

    def test_load_from_env_vars(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("STREAM_URL", "rtsp://env.com/stream")
        monkeypatch.setenv("BLOCK_DURATION", "25")
        monkeypatch.setenv("WHISPER_MODEL", "medium")

        config = ConfigLoader.load_radio_listener_config()

        assert config.stream_url == "rtsp://env.com/stream"
        assert config.block_duration == 25
        assert config.whisper_model == "medium"

    def test_priority_order(self, tmp_path, monkeypatch):
        """Test that kwargs override file config and env vars."""
        # Setup env vars
        monkeypatch.setenv("STREAM_URL", "rtsp://env.com/stream")
        monkeypatch.setenv("BLOCK_DURATION", "25")

        # Setup config file
        config_file = tmp_path / "config.yaml"
        config_data = {
            "radio_listener": {
                "stream_url": "rtsp://yaml.com/stream",
                "block_duration": 15,
                "whisper_model": "tiny",
            }
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Load with kwargs (should override everything)
        config = ConfigLoader.load_radio_listener_config(
            config_file=str(config_file),
            block_duration=30,  # This should win
        )

        # kwargs wins
        assert config.block_duration == 30
        # File config wins over env
        assert config.stream_url == "rtsp://yaml.com/stream"
        assert config.whisper_model == "tiny"
