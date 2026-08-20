"""
Analyzes the visual track of a video to score how much motion / visual
change is happening at each point in time. High motion often correlates
with action, gestures, or scene cuts worth featuring in a reel.
"""

import cv2
import numpy as np

from .utils import get_logger

logger = get_logger("SceneAnalyzer")


class SceneAnalyzer:
    def __init__(self, window_seconds: float = 1.0, sample_fps: float = 5.0):
        self.window_seconds = window_seconds
        self.sample_fps = sample_fps  # how many frames per second we actually inspect

    def compute_motion_timeline(self, video_path: str):
        """
        Returns a list of (start_time, end_time, score) tuples where score
        is the normalized frame-to-frame motion magnitude, 0.0 - 1.0.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps else 0.0
        frame_step = max(1, int(fps / self.sample_fps))

        prev_gray = None
        window_scores = {}  # window_index -> list of diffs
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_step == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, (160, 90))  # downscale for speed
                if prev_gray is not None:
                    diff = cv2.absdiff(gray, prev_gray)
                    motion = float(np.mean(diff))
                    t = frame_idx / fps
                    window_idx = int(t // self.window_seconds)
                    window_scores.setdefault(window_idx, []).append(motion)
                prev_gray = gray

            frame_idx += 1

        cap.release()

        num_windows = max(1, int(duration // self.window_seconds) + 1)
        raw_scores = [
            float(np.mean(window_scores[i])) if i in window_scores else 0.0
            for i in range(num_windows)
        ]

        lo, hi = min(raw_scores), max(raw_scores)
        spread = hi - lo if hi - lo > 1e-9 else 1.0
        timeline = []
        for i, score in enumerate(raw_scores):
            start_t = i * self.window_seconds
            end_t = start_t + self.window_seconds
            timeline.append((start_t, end_t, (score - lo) / spread))

        logger.info("Computed motion scores for %d windows.", len(timeline))
        return timeline
