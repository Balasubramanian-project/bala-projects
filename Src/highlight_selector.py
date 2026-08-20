"""
Fuses the audio-energy and motion timelines into a single excitement score
per time window, then selects the top-K non-overlapping segments to use
as reels.
"""

from .utils import get_logger, format_timestamp

logger = get_logger("HighlightSelector")


class HighlightSelector:
    def __init__(self, audio_weight: float = 0.6, motion_weight: float = 0.4):
        self.audio_weight = audio_weight
        self.motion_weight = motion_weight

    def fuse_timelines(self, audio_timeline, motion_timeline):
        """Combine two (start, end, score) timelines into one weighted timeline."""
        n = min(len(audio_timeline), len(motion_timeline))
        fused = []
        for i in range(n):
            start_t, end_t, a_score = audio_timeline[i]
            _, _, m_score = motion_timeline[i]
            combined = self.audio_weight * a_score + self.motion_weight * m_score
            fused.append((start_t, end_t, combined))
        return fused

    def select_segments(self, fused_timeline, segment_duration: float,
                         num_segments: int, min_gap: float = 5.0):
        """
        Slide a window of `segment_duration` across the fused timeline,
        summing scores to find the most exciting continuous stretches,
        then greedily pick the top `num_segments` non-overlapping ones.
        """
        if not fused_timeline:
            return []

        window_size = fused_timeline[0][1] - fused_timeline[0][0]
        windows_per_segment = max(1, int(segment_duration // window_size))

        candidates = []
        for i in range(len(fused_timeline) - windows_per_segment + 1):
            chunk = fused_timeline[i:i + windows_per_segment]
            score_sum = sum(s for _, _, s in chunk)
            start_t = chunk[0][0]
            end_t = chunk[-1][1]
            candidates.append((start_t, end_t, score_sum))

        # Sort best-first, then greedily accept non-overlapping candidates.
        candidates.sort(key=lambda c: c[2], reverse=True)

        selected = []
        for start_t, end_t, score in candidates:
            overlaps = any(
                not (end_t + min_gap <= s.start or start_t - min_gap >= s.end)
                for s in selected
            )
            if not overlaps:
                selected.append(_Segment(start_t, end_t, score))
            if len(selected) >= num_segments:
                break

        selected.sort(key=lambda s: s.start)
        for s in selected:
            logger.info(
                "Selected highlight: %s - %s (score=%.3f)",
                format_timestamp(s.start), format_timestamp(s.end), s.score,
            )
        return selected


class _Segment:
    def __init__(self, start, end, score):
        self.start = start
        self.end = end
        self.score = score
