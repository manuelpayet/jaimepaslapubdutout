"""
Audio capture from audio streams using FFmpeg.
Supports RTSP, HTTP, HLS, and other FFmpeg-compatible streams.
"""

import subprocess
import threading
import queue
import numpy as np
from typing import Optional
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class AudioCapture:
    """
    Captures audio from various stream types via FFmpeg.
    Supports RTSP, HTTP/HTTPS, HLS, and other formats.
    Optimized for low memory consumption using circular buffer.
    """

    def __init__(
        self, stream_url: str, sample_rate: int = 16000, buffer_size: int = 10
    ):
        """
        Initialize audio capture.

        Args:
            stream_url: URL of the audio stream (RTSP, HTTP, HLS, etc.)
            sample_rate: Sample rate in Hz (16kHz for Whisper)
            buffer_size: Size of audio buffer in seconds
        """
        self.stream_url = stream_url
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # Detect stream type
        self.stream_type = self._detect_stream_type(stream_url)

        # FFmpeg process
        self._process: Optional[subprocess.Popen] = None
        self._capture_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Audio buffer (queue of numpy arrays)
        self._buffer: queue.Queue = queue.Queue(maxsize=buffer_size * 2)

        # Statistics
        self._bytes_read = 0
        self._errors = 0

    def _detect_stream_type(self, url: str) -> str:
        """
        Detect the type of stream from URL.

        Args:
            url: Stream URL

        Returns:
            Stream type: 'rtsp', 'http', 'hls', or 'unknown'
        """
        parsed = urlparse(url.lower())
        scheme = parsed.scheme
        path = parsed.path.lower()

        if scheme in ["rtsp", "rtsps"]:
            return "rtsp"
        elif path.endswith(".m3u8") or path.endswith(".m3u"):
            return "hls"
        elif scheme in ["http", "https"]:
            return "http"
        else:
            return "unknown"

    def start_capture(self) -> None:
        """Start capturing audio from the stream."""
        if self._process is not None:
            logger.warning("Capture already started")
            return

        logger.info(f"Starting audio capture from {self.stream_url}")
        logger.info(f"Detected stream type: {self.stream_type}")

        # Build FFmpeg command based on stream type
        command = self._build_ffmpeg_command()

        logger.debug(f"FFmpeg command: {' '.join(command)}")

        try:
            self._process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8
            )

            # Start capture thread
            self._stop_event.clear()
            self._capture_thread = threading.Thread(
                target=self._capture_loop, daemon=True
            )
            self._capture_thread.start()

            # Start stderr monitoring thread
            self._stderr_thread = threading.Thread(
                target=self._monitor_stderr, daemon=True
            )
            self._stderr_thread.start()

            logger.info("Audio capture started successfully")

        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            raise

    def _build_ffmpeg_command(self) -> list:
        """
        Build FFmpeg command with appropriate options for stream type.

        Returns:
            List of command arguments
        """
        command = ["ffmpeg"]

        # Add stream-specific input options
        if self.stream_type == "rtsp":
            # RTSP-specific options
            command.extend(
                [
                    "-rtsp_transport",
                    "tcp",  # Use TCP for reliability
                    "-rtsp_flags",
                    "prefer_tcp",
                    "-stimeout",
                    "5000000",  # 5 second timeout
                ]
            )
        elif self.stream_type in ["http", "hls"]:
            # HTTP/HLS-specific options
            command.extend(
                [
                    "-reconnect",
                    "1",  # Enable auto-reconnection
                    "-reconnect_streamed",
                    "1",
                    "-reconnect_delay_max",
                    "5",  # Max 5 seconds between retries
                    "-timeout",
                    "10000000",  # 10 second timeout (microseconds)
                ]
            )

        # Input URL
        command.extend(["-i", self.stream_url])

        # Common audio processing options
        command.extend(
            [
                "-vn",  # No video
                "-acodec",
                "pcm_s16le",  # 16-bit PCM
                "-ar",
                str(self.sample_rate),  # Sample rate
                "-ac",
                "1",  # Mono
                "-f",
                "s16le",  # Raw format
                "pipe:1",  # Output to stdout
            ]
        )

        return command

    def _monitor_stderr(self) -> None:
        """
        Monitor FFmpeg stderr for errors and warnings.
        Runs in a separate thread.
        """
        if not self._process or not self._process.stderr:
            return

        try:
            for line in iter(self._process.stderr.readline, b""):
                if self._stop_event.is_set():
                    break

                line_str = line.decode("utf-8", errors="ignore").strip()

                # Log important FFmpeg messages
                if line_str:
                    # Filter out verbose messages
                    if any(
                        x in line_str.lower()
                        for x in ["error", "failed", "invalid", "could not"]
                    ):
                        logger.error(f"FFmpeg error: {line_str}")
                    elif "warning" in line_str.lower():
                        logger.warning(f"FFmpeg warning: {line_str}")
                    elif any(
                        x in line_str.lower()
                        for x in ["input #0", "stream #0", "duration:"]
                    ):
                        logger.info(f"FFmpeg info: {line_str}")

        except Exception as e:
            logger.error(f"Error monitoring FFmpeg stderr: {e}")

    def _capture_loop(self) -> None:
        """
        Internal loop that reads from FFmpeg stdout and fills the buffer.
        Runs in a separate thread.
        """
        if not self._process or not self._process.stdout:
            logger.error("Cannot start capture loop: process not initialized")
            return

        # Each sample is 2 bytes (16-bit)
        chunk_size = self.sample_rate * 2  # 1 second of audio

        while not self._stop_event.is_set() and self._process:
            try:
                # Read chunk from FFmpeg stdout
                raw_data = self._process.stdout.read(chunk_size)

                if not raw_data:
                    logger.warning(
                        "No data received from FFmpeg, stream may have ended"
                    )
                    break

                # Convert bytes to numpy array
                audio_data = np.frombuffer(raw_data, dtype=np.int16)

                # Convert to float32 normalized to [-1, 1] (Whisper expects this)
                audio_data = audio_data.astype(np.float32) / 32768.0

                # Add to buffer (drop oldest if full)
                try:
                    self._buffer.put(audio_data, block=False)
                    self._bytes_read += len(raw_data)
                except queue.Full:
                    # Buffer full, drop oldest chunk
                    try:
                        self._buffer.get_nowait()
                        self._buffer.put(audio_data, block=False)
                    except queue.Empty:
                        pass

            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                self._errors += 1
                if self._errors > 10:
                    logger.error("Too many errors, stopping capture")
                    break

    def read_chunk(self, duration_seconds: int) -> Optional[np.ndarray]:
        """
        Read a chunk of audio of specified duration.

        Args:
            duration_seconds: Duration in seconds

        Returns:
            Numpy array with audio data, or None if not enough data available
        """
        if not self.is_alive():
            logger.error("Cannot read chunk: capture not active")
            return None

        # Calculate number of chunks needed
        chunks_needed = duration_seconds

        chunks = []
        for _ in range(chunks_needed):
            try:
                chunk = self._buffer.get(timeout=duration_seconds + 1)
                chunks.append(chunk)
            except queue.Empty:
                logger.warning(f"Timeout reading audio chunk after {duration_seconds}s")
                if chunks:
                    # Return what we have
                    break
                return None

        if not chunks:
            return None

        # Concatenate all chunks
        audio_data = np.concatenate(chunks)

        return audio_data

    def stop_capture(self) -> None:
        """Stop the audio capture gracefully."""
        logger.info("Stopping audio capture")

        # Signal threads to stop
        self._stop_event.set()

        # Wait for threads to finish
        if self._capture_thread:
            self._capture_thread.join(timeout=5)

        if self._stderr_thread:
            self._stderr_thread.join(timeout=5)

        # Terminate FFmpeg process
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("FFmpeg did not terminate, killing process")
                self._process.kill()
            finally:
                self._process = None

        logger.info("Audio capture stopped")

    def is_alive(self) -> bool:
        """
        Check if the capture is still active.

        Returns:
            True if capture is running
        """
        return (
            self._process is not None
            and self._process.poll() is None
            and self._capture_thread is not None
            and self._capture_thread.is_alive()
        )

    def get_stats(self) -> dict:
        """
        Get capture statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "bytes_read": self._bytes_read,
            "errors": self._errors,
            "buffer_size": self._buffer.qsize(),
            "is_alive": self.is_alive(),
        }
