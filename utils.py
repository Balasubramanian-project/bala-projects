"""Small shared helpers used across the pipeline."""

import logging
import os


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger with consistent formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s", "%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def ensure_dir(path: str) -> str:
    """Create a directory if it doesn't already exist and return its path."""
    os.makedirs(path, exist_ok=True)
    return path


def format_timestamp(seconds: float) -> str:
    """Convert seconds into a MM:SS string for logging/UI purposes."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def normalize(values):
    """Min-max normalize a list of numbers to the 0-1 range."""
    if not values:
        return values
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]
