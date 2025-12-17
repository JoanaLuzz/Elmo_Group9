import cv2
import mediapipe as mp
import threading
import time
import numpy as np

class EyeTracker:
    def __init__(self, source=0):
        # MediaPipe Configuration
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.cap = cv2.VideoCapture(source)
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

        # Shared Data
        self.current_ratio = 0.0
        self.is_looking = False
        
        # Landmark Indices
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]

    def start(self):
        """Starts the camera thread."""
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def stop(self):
        """Stops the camera thread and releases resources."""
        self.running = False
        if self.thread:
            self.thread.join()
        self.cap.release()

    def get_iris_ratio(self):
        """Returns the current iris ratio safely."""
        with self.lock:
            return self.current_ratio

    def is_focused(self):
        """Returns whether the user is looking at the screen."""
        with self.lock:
            return self.is_looking

    def _get_eye_dimensions(self, landmarks, eye_indices, w, h):
        points = np.array([(landmarks[idx].x * w, landmarks[idx].y * h) for idx in eye_indices])
        width = np.ptp(points[:, 0])
        height = np.ptp(points[:, 1])
        min_x = np.min(points[:, 0])
        min_y = np.min(points[:, 1])
        return width, height, min_x, min_y

    def _get_pupil_location(self, landmarks, iris_indices, w, h):
        points = np.array([(landmarks[idx].x * w, landmarks[idx].y * h) for idx in iris_indices])
        return np.mean(points, axis=0)

    def _update(self):
        """Internal loop to process frames."""
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Process frame
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

            focused = False
            ratio = 0.0

            if results.multi_face_landmarks:
                mesh_points = results.multi_face_landmarks[0].landmark
                
                # Use Right Eye for calculations (consistent with your logic)
                r_width, r_height, r_min_x, r_min_y = self._get_eye_dimensions(mesh_points, self.RIGHT_EYE, w, h)
                r_pupil = self._get_pupil_location(mesh_points, self.RIGHT_IRIS, w, h)
                
                l_width, l_height, l_min_x, l_min_y = self._get_eye_dimensions(mesh_points, self.LEFT_EYE, w, h)
                
                # Blink detection logic
                is_blinking = ((r_height/r_width) + (l_height/l_width)) / 2 < 0.28

                if not is_blinking:
                    # Calculate Ratios
                    rx_ratio = (r_pupil[0] - r_min_x) / r_width
                    # ry_ratio = (r_pupil[1] - r_min_y) / r_height
                    l_pupil = self._get_pupil_location(mesh_points, self.LEFT_IRIS, w, h)
                    lx_ratio = (l_pupil[0] - l_min_x) / l_width
                    
                    avg_h_ratio = (rx_ratio + lx_ratio) / 2
                    ratio = avg_h_ratio

                    # Thresholds (Using your Config values)
                    HORIZONTAL_MIN = 0.40
                    HORIZONTAL_MAX = 0.60
                    
                    if HORIZONTAL_MIN <= avg_h_ratio <= HORIZONTAL_MAX:
                        focused = True
                    else:
                        focused = False
                else:
                    # If blinking, assume previous state or treat as focused briefly
                    focused = self.is_looking 

            # Update shared variables thread-safely
            with self.lock:
                self.is_looking = focused
                self.current_ratio = ratio
            
            # Small sleep to save CPU
            time.sleep(0.03)