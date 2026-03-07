# Gesture Control for Ableton Live

Real-time hand gesture recognition using your webcam to control Ableton Live playback.

## Requirements

- Python 3.10+
- Ableton Live with the [AbletonMCP Remote Script](https://github.com/ahujasid/ableton-mcp) installed and running (follow instructions there)

## Setup

```bash
pip install -r requirements.txt
```

Download the MediaPipe hand landmark model and place it in the project root:

```bash
wget -q https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

## Usage

```bash
python3 webcam_viewer.py
```

## Gestures

| Gesture | Action |
|---------|--------|
| Pointing | Start playback |
| Fist | Stop playback |
| Peace Sign | - |
| Open Hand | - |
| Thumbs Up | - |
| Rock On | - |

## How it works

- Uses [MediaPipe Hand Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) to detect 21 hand landmarks per hand in real time
- Gesture logic compares fingertip distances to determine which fingers are extended
- Connects to Ableton Live via a socket on `localhost:9877` and sends `start_playback` / `stop_playback` commands
- Works without Ableton connected — gesture detection still runs, Ableton commands are skipped

## Files

- `webcam_viewer.py` — main script
- `hand_landmarker.task` — MediaPipe hand landmark model (required)
