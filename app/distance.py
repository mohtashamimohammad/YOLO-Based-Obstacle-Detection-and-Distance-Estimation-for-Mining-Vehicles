import numpy as np
from logger import setup_logging

class DistanceCalculator:
    def __init__(self, classes=None):
        """
        Initialize the DistanceCalculator with polynomial equation for distance calculation.

        Args:
            classes (list): List of class names (e.g., ["person", "dump truck"]).
        """
        self.logger, _ = setup_logging()
        self.classes = classes or ["person", "dump truck"]
        self.scale_factor_dump_truck = 2.493  # Fixed scale factor for Dump Truck
        self.logger.info(f"DistanceCalculator initialized with scale_factor_dump_truck={self.scale_factor_dump_truck}")

    def calculate_object_distance(self, box, image_width=640, image_height=640, class_name="dump truck"):
        """
        Calculate the distance of a single object using a polynomial equation based on height.

        Args:
            box: YOLO bounding box object with xyxy coordinates.
            image_width (int): Width of the frame (fixed at 640).
            image_height (int): Height of the frame (fixed at 640).
            class_name (str): Class name of the bounding box ("person" or "dump truck").

        Returns:
            tuple: (distance in meters, centroid) or (None, None) if calculation fails.
        """
        try:
            # Extract and validate bounding box features
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
            height = (y2 - y1) / image_height  # Normalized height

            # Validate height
            if not (0 < height <= 1):
                self.logger.warning(f"Invalid normalized height for {class_name}: {height}")
                return None, None

            # Polynomial equation for distance
            # y = 37.5960 - 360.0588*height + 1528.6452*height^2 - 3144.1884*height^3 + 3060.1623*height^4 - 1125.4166*height^5
            distance_meters = (
                37.5960
                - 360.0588 * height
                + 1528.6452 * height**2
                - 3144.1884 * height**3
                + 3060.1623 * height**4
                - 1125.4166 * height**5
            )

            # Apply fixed scale factor for Dump Truck
            if class_name == "dump truck":
                distance_meters *= self.scale_factor_dump_truck

            # Validate distance
            if distance_meters < 0 or distance_meters > 100:
                self.logger.warning(f"Unrealistic distance predicted: {distance_meters} meters for {class_name}")
                return None, None

            self.logger.info(f"Distance for {class_name}: {distance_meters:.2f} meters")
            return distance_meters, centroid

        except Exception as e:
            self.logger.error(f"Error calculating distance for {class_name}: {e}")
            return None, None