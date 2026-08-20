"""
Analyzes the audio track of a video to score how 'exciting' each moment
sounds, using short-term RMS energy as a proxy for laughter, shouting,
music drops, applause, etc.
"""

import os
import tempfile

import numpy as np

from .utils import get_logger

logger = get_logger("AudioAnalyzer")


class AudioAnalyzer:
    def __init__(self, window_seconds: float = 1.0):
        self.window_seconds = window_seconds

    def extract_audio(self, video_clip, tmp_dir: str = None) -> str:
        """Extract the audio track of a moviepy clip to a temporary WAV file."""
        tmp_dir = tmp_dir or tempfile.gettempdir()
        audio_path = os.path.join(tmp_dir, "reel_audio_tmp.wav")
        if video_clip.audio is None:
            raise ValueError("Input video has no audio track.")
        video_clip.audio.write_audiofile(audio_path, logger=None, fps=22050)
        return audio_path

    def compute_energy_timeline(self, audio_path: str):
        """
        Returns a list of (start_time, end_time, score) tuples where score
        is the normalized RMS energy of that window, 0.0 - 1.0.
        """
        import librosa

        y, sr = librosa.load(audio_path, sr=None, mono=True)
        window_samples = int(self.window_seconds * sr)
        if window_samples <= 0:
            raise ValueError("window_seconds too small for this sample rate.")

        num_windows = max(1, len(y) // window_samples)
        raw_scores = []
        for i in range(num_windows):
            start = i * window_samples
            end = start + window_samples
            chunk = y[start:end]
            rms = float(np.sqrt(np.mean(chunk ** 2))) if len(chunk) else 0.0
            raw_scores.append(rms)

        lo, hi = min(raw_scores), max(raw_scores)
        spread = hi - lo if hi - lo > 1e-9 else 1.0
        timeline = []
        for i, score in enumerate(raw_scores):
            start_t = i * self.window_seconds
            end_t = start_t + self.window_seconds
            timeline.append((start_t, end_t, (score - lo) / spread))

        logger.info("Computed audio energy for %d windows.", len(timeline))
        return timeline
