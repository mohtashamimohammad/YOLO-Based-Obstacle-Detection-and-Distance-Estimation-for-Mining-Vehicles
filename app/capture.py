import cv2
import time
import numpy as np
from PySide6.QtCore import QThread, Signal
from logger import setup_logging

class CaptureThread(QThread):
    frame_captured = Signal(np.ndarray)

    def __init__(self, camera_sources, target_fps=5):
        super().__init__()
        self.logger, _ = setup_logging()
        self.running = False
        self.current_source_index = 0
        # Limit to maximum two sources
        self.sources = camera_sources[:2] if camera_sources else ["0"]
        if len(self.sources) > 2:
            self.logger.warning(f"More than two camera sources provided. Using only the first two: {self.sources[:2]}")
            self.sources = self.sources[:2]
        self.cap = None
        self.target_fps = target_fps
        self.logger.info(f"CaptureThread initialized with sources: {self.sources} and target_fps={self.target_fps}")

    def run(self):
        self.running = True
        retry_count = 0
        while self.running:
            try:
                if not self.cap or not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(self.sources[self.current_source_index])
                    if not self.cap.isOpened():
                        retry_count += 1
                        if retry_count >= 3:
                            self.logger.error(f"Failed to open source {self.sources[self.current_source_index]} after 3 attempts.")
                            if len(self.sources) > 1:
                                self.current_source_index = (self.current_source_index + 1) % len(self.sources)
                                retry_count = 0
                            else:
                                self.logger.error("No more sources available. Stopping CaptureThread.")
                                self.running = False
                                break
                        self.logger.warning(f"Failed to open source: {self.sources[self.current_source_index]}. Retrying ({retry_count}/3)...")
                        time.sleep(1)
                        continue
                    self.logger.info(f"Opened source: {self.sources[self.current_source_index]}")
                    retry_count = 0

                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.logger.warning(f"Failed to capture frame from {self.sources[self.current_source_index]}")
                    self.cap.release()
                    retry_count += 1
                    if retry_count >= 3:
                        self.logger.error(f"Failed to capture frame after 3 attempts. Switching to next source or stopping.")
                        if len(self.sources) > 1:
                            self.current_source_index = (self.current_source_index + 1) % len(self.sources)
                            retry_count = 0
                        else:
                            self.logger.error("No more sources available. Stopping CaptureThread.")
                            self.running = False
                            break
                    time.sleep(0.1)
                    continue

                self.frame_captured.emit(frame)
                time.sleep(1 / self.target_fps)  # Adjust sleep based on target FPS

            except Exception as e:
                self.logger.error(f"Error in CaptureThread: {e}")
                if self.cap:
                    self.cap.release()
                retry_count += 1
                if retry_count >= 3:
                    if len(self.sources) > 1:
                        self.current_source_index = (self.current_source_index + 1) % len(self.sources)
                        retry_count = 0
                    else:
                        self.logger.error("No more sources available. Stopping CaptureThread.")
                        self.running = False
                        break
                time.sleep(1)

        if self.cap:
            self.cap.release()
            self.logger.info("Capture device released")

    def set_source(self, index):
        if 0 <= index < len(self.sources):
            self.current_source_index = index
            if self.cap:
                self.cap.release()
            self.cap = cv2.VideoCapture(self.sources[self.current_source_index])
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open new source: {self.sources[self.current_source_index]}")
            else:
                self.logger.info(f"Switched to source: {self.sources[self.current_source_index]}")
        else:
            self.logger.warning(f"Invalid source index: {index}")

    def stop(self):
        self.running = False
        self.wait()
        self.logger.info("CaptureThread stopped")