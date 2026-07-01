# YOLO Object Detection and Distance Estimation

A PySide6/OpenCV application for detecting objects in video streams, estimating approximate object distance, drawing distance-based warning zones, and exporting an annotated output video.

The current project is configured for a custom YOLO11n model saved as `best.pt`, with the target classes:

- `person`
- `dump truck`

## Features

- Real-time object detection using Ultralytics YOLO
- PySide6 GUI for viewing annotated video frames
- OpenCV video capture from local video files, RTSP streams, or camera sources
- Approximate distance estimation from bounding-box height
- Distance-based visualization:
  - Red zone: danger range
  - Yellow zone: warning range
  - Green bounding boxes for safer detections
- Annotated video export
- General application logging
- Detection-specific logging

## Project Structure

├── app/
│   ├── main.py              # Main application entry point
│   ├── processor.py         # YOLO inference, annotation, video writing
│   ├── distance.py          # Distance estimation logic
│   ├── ground_zone.py       # Red/yellow ground-zone drawing
│   ├── logger.py            # Logging configuration
│   ├── capture.py           # Alternative capture-thread implementation
│   └── gui.py               # Alternative GUI implementation
├── configs/
│   └── config.yaml          # Runtime configuration
├── videos/
│   └── movie.mp4            # Example input video
├── output/
│   └── movie.mp4            # Annotated output video
├── best.pt                  # Custom YOLO11n model weights
├── requirements.txt
└── README.md

## Requirements

Recommended Python version:

Python 3.10+


Install dependencies:

```bash
pip install -r requirements.txt
```

Minimal `requirements.txt`:

```txt
numpy
opencv-python
torch
ultralytics
PySide6
PyYAML
```

> Note: For CUDA/GPU acceleration, install the correct PyTorch build for your CUDA version. The generic `torch` package may install a CPU-only build depending on your system and package index.

## Configuration

The application reads its settings from:

```text
configs/config.yaml
```

Current example:

```yaml
model_path: "best.pt"

camera_sources:
  # - "rtsp://admin:123456@192.168.1.188:554/ch01.264"
  # - "rtsp://admin:123456@192.168.1.189:554/ch01.264"
  - "videos/movie.mp4"

app_type: 1
target_fps: 5
log_level: "DEBUG"

classes:
  - "person"
  - "dump truck"

camera_height: 2
target_resolution: [640, 640]
output_path: "output/movie.mp4"
```

### Configuration Fields

