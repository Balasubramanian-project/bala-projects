"""
Central configuration for the AI Reel Generator.
Tweak these values to change how highlights are detected and rendered.
"""

# --- Highlight detection ---
WINDOW_SECONDS = 1.0          # size of each scoring window
AUDIO_WEIGHT = 0.6            # contribution of audio energy to the highlight score
MOTION_WEIGHT = 0.4           # contribution of visual motion to the highlight score
MIN_GAP_SECONDS = 5.0         # minimum gap enforced between two selected reels

# --- Output format ---
REEL_DURATION_SECONDS = 30    # default length of each generated reel
NUM_REELS_DEFAULT = 3         # how many reels to produce per input video
OUTPUT_WIDTH = 1080           # vertical 9:16 output resolution
OUTPUT_HEIGHT = 1920
OUTPUT_FPS = 30

# --- Smart cropping ---
CROP_MODE_DEFAULT = "smart"   # "smart" (face-tracking) or "center"
FACE_DETECTION_SCALE = 1.1
FACE_DETECTION_MIN_NEIGHBORS = 5

# --- Captions ---
CAPTIONS_ENABLED_DEFAULT = True
CAPTION_CHUNK_SECONDS = 4.0   # granularity of caption chunks sent to speech recognition
CAPTION_FONT = "Arial-Bold"
CAPTION_FONT_SIZE = 60
CAPTION_COLOR = "white"
CAPTION_STROKE_COLOR = "black"
CAPTION_STROKE_WIDTH = 2

# --- Branding ---
WATERMARK_TEXT = None         # e.g. "@yourhandle" - set to None to disable
WATERMARK_FONT_SIZE = 40
