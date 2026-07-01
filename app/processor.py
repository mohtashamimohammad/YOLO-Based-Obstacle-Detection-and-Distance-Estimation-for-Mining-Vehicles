import cv2
import numpy as np
import torch
from ultralytics import YOLO
from PySide6.QtCore import QThread, Signal, Slot
from datetime import datetime
from logger import setup_logging
from distance import DistanceCalculator
from ground_zone import GroundZone
import time
import os 

class ProcessingThread(QThread):
    frame_processed = Signal(np.ndarray)

    def __init__(self, model_path, app_type, config , classes=None, camera_height=1.5, target_resolution=(640, 640) ,input_fps=None):
        super().__init__()
        self.logger, self.detections_logger = setup_logging()
        self.model_path = model_path
        self.app_type = app_type
        self.classes = classes or ["person", "dump truck"]
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.distance_calculator = DistanceCalculator(classes=self.classes)
        self.ground_zone = GroundZone(camera_height=camera_height)  # Pass camera_height explicitly
        self.current_results = None
        self.target_resolution = target_resolution
        self.logger.info(f"Using device: {self.device}, Target resolution: {self.target_resolution}")
        self.input_fps = input_fps
        self.video_writer =None
        self.output_video_path = config["output_path"]
        if not os.path.exists("output"):
            os.makedirs("output")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer =  cv2.VideoWriter(self.output_video_path, fourcc, self.input_fps, (self.target_resolution[0] ,self.target_resolution[1]))
    def run(self):
        try:
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            if self.device == "cuda":
                self.model.model.half()
                self.logger.info("YOLO model set to half-precision for GPU")
            else:
                torch.set_num_threads(4)
                self.logger.info("YOLO model using 4 CPU threads")
        except Exception as e:
            self.logger.error(f"Failed to initialize YOLO model: {e}")
            return
        self.exec()

    @Slot(np.ndarray)
    def process_frame(self, frame):
        try:
            start_time = time.time()
            # Resize frame to 640x640
            frame = cv2.resize(frame, self.target_resolution, interpolation=cv2.INTER_LINEAR)
            self.current_results = self.model(frame, verbose=False)
            annotated_frame = self.draw_results(frame)
            if self.app_type == 0:
                self.print_detections(self.current_results, frame)
            elif self.app_type ==1 :
                self.frame_processed.emit(annotated_frame)
            self.video_writer.write(annotated_frame)
            self.logger.debug(f"Frame processed in {time.time() - start_time:.3f} seconds")
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            if self.app_type == 1:
                self.frame_processed.emit(frame)

    def print_detections(self, results, frame):
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    label_index = int(box.cls[0])
                    label_name = self.classes[label_index] if label_index < len(self.classes) else "Unknown"
                    confidence = float(box.conf[0])
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    log_message = f"Detection: ClassID={label_index}, ClassName={label_name}, Confidence={confidence:.2f}, Timestamp={timestamp}"
                    
                    distance, _ = self.distance_calculator.calculate_object_distance(
                        box, image_width=self.target_resolution[0], image_height=self.target_resolution[1], class_name=label_name
                    )
                    if distance is not None:
                        log_message += f", Distance={distance:.2f} m"
                    
                    print(log_message)
                    self.detections_logger.info(log_message)

    def draw_results(self, frame):
        try:
            image_width, image_height = self.target_resolution
            frame = self.ground_zone.draw_ground_zone(frame)

            for result in self.current_results:
                if result.boxes is not None:
                    for box in result.boxes:
                        if box.xyxy is not None and box.xyxy[0] is not None:
                            try:
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                            except (TypeError, ValueError) as e:
                                self.logger.error(f"Invalid bounding box data for box: {box}. Error: {e}")
                                continue
                        label_index = int(box.cls[0])
                        label_name = self.classes[label_index] if label_index < len(self.classes) else "Unknown"
                        confidence = float(box.conf[0])
                        label = f"{label_name} {confidence:.2f}"

                        distance, centroid = self.distance_calculator.calculate_object_distance(
                            box, image_width=image_width, image_height=image_height, class_name=label_name
                        )
                        self.logger.debug(f"Distance: {distance}, Centroid: {centroid}")
                        if distance is not None and centroid is not None:
                            label += f", {distance:.2f} m"
                            cv2.putText(
                                frame,
                                f"{distance:.2f} m",
                                (int(centroid[0]), int(centroid[1]) - 20),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                (255, 0, 0),
                                2,
                            )
                            # Determine color based on distance
                            if distance < 5:
                                box_color = (0, 0, 255)  # Red
                                text_color = (0, 0, 255)  # Red
                            elif 5 <= distance <= 10:
                                box_color = (0, 255, 255)  # Yellow
                                text_color = (0, 255, 255)  # Yellow
                            else:
                                box_color = (0, 255, 0)  # Green (default)
                                text_color = (0, 255, 0)  # Green (default)

                            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                            cv2.putText(
                                frame,
                                label,
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                text_color,
                                2,
                            )
                        self.detections_logger.info(
                            f"Detection: ClassID={label_index}, ClassName={label_name}, "
                            f"Confidence={confidence:.2f}, Timestamp={datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}"
                        )
                    else:
                        self.logger.warning(f"Skipping box with invalid xyxy data: {box}")
                        continue
            return frame
        except Exception as e:
            self.logger.error(f"Error drawing results: {e}")
            return frame

    def stop(self):
        self.quit()
        self.wait()
        if self.video_writer is not None : 
            self.video_writer.release()
            self.video_writer = None
        self.logger.info("ProcessingThread terminated")