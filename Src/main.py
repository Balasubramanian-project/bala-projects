"""
AI Reel Generator
==================
Takes a long-form input video, detects the most 'exciting' moments using
audio energy + visual motion analysis, and exports each as a short,
vertically-cropped reel with optional auto-generated captions.

Usage:
    python -m src.main --input path/to/video.mp4 --num-reels 3 --duration 30
"""

import argparse
import os
import sys

from moviepy.editor import VideoFileClip

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.audio_analyzer import AudioAnalyzer
from src.scene_analyzer import SceneAnalyzer
from src.highlight_selector import HighlightSelector
from src.video_editor import VideoEditor
from src.caption_generator import CaptionGenerator
from src.utils import get_logger, ensure_dir, format_timestamp

logger = get_logger("ReelGenerator")


class ReelGenerator:
    def __init__(self, input_path: str, output_dir: str, num_reels: int,
                 duration: float, captions_enabled: bool, crop_mode: str):
        self.input_path = input_path
        self.output_dir = ensure_dir(output_dir)
        self.num_reels = num_reels
        self.duration = duration
        self.captions_enabled = captions_enabled
        self.crop_mode = crop_mode

        self.audio_analyzer = AudioAnalyzer(window_seconds=config.WINDOW_SECONDS)
        self.scene_analyzer = SceneAnalyzer(window_seconds=config.WINDOW_SECONDS)
        self.selector = HighlightSelector(
            audio_weight=config.AUDIO_WEIGHT, motion_weight=config.MOTION_WEIGHT
        )
        self.editor = VideoEditor(
            output_width=config.OUTPUT_WIDTH, output_height=config.OUTPUT_HEIGHT
        )
        self.caption_gen = CaptionGenerator(chunk_seconds=config.CAPTION_CHUNK_SECONDS)

    def run(self):
        logger.info("Loading video: %s", self.input_path)
        clip = VideoFileClip(self.input_path)

        logger.info("Analyzing audio energy...")
        audio_path = self.audio_analyzer.extract_audio(clip)
        audio_timeline = self.audio_analyzer.compute_energy_timeline(audio_path)

        logger.info("Analyzing visual motion...")
        motion_timeline = self.scene_analyzer.compute_motion_timeline(self.input_path)

        fused = self.selector.fuse_timelines(audio_timeline, motion_timeline)
        segments = self.selector.select_segments(
            fused,
            segment_duration=self.duration,
            num_segments=self.num_reels,
            min_gap=config.MIN_GAP_SECONDS,
        )

        if not segments:
            logger.error("No highlight segments could be selected. Aborting.")
            return []

        output_paths = []
        for i, seg in enumerate(segments, start=1):
            logger.info(
                "Rendering reel %d/%d (%s - %s)...",
                i, len(segments), format_timestamp(seg.start), format_timestamp(seg.end),
            )
            output_paths.append(self._render_reel(clip, seg, index=i))

        clip.close()
        logger.info("Done. %d reels written to %s", len(output_paths), self.output_dir)
        return output_paths

    def _render_reel(self, clip, segment, index: int) -> str:
        sub = clip.subclip(segment.start, segment.end)
        vertical = self.editor.crop_to_vertical(sub, mode=self.crop_mode)

        if self.captions_enabled:
            captions = self.caption_gen.generate(sub)
            # Re-anchor caption timestamps to the subclip's local timeline.
            local_captions = [(s - segment.start, e - segment.start, t) for s, e, t in captions]
            vertical = self.editor.add_captions(
                vertical, local_captions,
                font=config.CAPTION_FONT, font_size=config.CAPTION_FONT_SIZE,
                color=config.CAPTION_COLOR, stroke_color=config.CAPTION_STROKE_COLOR,
                stroke_width=config.CAPTION_STROKE_WIDTH,
            )

        if config.WATERMARK_TEXT:
            vertical = self.editor.add_watermark(
                vertical, config.WATERMARK_TEXT, font_size=config.WATERMARK_FONT_SIZE
            )

        out_path = os.path.join(self.output_dir, f"reel_{index}.mp4")
        vertical.write_videofile(
            out_path, fps=config.OUTPUT_FPS, codec="libx264", audio_codec="aac", logger=None
        )
        return out_path


def parse_args():
    parser = argparse.ArgumentParser(description="AI-based short reel generator.")
    parser.add_argument("--input", required=True, help="Path to the source video file.")
    parser.add_argument("--output-dir", default="output", help="Directory to save reels.")
    parser.add_argument("--num-reels", type=int, default=config.NUM_REELS_DEFAULT)
    parser.add_argument("--duration", type=float, default=config.REEL_DURATION_SECONDS,
                         help="Target length of each reel, in seconds.")
    parser.add_argument("--no-captions", action="store_true",
                         help="Disable auto-generated captions.")
    parser.add_argument("--crop-mode", choices=["smart", "center"],
                         default=config.CROP_MODE_DEFAULT,
                         help="'smart' uses face detection to guide the crop window.")
    return parser.parse_args()


def main():
    args = parse_args()
    generator = ReelGenerator(
        input_path=args.input,
        output_dir=args.output_dir,
        num_reels=args.num_reels,
        duration=args.duration,
        captions_enabled=not args.no_captions,
        crop_mode=args.crop_mode,
    )
    generator.run()


if __name__ == "__main__":
    main()
