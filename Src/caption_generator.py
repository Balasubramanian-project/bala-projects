"""
Generates timed captions for a clip by chunking its audio into short
windows and running each through speech recognition. This keeps the
implementation dependency-light (no large local ASR model download),
at the cost of coarser per-chunk timing rather than word-level timing.
"""

import os
import tempfile

import speech_recognition as sr

from .utils import get_logger

logger = get_logger("CaptionGenerator")


class CaptionGenerator:
    def __init__(self, chunk_seconds: float = 4.0):
        self.chunk_seconds = chunk_seconds
        self.recognizer = sr.Recognizer()

    def generate(self, clip):
        """
        Returns a list of (start, end, text) caption chunks covering the
        full duration of the clip. Chunks that fail to transcribe (e.g.
        silence, no internet) are simply omitted rather than raising.
        """
        if clip.audio is None:
            logger.warning("Clip has no audio track; skipping captions.")
            return []

        captions = []
        duration = clip.duration
        t = 0.0
        tmp_path = os.path.join(tempfile.gettempdir(), "reel_caption_chunk.wav")

        while t < duration:
            end = min(t + self.chunk_seconds, duration)
            try:
                sub_audio = clip.audio.subclip(t, end)
                sub_audio.write_audiofile(tmp_path, logger=None, fps=16000)
                with sr.AudioFile(tmp_path) as source:
                    audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                captions.append((t, end, text))
            except sr.UnknownValueError:
                pass  # No speech detected in this chunk; skip silently.
            except Exception as exc:
                logger.warning("Caption chunk %.1f-%.1fs failed: %s", t, end, exc)
            t = end

        logger.info("Generated %d caption chunks.", len(captions))
        return captions
