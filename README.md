# AutoVision

Real-time computer vision system using YOLOv5 with webcam and screen capture capabilities, featuring automated actions based on object detection.

## Features

- Real-time object detection using YOLOv5
- Multiple video sources:
    - Webcam capture
    - Full screen capture
- Built-in automation actions:
    - Snapshot capture
    - Sound alerts
    - Desktop notifications
    - Event logging
- Modern dark-themed GUI
- Automation rules by object type
- Custom color highlights for different objects
- Extensible automation system

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/AutoVision.git
cd AutoVision
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download YOLOv5 model weights:
```bash
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Interface Guide:
    - Choose detection source (Webcam/Screen)
    - Select object type (person, car, dog, etc.)
    - Choose automation action
    - Click "Add Rule" to create detection rule

3. Available Actions:
    - `snapshot`: Saves detection images
    - `sound`: Plays alert sound
    - `notify`: Shows Windows notification
    - `log`: Records detection events
    - `highlight`: Custom colored boxes per object

4. Object Types:
    - person
    - car
    - dog
    - cat
    - bottle
    - chair
    (and more from YOLOv5 model)

## Custom Automations

You can create your own automation scripts by adding Python files to the `automations` directory. Each script should contain a `run` function with the following signature:

```python
def run(detected_object, frame, confidence, **kwargs):
    """
    Args:
        detected_object (str): Name of the detected object
        frame (numpy.ndarray): The current video frame
        confidence (float): Detection confidence score
        **kwargs: Additional arguments including:
                 - coords: [x1, y1, x2, y2] of detection box
                 - manager: AutomationManager instance
    Returns:
        bool: True if successful
    """
```

Example scripts are provided in the automations directory. Your custom automations will automatically appear in the actions dropdown menu.

## Performance

- Achieves 30 FPS processing on 1080p video
- Real-time object detection and automation
- Low-latency response to detections

## Requirements

- Python 3.8+
- PyQt5
- OpenCV
- PyTorch
- YOLOv5
- See requirements.txt for full list

## Project Structure

```
AutoVision/
├── main.py              # Main application
├── automations/         # Automation scripts
│   ├── example.py      # Example automation
│   └── highlight.py    # Custom highlighting
├── sounds/              # Alert sound files
└── automation_output/   # Generated on runtime
    ├── snapshots/      
    └── logs/           
```

## Note

The automation_output directory is created automatically when running the application. Make sure you have appropriate permissions in the project directory.
