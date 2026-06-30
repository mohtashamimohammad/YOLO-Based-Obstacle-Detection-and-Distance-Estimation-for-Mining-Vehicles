import sys
import yaml
import cv2
import time
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from logger import setup_logging
from processor import ProcessingThread

class CaptureThread(QThread):
    frame_captured = Signal(np.ndarray)
    change_source = Signal()
    video_finished = Signal()
    
    def __init__(self, camera_sources, target_fps):
        super().__init__()
        self.logger, _ = setup_logging()
        self.camera_sources = camera_sources
        self.target_fps = target_fps
        self.cap = None
        self.current_source_index = 0
        self.running = False
        self.frame_interval = 1.0 / target_fps if target_fps > 0 else 0.2  # Default to 5 FPS
    def run(self):
        self.running = True
        while self.running:
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_sources[self.current_source_index])
                if self.cap.isOpened():
                    self.logger.info(f"Capture opened for source: {self.camera_sources[self.current_source_index]}")
                else:
                    self.logger.error(f"Failed to open camera source: {self.camera_sources[self.current_source_index]}")
                    self.running = False
                    break

            start_time = time.time()
            ret, frame = self.cap.read()
            if ret:
                self.frame_captured.emit(frame)
            else:
                
                self.logger.warning(f"Failed to capture frame from source: {self.camera_sources[self.current_source_index]}")
                self.logger.info("Video finished")
                self.video_finished.emit()
                self.running = False
                break

            # Control frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, self.frame_interval - elapsed)
            time.sleep(sleep_time)

        if self.cap:
            self.cap.release()
            self.logger.info("Capture device released")

    @Slot()
    def switch_source(self):
        if self.cap:
            self.cap.release()
        self.current_source_index = (self.current_source_index + 1) % len(self.camera_sources)
        self.logger.info(f"Switching to source: {self.camera_sources[self.current_source_index]}")

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.quit()
        self.wait()
        self.logger.info("CaptureThread stopped")

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.logger, _ = setup_logging()
        self.setWindowTitle("Object Detection and Distance Estimation")
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Image label
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.image_label)

        # Buttons
        self.switch_button = QPushButton("Switch Source", self)
        self.switch_button.clicked.connect(self.switch_source)
        layout.addWidget(self.switch_button)

        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)

        input_fps = self.get_input_fps(config["camera_sources"][0])

        self.capture_thread = CaptureThread(config["camera_sources"], config["target_fps"])
        self.processing_thread = ProcessingThread(
            model_path=config["model_path"],
            app_type=config["app_type"],
            config=config,
            classes=config["classes"],
            camera_height=config.get("camera_height", 1.5),
            target_resolution=tuple(config["target_resolution"]),
            input_fps=input_fps
        )

        self.capture_thread.frame_captured.connect(self.processing_thread.process_frame)
        self.capture_thread.video_finished.connect(self.close)
        self.processing_thread.frame_processed.connect(self.update_image)
        self.switch_button.setEnabled(len(self.capture_thread.camera_sources) > 1)
        self.capture_thread.start()
        self.processing_thread.start()
        
    def get_input_fps(self, source):
        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            self.logger.warning(f"Could not open source to read FPS: {source}")
            return 30

        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        if fps is None or fps <= 0:
            self.logger.warning("Invalid input FPS detected. Falling back to 30 FPS.")
            return 5

        return fps
    @Slot(np.ndarray)
    def update_image(self, frame):
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.logger.debug(f"Image updated in GUI")
        except Exception as e:
            self.logger.error(f"Error updating image in GUI: {e}")

    @Slot()
    def switch_source(self):
        self.capture_thread.switch_source()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C:
            self.switch_source()
        elif event.key() == Qt.Key_Q:
            self.close()

    def closeEvent(self, event):
        self.logger.info("Closing application")
        self.capture_thread.stop()
        self.processing_thread.stop()
        event.accept()

def main():
    logger, _ = setup_logging()
    try:
        with open("configs/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded config from configs/config.yaml")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return

    app = QApplication(sys.argv)
    window = MainWindow(config)
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()