import cv2
import time
import mediapipe as mp
import numpy as np
import csv
from datetime import datetime

# --- CONFIGURATION ---
HORIZONTAL_MIN = 0.40
HORIZONTAL_MAX = 0.60
VERTICAL_MIN = 0.35 
VERTICAL_MAX = 0.50

INATTENTION_LIMIT = 3.0 
FOCUS_RECOVERY_TIME = 0.5 

# --- LOGGING SETUP ---
start_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"Reading_Log_{start_timestamp}.csv"

log_file = open(log_filename, mode='w', newline='')
log_writer = csv.writer(log_file)
log_writer.writerow(['Timestamp', 'Event', 'Status', 'Gaze_Direction', 'Timer_Duration'])
print(f"Logging started: {log_filename}")

# --- MEDIAPIPE SETUP ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True, 
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Landmark Indices
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
UPPER_LIP = 13
LOWER_LIP = 14

cap = cv2.VideoCapture(0)

# State variables
distraction_start_time = None
focus_start_time = None 
status_text = "Initializing..."
gaze_dir = "Center"
color_status = (0, 255, 0)

# Variables to track changes
prev_status = ""
prev_gaze = ""

def get_eye_dimensions(landmarks, eye_indices, frame_w, frame_h):
    eye_points = np.array([(landmarks[idx].x * frame_w, landmarks[idx].y * frame_h) for idx in eye_indices])
    width = np.ptp(eye_points[:, 0]) 
    height = np.ptp(eye_points[:, 1])
    min_x = np.min(eye_points[:, 0])
    min_y = np.min(eye_points[:, 1])
    return width, height, min_x, min_y

def get_pupil_location(landmarks, iris_indices, frame_w, frame_h):
    iris_points = np.array([(landmarks[idx].x * frame_w, landmarks[idx].y * frame_h) for idx in iris_indices])
    return np.mean(iris_points, axis=0)

def log_data(event_type, status, gaze, timer_val=""):
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3] 
    log_writer.writerow([now, event_type, status, gaze, timer_val])

# --- MAIN LOOP ---
while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    results = face_mesh.process(rgb_frame)
    
    if results.multi_face_landmarks:
        mesh_points = results.multi_face_landmarks[0].landmark
        
        # --- 1. EYE GEOMETRY ---
        r_width, r_height, r_min_x, r_min_y = get_eye_dimensions(mesh_points, RIGHT_EYE, w, h)
        r_pupil = get_pupil_location(mesh_points, RIGHT_IRIS, w, h)
        l_width, l_height, l_min_x, l_min_y = get_eye_dimensions(mesh_points, LEFT_EYE, w, h)
        l_pupil = get_pupil_location(mesh_points, LEFT_IRIS, w, h)
        
        # --- 2. BLINK DETECTION ---
        is_blinking = ((r_height/r_width) + (l_height/l_width)) / 2 < 0.28
        
        # --- 3. GAZE RATIOS ---
        rx_ratio = (r_pupil[0] - r_min_x) / r_width
        ry_ratio = (r_pupil[1] - r_min_y) / r_height
        lx_ratio = (l_pupil[0] - l_min_x) / l_width
        ly_ratio = (l_pupil[1] - l_min_y) / l_height
        
        avg_h_ratio = (rx_ratio + lx_ratio) / 2
        avg_v_ratio = (ry_ratio + ly_ratio) / 2
        
        # --- 4. ATTENTION LOGIC ---
        is_looking_away = False
        current_gaze = "Center"
        
        if not is_blinking:
            if avg_h_ratio < HORIZONTAL_MIN:
                current_gaze = "Right"
                is_looking_away = True
            elif avg_h_ratio > HORIZONTAL_MAX:
                current_gaze = "Left"
                is_looking_away = True
            elif avg_v_ratio < VERTICAL_MIN:
                current_gaze = "Up"
                is_looking_away = True
            elif avg_v_ratio > VERTICAL_MAX:
                current_gaze = "Down"
                is_looking_away = True
        else:
            current_gaze = "Blinking"

        # --- 5. ROBUST TIMER LOGIC ---
        if is_looking_away:
            focus_start_time = None 
            
            if distraction_start_time is None:
                distraction_start_time = time.time()
                log_data("TIMER_START", status_text, current_gaze, "0.0")
            
            elapsed = time.time() - distraction_start_time
            cv2.putText(frame, f"Distraction: {elapsed:.1f}s", (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            if elapsed > INATTENTION_LIMIT:
                status_text = "STOPPED READING"
                color_status = (0, 0, 255)
        
        else:
            if focus_start_time is None:
                focus_start_time = time.time() 
            
            focus_duration = time.time() - focus_start_time
            
            if focus_duration > FOCUS_RECOVERY_TIME:
                if "SLEEPY" not in status_text:
                    if distraction_start_time is not None:
                        total_time = time.time() - distraction_start_time
                        log_data("TIMER_STOP", status_text, current_gaze, f"{total_time:.2f}")
                        distraction_start_time = None

                    status_text = "READING"
                    color_status = (0, 255, 0)
            else:
                if distraction_start_time is not None:
                     elapsed = time.time() - distraction_start_time
                     cv2.putText(frame, f"Distraction: {elapsed:.1f}s (Verifying...)", (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        # --- 6. LOGGING STATE CHANGES ---
        if status_text != prev_status:
            log_data("STATUS_CHANGE", status_text, current_gaze)
            prev_status = status_text
            
        if current_gaze != prev_gaze and current_gaze != "Blinking":
            log_data("GAZE_CHANGE", status_text, current_gaze)
            prev_gaze = current_gaze

        # --- DRAWING (RESTORED) ---
        # 1. Draw Eye Boxes (Blue)
        cv2.rectangle(frame, (int(r_min_x), int(r_min_y)), (int(r_min_x+r_width), int(r_min_y+r_height)), (255, 0, 0), 1)
        cv2.rectangle(frame, (int(l_min_x), int(l_min_y)), (int(l_min_x+l_width), int(l_min_y+l_height)), (255, 0, 0), 1)
        
        # 2. Draw Pupil Centers (Green Dots)
        cv2.circle(frame, (int(r_pupil[0]), int(r_pupil[1])), 2, (0, 255, 0), -1)
        cv2.circle(frame, (int(l_pupil[0]), int(l_pupil[1])), 2, (0, 255, 0), -1)
        
        # 3. Text Info
        cv2.putText(frame, f"Gaze: {current_gaze}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        cv2.putText(frame, f"H:{avg_h_ratio:.2f} V:{avg_v_ratio:.2f}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

    else:
        status_text = "NO READER"
        color_status = (0, 0, 255)

    cv2.putText(frame, f"STATUS: {status_text}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_status, 2)
    cv2.imshow("Logged Eye Tracker", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
log_file.close()
print(f"Log saved to: {log_filename}")