| Field | Description |
|---|---|
| `model_path` | Path to the YOLO model weights. In this project, `best.pt` is a custom YOLO11n model. |
| `camera_sources` | Input sources. Can be a local video path, RTSP URL, or camera index. |
| `app_type` | Runtime mode. See [Application Modes](#application-modes). |
| `target_fps` | Capture/processing rate used by the capture thread. |
| `log_level` | Logging level, for example `DEBUG`, `INFO`, `WARNING`, or `ERROR`. |
| `classes` | Class names expected from the trained YOLO model. |
| `camera_height` | Camera height in meters, used by the ground-zone visualization logic. |
| `target_resolution` | Fixed frame size used before inference. Current default is `640x640`. |
| `output_path` | Path where the annotated output video is saved. |

## Application Modes

The code currently uses `app_type` to control how processed frames are handled.

| `app_type` | Behavior |
|---:|---|
| `0` | Print detection results to console and save annotated video. |
| `1` | Show annotated frames in the PySide6 GUI and save annotated video. |
| `2` | Intended for video-export-only workflows. This requires the main program to avoid creating the GUI if a fully headless mode is desired. |

In the current implementation, annotated frames are written to the configured output video path after processing.

## Usage

From the project root:

```bash
python app/main.py
```

Or, if you are already inside the `app/` directory:

```bash
python main.py
```

Make sure the paths in `configs/config.yaml` are correct relative to your current working directory.

## Output

The application produces:

```text
output/movie.mp4
```

This output video contains:

- YOLO bounding boxes
- Class labels
- Confidence scores
- Estimated distance values
- Distance-based color coding
- Ground-zone visualization

It also writes logs:

```text
app.log
detections.log
```

`app.log` contains general application events and errors.  
`detections.log` contains detection-specific records, including class name, confidence, timestamp, and distance when available.

## How It Works

1. The application loads `configs/config.yaml`.
2. The GUI and worker threads are initialized.
3. `CaptureThread` opens the configured video source and emits frames.
4. `ProcessingThread` resizes frames to the configured target resolution.
5. The YOLO model runs inference on each frame.
6. Bounding boxes, labels, confidence values, distances, and warning zones are drawn.
7. Annotated frames are sent to the GUI when `app_type == 1`.
8. Annotated frames are written to the output video file.
9. When the video source ends, the capture thread emits a finish signal and the application closes.

## Distance Estimation

Distance is estimated from the normalized height of the detected bounding box using a polynomial equation. The estimated distance is approximate and depends on:

- Camera placement
- Camera height
- Object scale
- Bounding-box stability
- Perspective distortion
- Calibration quality
- Correct class detection

For `dump truck`, a fixed scale factor is applied in the current implementation.

## Warning-Zone Visualization

The ground-zone overlay is used to communicate approximate danger and warning areas in the image.

Default interpretation:

| Zone | Meaning |
|---|---|
| Red | Danger zone, typically below 5 meters |
| Yellow | Warning zone, typically 5 to 10 meters |
| Green | Safer detection, typically above 10 meters |

The visual zone should be treated as an approximate aid, not as a calibrated safety boundary unless the camera geometry has been properly calibrated.

## Keyboard Controls

When the GUI is active:

| Key | Action |
|---|---|
| `C` | Switch input source |
| `Q` | Close application |

The GUI also provides:

- **Switch Source** button
- **Close** button

## Notes on FPS and Video Duration

To keep the output video duration close to the original input video duration:

- Use the input video FPS for `VideoWriter`.
- Use `target_fps` only to control capture or processing rate.
- Do not write only low-FPS inference frames if the output video must preserve the original duration.

If the model performs better at 5 FPS but the input video is 30 FPS, a better architecture is:

```text
Input video FPS: 30
Model inference FPS: 5
Output video FPS: 30
```
# YOLO Object Detection and Distance Estimation

A PySide6/OpenCV application for detecting objects in video streams, estimating approximate object distance, drawing distance-based warning zones, and exporting an annotated output video.

The current project is configured for a custom YOLO11n model saved as `best.pt`, with the target classes:

- `person`
- `dump truck`

## Features

- Real-time object detection using Ultralytics YOLO
- PySide6 GUI for viewing annotated video frames
- OpenCV video capture from local video files, RTSP streams, or camera sources
- Approximate distance estimation from bounding-box height
- Distance-based visualization:
  - Red zone: danger range
  - Yellow zone: warning range
  - Green bounding boxes for safer detections
- Annotated video export
- General application logging
- Detection-specific logging
- Automatic window close when video input finishes

## Project Structure

```text
bsc-project/
├── app/
│   ├── main.py              # Main application entry point
│   ├── processor.py         # YOLO inference, annotation, video writing
│   ├── distance.py          # Distance estimation logic
│   ├── ground_zone.py       # Red/yellow ground-zone drawing
│   ├── logger.py            # Logging configuration
│   ├── capture.py           # Alternative capture-thread implementation
│   └── gui.py               # Alternative GUI implementation
├── configs/
│   └── config.yaml          # Runtime configuration
├── videos/
│   └── movie.mp4            # Example input video
├── output/
│   └── movie.mp4            # Annotated output video
├── best.pt                  # Custom YOLO11n model weights
├── requirements.txt
└── README.md
```

## Requirements

Recommended Python version:

```text
Python 3.10+
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Minimal `requirements.txt`:

```txt
numpy
opencv-python
torch
ultralytics
PySide6
PyYAML
```

> Note: For CUDA/GPU acceleration, install the correct PyTorch build for your CUDA version. The generic `torch` package may install a CPU-only build depending on your system and package index.

## Configuration

The application reads its settings from:

```text
configs/config.yaml
```

Current example:

```yaml
model_path: "best.pt"

camera_sources:
  # - "rtsp://admin:123456@192.168.1.188:554/ch01.264"
  # - "rtsp://admin:123456@192.168.1.189:554/ch01.264"
  - "videos/movie.mp4"

app_type: 1
target_fps: 5
log_level: "DEBUG"

classes:
  - "person"
  - "dump truck"

camera_height: 2
target_resolution: [640, 640]
output_path: "output/movie.mp4"
```

### Configuration Fields

| Field | Description |
|---|---|
| `model_path` | Path to the YOLO model weights. In this project, `best.pt` is a custom YOLO11n model. |
| `camera_sources` | Input sources. Can be a local video path, RTSP URL, or camera index. |
| `app_type` | Runtime mode. See [Application Modes](#application-modes). |
| `target_fps` | Capture/processing rate used by the capture thread. |
| `log_level` | Logging level, for example `DEBUG`, `INFO`, `WARNING`, or `ERROR`. |
| `classes` | Class names expected from the trained YOLO model. |
| `camera_height` | Camera height in meters, used by the ground-zone visualization logic. |
| `target_resolution` | Fixed frame size used before inference. Current default is `640x640`. |
| `output_path` | Path where the annotated output video is saved. |

## Application Modes

The code currently uses `app_type` to control how processed frames are handled.

| `app_type` | Behavior |
|---:|---|
| `0` | Print detection results to console and save annotated video. |
| `1` | Show annotated frames in the PySide6 GUI and save annotated video. |
| `2` | Intended for video-export-only workflows. This requires the main program to avoid creating the GUI if a fully headless mode is desired. |

In the current implementation, annotated frames are written to the configured output video path after processing.

## Usage

From the project root:

```bash
python app/main.py
```

Or, if you are already inside the `app/` directory:

```bash
python main.py
```

Make sure the paths in `configs/config.yaml` are correct relative to your current working directory.

## Output

The application produces:

```text
output/movie.mp4
```

This output video contains:

- YOLO bounding boxes
- Class labels
- Confidence scores
- Estimated distance values
- Distance-based color coding
- Ground-zone visualization

It also writes logs:

```text
app.log
detections.log
```

`app.log` contains general application events and errors.  
`detections.log` contains detection-specific records, including class name, confidence, timestamp, and distance when available.

## How It Works

1. The application loads `configs/config.yaml`.
2. The GUI and worker threads are initialized.
3. `CaptureThread` opens the configured video source and emits frames.
4. `ProcessingThread` resizes frames to the configured target resolution.
5. The YOLO model runs inference on each frame.
6. Bounding boxes, labels, confidence values, distances, and warning zones are drawn.
7. Annotated frames are sent to the GUI when `app_type == 1`.
8. Annotated frames are written to the output video file.
9. When the video source ends, the capture thread emits a finish signal and the application closes.

## Distance Estimation

Distance is estimated from the normalized height of the detected bounding box using a polynomial equation. The estimated distance is approximate and depends on:

- Camera placement
- Camera height
- Object scale
- Bounding-box stability
- Perspective distortion
- Calibration quality
- Correct class detection

For `dump truck`, a fixed scale factor is applied in the current implementation.

## Warning-Zone Visualization

The ground-zone overlay is used to communicate approximate danger and warning areas in the image.

Default interpretation:

| Zone | Meaning |
|---|---|
| Red | Danger zone, typically below 5 meters |
| Yellow | Warning zone, typically 5 to 10 meters |
| Green | Safer detection, typically above 10 meters |

The visual zone should be treated as an approximate aid, not as a calibrated safety boundary unless the camera geometry has been properly calibrated.

## Keyboard Controls

When the GUI is active:

| Key | Action |
|---|---|
| `C` | Switch input source |
| `Q` | Close application |

The GUI also provides:

- **Switch Source** button
- **Close** button

## Notes on FPS and Video Duration

To keep the output video duration close to the original input video duration:

- Use the input video FPS for `VideoWriter`.
- Use `target_fps` only to control capture or processing rate.
- Do not write only low-FPS inference frames if the output video must preserve the original duration.

If the model performs better at 5 FPS but the input video is 30 FPS, a better architecture is:

```text
Input video FPS: 30
Model inference FPS: 5
Output video FPS: 30
```

This means all frames should be written to the output video, while model inference can run only every N frames and reuse/smooth the latest detection results for intermediate frames.

## Limitations

- Distance estimation is approximate and not a substitute for calibrated depth measurement.
- Bounding-box jitter can cause distance and warning colors to fluctuate between frames.
- Detection failures can cause labels or zones to disappear unless smoothing or tracking is added.
- The current distance model depends heavily on the object bounding-box height.
- For production safety use, camera calibration, tracking, temporal smoothing, and validation on real-world data are required.

## Recommended Improvements

- Add object tracking to reduce bounding-box jitter.
- Add smoothing for centroid and distance values.
- Add hysteresis for red/yellow/green zone transitions.
- Separate model inference FPS from output video FPS.
- Add a true headless mode for `app_type == 2`.
- Add command-line arguments for config path and mode selection.
- Add validation for `config.yaml` fields.
- Check whether `VideoWriter.isOpened()` returns `True` before writing frames.
- Replace hardcoded output folder assumptions with path-safe directory creation.

## Troubleshooting

### The GUI opens but shows no frames

Check:

- `camera_sources` path is valid
- video file exists
- RTSP URL is reachable
- OpenCV can open the source
- `app_type` is set correctly

### Output video is too long or too short

Check that `VideoWriter` uses the input video FPS, not the model/capture FPS.

### Output video is empty or corrupted

Check:

- `output_path` folder exists
- codec is compatible with the file extension
- `VideoWriter.isOpened()` is `True`
- frame size matches `target_resolution`

### CUDA is not used

Check your PyTorch installation:

```python
import torch
print(torch.cuda.is_available())
```

If it prints `False`, install a CUDA-compatible PyTorch build.

## License

Add your project license here.

## Author

Add your name, university, supervisor, and project information here.

This means all frames should be written to the output video, while model inference can run only every N frames and reuse/smooth the latest detection results for intermediate frames.

## Limitations

- Distance estimation is approximate and not a substitute for calibrated depth measurement.
- Bounding-box jitter can cause distance and warning colors to fluctuate between frames.
- Detection failures can cause labels or zones to disappear unless smoothing or tracking is added.
- The current distance model depends heavily on the object bounding-box height.
- For production safety use, camera calibration, tracking, temporal smoothing, and validation on real-world data are required.

## Recommended Improvements

- Add object tracking to reduce bounding-box jitter.
- Add smoothing for centroid and distance values.
- Add hysteresis for red/yellow/green zone transitions.
- Separate model inference FPS from output video FPS.
- Add a true headless mode for `app_type == 2`.
- Add command-line arguments for config path and mode selection.
- Add validation for `config.yaml` fields.
- Check whether `VideoWriter.isOpened()` returns `True` before writing frames.
- Replace hardcoded output folder assumptions with path-safe directory creation.

## Troubleshooting

### The GUI opens but shows no frames

Check:

- `camera_sources` path is valid
- video file exists
- RTSP URL is reachable
- OpenCV can open the source
- `app_type` is set correctly

### Output video is too long or too short

Check that `VideoWriter` uses the input video FPS, not the model/capture FPS.

### Output video is empty or corrupted

Check:

- `output_path` folder exists
- codec is compatible with the file extension
- `VideoWriter.isOpened()` is `True`
- frame size matches `target_resolution`

### CUDA is not used

Check your PyTorch installation:

```python
import torch
print(torch.cuda.is_available())
```

If it prints `False`, install a CUDA-compatible PyTorch build.

## License

Add your project license here.

## Author

Add your name, university, supervisor, and project information here.
