from PySide6.QtWidgets import QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QSizePolicy, QStatusBar
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QImage, QPixmap, QKeyEvent
from capture import CaptureThread
from processor import ProcessingThread
from logger import setup_logging
import cv2
import time
import numpy as np 

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.logger, _ = setup_logging(config.get("log_level", "DEBUG"))
        self.config = config
        self.app_type = config.get("app_type", 1)
        self.logger.info(f"App type: {self.app_type}")

        if self.app_type == 1:
            self.setWindowTitle("YOLO Object Detection GUI")
            self.setGeometry(100, 100, 800, 600)
            self.setFocusPolicy(Qt.StrongFocus)

            self.image_label = QLabel(self)
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.image_label.setMinimumSize(100, 100)
            self.image_label.setFocusPolicy(Qt.NoFocus)

            self.switch_button = QPushButton("Switch Source", self)
            self.switch_button.clicked.connect(self.switch_source)
            self.switch_button.setFocusPolicy(Qt.NoFocus)

            self.close_button = QPushButton("Close", self)
            self.close_button.clicked.connect(self.close)
            self.close_button.setFocusPolicy(Qt.NoFocus)

            layout = QVBoxLayout()
            layout.addWidget(self.image_label)
            layout.addWidget(self.switch_button)
            layout.addWidget(self.close_button)
            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)

            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.status_bar.showMessage("Initializing...")

        self.capture_thread = CaptureThread(config.get("camera_sources", ["0"]))
        self.processing_thread = ProcessingThread(
            config.get("model_path", "best.pt"),
            self.app_type,
            config,
            config.get("classes", ["person", "dump truck"])
        )

        if self.app_type == 1:
            self.capture_thread.frame_captured.connect(self.processing_thread.process_frame)
            self.processing_thread.frame_processed.connect(self.update_image)
            self.switch_button.setEnabled(len(self.capture_thread.sources) > 1)
            if len(self.capture_thread.sources) <= 1:
                self.logger.warning("Only one source available; switch button disabled")
            self.setFocus()

        self.capture_thread.start()
        self.processing_thread.start()
        self.logger.info("Threads started")

    @Slot(np.ndarray)
    def update_image(self, frame):
        try:
            start_time = time.time()
            if frame is None:
                self.logger.warning("Received None frame")
                self.status_bar.showMessage("Error: No frame received")
                return
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, c = frame_rgb.shape
            bytes_per_line = c * w
            image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.FastTransformation))
            self.status_bar.showMessage("Source: " + str(self.capture_thread.sources[self.capture_thread.current_source_index]))
            self.logger.debug(f"Image updated in GUI in {time.time() - start_time:.3f} seconds")
        except Exception as e:
            self.logger.error(f"Error updating image: {e}")

    def switch_source(self):
        if len(self.capture_thread.sources) > 1:
            next_index = (self.capture_thread.current_source_index + 1) % len(self.capture_thread.sources)
            self.capture_thread.set_source(next_index)
            self.logger.info(f"Switched to source index {next_index}: {self.capture_thread.sources[next_index]}")
        else:
            self.logger.warning("Cannot switch: Only one source available")

    def keyPressEvent(self, event: QKeyEvent):
        if self.app_type == 1:
            self.logger.debug(f"Key pressed: {event.key()} (Qt.Key_Q={Qt.Key_Q}, Qt.Key_C={Qt.Key_C})")
            if event.key() == Qt.Key_Q:
                self.logger.info("Q key pressed, closing application")
                self.close()
            elif event.key() == Qt.Key_C:
                self.logger.info("C key pressed, switching source")
                self.switch_source()
            event.accept()

    def closeEvent(self, event):
        self.logger.info("Closing application")
        self.capture_thread.stop()
        self.processing_thread.stop()
        event.accept()