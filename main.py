import sys
import os
import json
import time
import warnings
import threading
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QLabel, 
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QFrame,
    QStyleFactory
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPalette, QColor, QFont

import cv2
import torch
import numpy as np
import mss
import PIL.ImageGrab

QApplication.setStyle(QStyleFactory.create('Fusion'))

dark_palette = QPalette()
dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

STYLE_SHEET = """
QMainWindow {
    background-color: #2b2b2b;
}
QLabel {
    color: #ffffff;
    font-size: 14px;
    font-weight: normal;
}
QPushButton {
    background-color: #0d47a1;
    border: none;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1565c0;
}
QPushButton:pressed {
    background-color: #0a3d91;
}
QComboBox {
    background-color: #424242;
    border: 1px solid #555555;
    border-radius: 4px;
    color: white;
    padding: 6px;
    min-width: 150px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox::down-arrow {
    image: none;
    border: none;
}
QRadioButton {
    color: white;
    font-size: 14px;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QFrame#line {
    color: #555555;
}
"""

try:
    from playsound import playsound
    from win10toast import ToastNotifier
    AUTOMATION_AVAILABLE = True
except ImportError:
    print("Warning: playsound and/or win10toast not installed. Some automation features will be disabled.")
    print("To enable all features, run: pip install playsound win10toast")
    AUTOMATION_AVAILABLE = False

warnings.filterwarnings('ignore', category=FutureWarning, message='.*torch.cuda.amp.autocast.*')

class AutomationManager:
    def __init__(self):
        self.output_dir = Path("automation_output")
        self.output_dir.mkdir(exist_ok=True)
        
        self.snapshots_dir = self.output_dir / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
        
        self.logs_dir = self.output_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.automations_dir = Path("automations")
        self.automations_dir.mkdir(exist_ok=True)
        
        if not any(self.automations_dir.iterdir()):
            self.create_example_automation()
        
        self.custom_automations = self.load_custom_automations()
        
        self.toaster = ToastNotifier() if AUTOMATION_AVAILABLE else None
        
        self.last_execution = {}

    def create_example_automation(self):
        example_code = ''
        
        with open(self.automations_dir / "example_automation.py", 'w') as f:
            f.write(example_code)
            
    def load_custom_automations(self):
        """Load all custom automation scripts from the automations directory."""
        custom_automations = {}
        
        for script_path in self.automations_dir.glob("*.py"):
            if script_path.name.startswith("__"):
                continue
                
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    script_path.stem, script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'run'):
                    custom_automations[script_path.stem] = module.run
                    print(f"Loaded custom automation: {script_path.stem}")
                    
            except Exception as e:
                print(f"Error loading automation {script_path.name}: {str(e)}")
                
        return custom_automations
        
        self.last_execution = {}
        
    def execute_action(self, action_type, detected_object, frame=None, confidence=None, **kwargs):
        current_time = time.time()
        
        action_key = f"{detected_object}_{action_type}"
        if action_key in self.last_execution:
            if current_time - self.last_execution[action_key] < 5:
                return
        
        self.last_execution[action_key] = current_time
        
        if action_type in self.custom_automations:
            try:
                self.custom_automations[action_type](
                    detected_object, 
                    frame, 
                    confidence, 
                    manager=self,
                    **kwargs
                )
                return
            except Exception as e:
                print(f"Error executing custom automation {action_type}: {str(e)}")
                return
        
        if action_type == "snapshot":
            self._save_snapshot(detected_object, frame)
        elif action_type == "sound":
            self._play_sound(detected_object)
        elif action_type == "notify":
            self._send_notification(detected_object, confidence)
        elif action_type == "log":
            self._log_detection(detected_object, confidence)
            
    def _save_snapshot(self, detected_object, frame):
        if frame is None:
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{detected_object}_{timestamp}.jpg"
        cv2.imwrite(str(self.snapshots_dir / filename), frame)
        
    def _play_sound(self, detected_object):
        if not AUTOMATION_AVAILABLE:
            print("Sound feature not available. Please install playsound package.")
            return
            
        sound_file = f"sounds/{detected_object}_alert.mp3"
        if os.path.exists(sound_file):
            threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()
            
    def _send_notification(self, detected_object, confidence):
        if not AUTOMATION_AVAILABLE:
            print("Notification feature not available. Please install win10toast package.")
            return
            
        message = f"Detected {detected_object} with {confidence:.2f}% confidence"
        self.toaster.show_toast("AutoVision Alert", message, duration=3, threaded=True)
        
    def _log_detection(self, detected_object, confidence, additional_data=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "object": detected_object,
            "confidence": confidence
        }
        
        if additional_data:
            log_entry.update(additional_data)
        
        log_file = self.logs_dir / f"detections_{datetime.now().strftime('%Y%m%d')}.json"
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
            
        logs.append(log_entry)
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

class AutoVisionGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoVision")
        self.setGeometry(100, 100, 1600, 900)
        
        self.setStyleSheet(STYLE_SHEET)
        
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor('#2b2b2b'))
        self.setPalette(p)  # Increased window size

        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
        self.model.conf = 0.5  # Confidence threshold
        
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]  # Primary monitor
        
        self.source = "webcam"  # Default to webcam
        self.cap = None
        self.init_capture()

        self.automation_manager = AutomationManager()
        self.automation_rules = {}

        self.setup_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)  # ~30 FPS
        
    def init_capture(self):
        if self.cap is not None:
            self.cap.release()
            
        if self.source == "webcam":
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        else:
            pass

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        source_layout = QHBoxLayout()
        source_label = QLabel("Source:")
        source_layout.addWidget(source_label)
        
        self.webcam_radio = QRadioButton("Webcam")
        self.screen_radio = QRadioButton("Screen")
        self.webcam_radio.setChecked(True)
        
        self.source_group = QButtonGroup()
        self.source_group.addButton(self.webcam_radio)
        self.source_group.addButton(self.screen_radio)
        self.source_group.buttonClicked.connect(self.source_changed)
        
        source_layout.addWidget(self.webcam_radio)
        source_layout.addWidget(self.screen_radio)
        source_layout.addStretch()
        
        layout.addLayout(source_layout)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(1280, 720)  # Set minimum size for video display
        layout.addWidget(self.video_label)

        controls_layout = QHBoxLayout()

        object_layout = QVBoxLayout()
        object_label = QLabel("Select Object:")
        self.object_combo = QComboBox()
        self.object_combo.addItems(['person', 'car', 'dog', 'cat', 'bottle', 'chair'])
        object_layout.addWidget(object_label)
        object_layout.addWidget(self.object_combo)
        controls_layout.addLayout(object_layout)

        action_layout = QVBoxLayout()
        action_label = QLabel("Select Action:")
        self.action_combo = QComboBox()

        actions = ['snapshot', 'sound', 'notify', 'log'] + list(self.automation_manager.custom_automations.keys())
        self.action_combo.addItems(actions)
        action_layout.addWidget(action_label)
        action_layout.addWidget(self.action_combo)
        controls_layout.addLayout(action_layout)

        button_layout = QVBoxLayout()
        button_layout.addWidget(QLabel(""))  # Spacing to align with other widgets
        add_rule_btn = QPushButton("Add Automation Rule")
        add_rule_btn.clicked.connect(self.add_automation_rule)
        button_layout.addWidget(add_rule_btn)
        controls_layout.addLayout(button_layout)

        self.rules_label = QLabel("Active Rules: None")
        controls_layout.addWidget(self.rules_label)

        layout.addLayout(controls_layout)

        self.stats_label = QLabel("FPS: 0 | Latency: 0ms")
        layout.addWidget(self.stats_label)

    def add_automation_rule(self):
        object_class = self.object_combo.currentText()
        action = self.action_combo.currentText()
        
        if object_class not in self.automation_rules:
            self.automation_rules[object_class] = []
            
        if action not in self.automation_rules[object_class]:
            self.automation_rules[object_class].append(action)
            
        self.update_rules_display()
        
    def update_rules_display(self):
        if not self.automation_rules:
            self.rules_label.setText("Active Rules: None")
            return
            
        rules_text = "Active Rules:\n"
        for obj, actions in self.automation_rules.items():
            rules_text += f"{obj}: {', '.join(actions)}\n"
        self.rules_label.setText(rules_text)

    def source_changed(self, button):
        self.source = "webcam" if button == self.webcam_radio else "screen"
        self.init_capture()

    def get_frame(self):
        if self.source == "webcam":
            ret, frame = self.cap.read()
            if not ret:
                return None
            return frame
        else:
            screen = np.array(PIL.ImageGrab.grab())
            return cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    def update_frame(self):
        start_time = cv2.getTickCount()
        
        frame = self.get_frame()
        if frame is None:
            return

        results = self.model(frame)
        
        for det in results.xyxy[0]:
            x1, y1, x2, y2, conf, cls = det.tolist()
            label = results.names[int(cls)]
            
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (int(x1), int(y1-10)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            if label in self.automation_rules:
                self.execute_action(label, frame, conf, coords=det.tolist())

        end_time = cv2.getTickCount()
        processing_time = (end_time - start_time) / cv2.getTickFrequency()
        fps = 1 / processing_time
        latency = processing_time * 1000

        self.stats_label.setText(f"FPS: {fps:.1f} | Latency: {latency:.1f}ms")

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        qt_image = QImage(rgb_frame.data, w, h, w * ch, QImage.Format_RGB888)
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            1280, 720,  # Fixed size for consistent display
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation  # Added smooth scaling
        )
        self.video_label.setPixmap(scaled_pixmap)

    def execute_action(self, detected_object, frame, confidence, coords=None):
        if detected_object not in self.automation_rules:
            return
            
        for action in self.automation_rules[detected_object]:
            self.automation_manager.execute_action(action, detected_object, frame, confidence, coords=coords)

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    app.setPalette(dark_palette)
    app.setStyle('Fusion')
    
    window = AutoVisionGUI()
    window.show()
    sys.exit(app.exec_())