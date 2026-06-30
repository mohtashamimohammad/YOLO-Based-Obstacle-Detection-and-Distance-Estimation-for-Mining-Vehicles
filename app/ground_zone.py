import cv2
import numpy as np
from logger import setup_logging

class GroundZone:
    def __init__(self, camera_height=1.5, red_distance=5, yellow_distance=10):
        """
        Initialize the GroundZone for drawing distance-based zones.

        Args:
            camera_height (float): Camera height in meters (adjusts perspective).
            red_distance (float): Distance threshold for red zone in meters.
            yellow_distance (float): Distance threshold for yellow zone in meters.
        """
        self.logger, _ = setup_logging()
        self.camera_height = camera_height
        self.red_distance = red_distance
        self.yellow_distance = yellow_distance
        self.logger.info(f"GroundZone initialized with camera_height={camera_height}, red_distance={red_distance}, yellow_distance={yellow_distance}")

    def draw_ground_zone(self, frame, distance, centroid=None):
        """
        Draw colored zones on the frame as trapezoids with aligned side lines for perspective.

        Args:
            frame (np.ndarray): Input frame to draw on.
            distance (float or dict): Distance to the object in meters or a dict containing 'distance' and optionally 'centroid'.
            centroid (tuple, optional): Centroid coordinates (x, y) to draw a point, if provided.

        Returns:
            np.ndarray: Frame with drawn zones.
        """
        try:
            # Handle dictionary input
            if isinstance(distance, dict):
                centroid = distance.get('centroid')
                distance = distance.get('distance', 0.0)
                self.logger.debug(f"Extracted distance: {distance}, centroid: {centroid}")
            elif not isinstance(distance, (int, float)):
                raise ValueError(f"Expected distance to be a float or int, got {type(distance)}")

            height, width = frame.shape[:2]

            # Calculate heights for red and yellow zones based on camera_height
            red_height = int(height * 0.1 * self.camera_height)
            yellow_height = int(height * 0.2 * self.camera_height)

            # Define trapezoid points for perspective effect
            bottom_width = width
            red_top_width = int(width * 0.6)
            yellow_top_width = int(width * 0.3)
            scale = yellow_height / red_height
            red_top_x = (width - red_top_width) // 2
            yellow_top_x = red_top_x*scale #(width - yellow_top_width) // 2
            yellow_top_right_x = int(width - red_top_x * scale)
            yellow_top_width = yellow_top_right_x - yellow_top_x
            yellow_bottom_x = red_top_x
            yellow_bottom_width = red_top_width

            # Red zone points (0 to 5 meters)
            red_points = [
                (red_top_x, height - red_height),
                (red_top_x + red_top_width, height - red_height),
                (width, height),
                (0, height)
            ]
            red_points = np.array(red_points, np.int32)

            # Yellow zone points (5 to 10 meters)
            yellow_points = [
                (yellow_top_x, height - yellow_height),
    (yellow_top_x + yellow_top_width, height - yellow_height),
    (yellow_bottom_x + yellow_bottom_width, height - red_height),
    (yellow_bottom_x, height - red_height)
            ]
            yellow_points = np.array(yellow_points, np.int32)

            # Draw zones as hollow trapezoids
            cv2.polylines(frame, [yellow_points], isClosed=True, color=(0, 255, 255), thickness=2)  # Yellow
            cv2.polylines(frame, [red_points], isClosed=True, color=(0, 0, 255), thickness=2)  # Red

            # Draw centroid point if provided
            if centroid:
                centroid_x, centroid_y = centroid
                cv2.circle(frame, (int(centroid_x), int(centroid_y)), 5, (0, 255, 0), -1)
                self.logger.debug(f"Centroid drawn at ({centroid_x}, {centroid_y})")

            return frame
        except Exception as e:
            self.logger.error(f"Error drawing ground zone: {e}")
            return frame