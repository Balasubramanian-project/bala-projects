# AI Reel Generator 🎬

Automatically turn a long-form video (podcast, lecture, vlog, gameplay
recording, etc.) into short, vertical, social-media-ready "reels" —
no manual clip-picking required.

The tool analyzes the video's **audio energy** and **visual motion**
to score every moment, selects the most exciting non-overlapping
segments, smart-crops them to 9:16 using face detection, and can
auto-generate burned-in captions.

## How it works

```
Input video
    │
    ├─► AudioAnalyzer   → per-second energy score (RMS of the waveform)
    ├─► SceneAnalyzer    → per-second motion score (frame-diff magnitude)
    │
    ▼
HighlightSelector  → fuses both signals, slides a window across the
                      timeline, and greedily picks the top-K highest-
                      scoring, non-overlapping segments
    │
    ▼
VideoEditor        → crops each segment to vertical 9:16, biasing the
                      crop window toward detected faces
    │
    ├─► CaptionGenerator (optional) → chunked speech-to-text captions
    │
    ▼
reel_1.mp4, reel_2.mp4, reel_3.mp4 ...
```

## Features

- **Highlight detection** from a fused audio-energy + motion-magnitude
  signal — no manual scrubbing through footage.
- **Smart vertical cropping** using OpenCV face detection to keep the
  speaker/subject in frame instead of a blind center-crop.
- **Auto captions** (optional) via chunked speech recognition, burned
  into the video.
- **Config-driven** — all thresholds, weights, and output settings live
  in `config.py`.
- **Modular pipeline** — every stage (`AudioAnalyzer`, `SceneAnalyzer`,
  `HighlightSelector`, `VideoEditor`, `CaptionGenerator`) is a
  standalone class that can be tested or swapped independently.

## Installation

```bash
git clone https://github.com/<your-username>/ai-reel-generator.git
cd ai-reel-generator
pip install -r requirements.txt
```

> Note: `moviepy` requires `ffmpeg` to be installed and available on
> your system PATH.

## Usage

```bash
python -m src.main --input path/to/video.mp4 --num-reels 3 --duration 30
```

| Flag | Default | Description |
|---|---|---|
| `--input` | *(required)* | Path to the source video |
| `--output-dir` | `output` | Where generated reels are saved |
| `--num-reels` | `3` | How many reels to generate |
| `--duration` | `30` | Target length of each reel, in seconds |
| `--no-captions` | off | Disable auto-generated captions |
| `--crop-mode` | `smart` | `smart` (face-aware) or `center` cropping |

Output reels are written as `output/reel_1.mp4`, `reel_2.mp4`, etc.,
each in 1080×1920 (9:16) vertical format.

## Project structure

```
reel-generator/
├── config.py                 # tunable parameters
├── requirements.txt
├── src/
│   ├── main.py                # CLI + pipeline orchestration
│   ├── audio_analyzer.py      # audio energy scoring
│   ├── scene_analyzer.py      # visual motion scoring
│   ├── highlight_selector.py  # score fusion + segment selection
│   ├── video_editor.py        # vertical crop, captions, watermark
│   ├── caption_generator.py   # speech-to-text captioning
│   └── utils.py
└── README.md
```

## Possible future improvements

- Swap the chunked speech-recognition captions for a local Whisper
  model to get word-level timestamps and remove the internet dependency.
- Add a scene-cut detector (histogram-based) so reels never start/end
  mid-cut.
- Rank highlights with a learned model instead of hand-tuned weights.
- Add background-music ducking under detected speech.
- Batch/parallel processing for multiple input videos.

## License

MIT
