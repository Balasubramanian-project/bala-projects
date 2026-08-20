"""
Handles turning a selected highlight clip into a finished vertical reel:
smart (face-aware) cropping to 9:16, caption overlays, and watermarking.
"""

import cv2
import numpy as np
from moviepy.editor import CompositeVideoClip, TextClip, VideoClip

from .utils import get_logger

logger = get_logger("VideoEditor")

_FACE_CASCADE = None


def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _FACE_CASCADE = cv2.CascadeClassifier(path)
    return _FACE_CASCADE


class VideoEditor:
    def __init__(self, output_width: int = 1080, output_height: int = 1920):
        self.output_width = output_width
        self.output_height = output_height
        self.target_ratio = output_width / output_height

    def _detect_face_center_x(self, frame_rgb) -> float:
        """Return the horizontal center (0-1 fraction of width) of the largest
        detected face in a frame, or 0.5 (frame center) if none is found."""
        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
        faces = _get_face_cascade().detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
        )
        if len(faces) == 0:
            return 0.5
        # Pick the largest face by area.
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        cx = x + w / 2
        return cx / frame_rgb.shape[1]

    def crop_to_vertical(self, clip, mode: str = "smart"):
        """
        Crop a landscape/square clip down to the target vertical aspect
        ratio. In 'smart' mode, sample a handful of frames to detect a
        face and bias the crop window towards it; otherwise crop from
        the center.
        """
        src_w, src_h = clip.size
        crop_w = min(src_w, int(src_h * self.target_ratio))
        crop_h = min(src_h, int(src_w / self.target_ratio))

        # Decide which dimension is the limiting factor.
        if crop_w < src_w:
            # We crop horizontally; find where to center the crop window.
            center_frac = 0.5
            if mode == "smart":
                center_frac = self._sample_face_center(clip)
            x_center = int(center_frac * src_w)
            x1 = max(0, min(src_w - crop_w, x_center - crop_w // 2))
            cropped = clip.crop(x1=x1, y1=0, x2=x1 + crop_w, y2=src_h)
        else:
            # Crop vertically (video already taller than target ratio needs).
            y1 = max(0, (src_h - crop_h) // 2)
            cropped = clip.crop(x1=0, y1=y1, x2=src_w, y2=y1 + crop_h)

        return cropped.resize((self.output_width, self.output_height))

    def _sample_face_center(self, clip, num_samples: int = 5) -> float:
        """Average the detected face center across a few sampled frames."""
        duration = clip.duration
        centers = []
        for i in range(num_samples):
            t = duration * (i + 0.5) / num_samples
            try:
                frame = clip.get_frame(t)
                centers.append(self._detect_face_center_x(frame))
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Face sampling failed at t=%.2f: %s", t, exc)
        if not centers:
            return 0.5
        return float(np.mean(centers))

    def add_captions(self, clip, captions, font=None, font_size=60,
                      color="white", stroke_color="black", stroke_width=2):
        """
        Overlay a list of (start, end, text) caption chunks onto the clip,
        bottom-anchored, one chunk visible at a time.
        """
        overlays = [clip]
        for start, end, text in captions:
            if not text.strip():
                continue
            try:
                txt_clip = (
                    TextClip(
                        text, fontsize=font_size, color=color, font=font,
                        stroke_color=stroke_color, stroke_width=stroke_width,
                        method="caption", size=(int(clip.w * 0.9), None),
                    )
                    .set_position(("center", "bottom"))
                    .set_start(start)
                    .set_end(end)
                )
                overlays.append(txt_clip)
            except Exception as exc:  # pragma: no cover - font issues, etc.
                logger.warning("Skipping caption '%s...': %s", text[:20], exc)
        return CompositeVideoClip(overlays, size=clip.size)

    def add_watermark(self, clip, text, font_size=40, color="white"):
        """Add a small persistent watermark/handle in the top-right corner."""
        try:
            wm = (
                TextClip(text, fontsize=font_size, color=color, method="label")
                .set_position(("right", "top"))
                .set_duration(clip.duration)
                .margin(right=20, top=20, opacity=0)
            )
            return CompositeVideoClip([clip, wm], size=clip.size)
        except Exception as exc:  # pragma: no cover
            logger.warning("Skipping watermark: %s", exc)
            return clip
