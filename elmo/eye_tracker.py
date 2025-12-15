import cv2
import mediapipe as mp
import threading
import time
import math

class EyeTracker:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.user_is_looking = True
        self.current_ratio = 0.5
        self.thread = None
        
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def _calculate_iris_position(self, iris_center, right_point, left_point):
        center_to_right_dist = math.dist(iris_center, right_point)
        total_distance = math.dist(right_point, left_point)
        if total_distance == 0: return 0.5
        return center_to_right_dist / total_distance

    def _run_detection(self):
        self.cap = cv2.VideoCapture(0)
        while self.is_running and self.cap.isOpened():
            success, image = self.cap.read()
            if not success: continue

            image.flags.writeable = False
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(image_rgb)

            looking_now = False
            if results.multi_face_landmarks:
                mesh_points = results.multi_face_landmarks[0].landmark
                p_iris = (mesh_points[468].x, mesh_points[468].y)
                p_right = (mesh_points[33].x, mesh_points[33].y)
                p_left = (mesh_points[133].x, mesh_points[133].y)

                ratio = self._calculate_iris_position(p_iris, p_right, p_left)
                
                self.current_ratio = ratio

                # Lógica de foco (ajustada para os teus valores preferidos)
                if 0.42 < ratio < 0.58: 
                    looking_now = True
            
            self.user_is_looking = looking_now
            time.sleep(0.1)
        self.cap.release()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run_detection)
            self.thread.daemon = True
            self.thread.start()
            print(" -> [EyeTracker] Webcam ON.")

    def stop(self):
        self.is_running = False
        if self.thread: self.thread.join()
        print(" -> [EyeTracker] Webcam OFF.")

    def is_focused(self):
        return self.user_is_looking

    # Novo método para obter a razão do íris do olho
    def get_iris_ratio(self):
        return self.current_ratio