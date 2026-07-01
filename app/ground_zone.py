import cv2
import numpy as np
from logger import setup_logging


class GroundZone:
    def __init__(self, camera_height=1.5, red_distance=5, yellow_distance=10):
        self.logger, _ = setup_logging()
        self.camera_height = camera_height
        self.red_distance = red_distance
        self.yellow_distance = yellow_distance

        self.yellow_color = (0, 255, 255)
        self.red_color = (0, 0, 255)
        self.green_color = (0, 255, 0)

        self.line_thickness = 2
        self.draw_fill = False
        self.fill_alpha = 0.12
        self.draw_centroid_point = True

        self.points_ratio = [
            (0.40, 0.73),
            (0.62, 0.73),
            (0.78, 0.86),
            (0.24, 0.86),
            (0.95, 1.00),
            (0.05, 1.00),
        ]

    def _scale_points(self, frame):
        height, width = frame.shape[:2]
        points = []
        for x_ratio, y_ratio in self.points_ratio:
            x = int(x_ratio * width)
            y = int(y_ratio * height)
            points.append((x, y))
        return points

    def _draw_zone(self, frame, points, color):
        polygon = np.array(points, dtype=np.int32)

        if self.draw_fill:
            overlay = frame.copy()
            cv2.fillPoly(overlay, [polygon], color)
            cv2.addWeighted(overlay, self.fill_alpha, frame, 1 - self.fill_alpha, 0, frame)

        cv2.polylines(
            frame,
            [polygon],
            isClosed=True,
            color=color,
            thickness=self.line_thickness,
            lineType=cv2.LINE_AA,
        )

        return frame

    def draw_centroid(self, frame, centroid):
        if centroid is None or not self.draw_centroid_point:
            return frame

        try:
            cx, cy = centroid
            cv2.circle(
                frame,
                (int(cx), int(cy)),
                5,
                self.green_color,
                -1,
                lineType=cv2.LINE_AA,
            )
        except Exception as e:
            self.logger.error(f"Error drawing centroid: {e}")

        return frame

    def draw_ground_zone(self, frame, distance=None, centroid=None):
        try:
            if frame is None or not isinstance(frame, np.ndarray):
                return frame

            points = self._scale_points(frame)
            if len(points) < 6:
                return frame

            p0, p1, p2, p3, p4, p5 = points

            yellow_points = [p0, p1, p2, p3]
            red_points = [p3, p2, p4, p5]

            frame = self._draw_zone(frame, yellow_points, self.yellow_color)
            frame = self._draw_zone(frame, red_points, self.red_color)

            if centroid is not None:
                frame = self.draw_centroid(frame, centroid)

            return frame

        except Exception as e:
            self.logger.error(f"Error drawing ground zone: {e}")
            return frame