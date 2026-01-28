"""
Audio capture from RTSP stream using FFmpeg.
"""

import subprocess
import threading
import queue
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AudioCapture:
    """
    Captures audio from RTSP stream via FFmpeg.
    Optimized for low memory consumption using circular buffer.
    """

    def __init__(self, rtsp_url: str, sample_rate: int = 16000, buffer_size: int = 10):
        """
        Initialize audio capture.

        Args:
            rtsp_url: URL of the RTSP stream
            sample_rate: Sample rate in Hz (16kHz for Whisper)
            buffer_size: Size of audio buffer in seconds
        """
        self.rtsp_url = rtsp_url
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # FFmpeg process
        self._process: Optional[subprocess.Popen] = None
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Audio buffer (queue of numpy arrays)
        self._buffer: queue.Queue = queue.Queue(maxsize=buffer_size * 2)

        # Statistics
        self._bytes_read = 0
        self._errors = 0

    def start_capture(self) -> None:
        """Start capturing audio from the RTSP stream."""
        if self._process is not None:
            logger.warning("Capture already started")
            return

        logger.info(f"Starting audio capture from {self.rtsp_url}")

        # FFmpeg command to extract audio
        # -rtsp_transport tcp: Use TCP for more reliable streaming
        # -i: Input URL
        # -vn: Disable video
        # -acodec pcm_s16le: Convert to 16-bit PCM
        # -ar: Sample rate
        # -ac 1: Mono audio
        # -f s16le: Raw 16-bit little-endian output
        # pipe:1: Output to stdout
        command = [
            "ffmpeg",
            "-rtsp_transport",
            "tcp",
            "-i",
            self.rtsp_url,
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

            logger.info("Audio capture started successfully")

        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            raise

    def _capture_loop(self) -> None:
        """
        Internal loop that reads from FFmpeg stdout and fills the buffer.
        Runs in a separate thread.
        """
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

        # Signal thread to stop
        self._stop_event.set()

        # Wait for thread to finish
        if self._capture_thread:
            self._capture_thread.join(timeout=5)

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
