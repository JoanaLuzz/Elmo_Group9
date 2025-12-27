import cv2
import time
import mediapipe as mp
import numpy as np
import csv
import sys
import threading
from datetime import datetime
from ElmoV2API import ElmoV2API  # Make sure ElmoV2API.py is in the same folder

# --- CONFIGURATION ---
HORIZONTAL_MIN = 0.40
HORIZONTAL_MAX = 0.60
VERTICAL_MIN = 0.35 
VERTICAL_MAX = 0.50

INATTENTION_LIMIT = 3.0   # Robot gets SAD after this many seconds
FOCUS_RECOVERY_TIME = 0.5 # Robot gets HAPPY after this many seconds of focus

# --- LOGGING SETUP ---
start_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"Session_Log_{start_timestamp}.csv"

try:
    log_file = open(log_filename, mode='w', newline='')
    log_writer = csv.writer(log_file)
    # Columns: Timestamp, Event Type, Status Text, Gaze Direction, Timer Value
    log_writer.writerow(['Timestamp', 'Event', 'Status', 'Gaze_Direction', 'Timer_Duration'])
    print(f" -> Logging started: {log_filename}")
except Exception as e:
    print(f"Error creating log file: {e}")
    sys.exit(1)

# --- ROBOT HELPERS (Non-Blocking) ---
robot = None
current_mood = "normal"

def set_robot_mood(mood):
    """
    Runs robot commands in a separate thread to prevent 
    the webcam video from freezing while the robot moves/sleeps.
    """
    global current_mood
    if robot is None: return
    
    # Avoid repeating the same mood command
    if mood == current_mood and mood != "happy": 
        return

    current_mood = mood
    threading.Thread(target=_robot_worker, args=(mood,)).start()

def _robot_worker(mood):
    """The actual robot commands running in background"""
    try:
        if mood == "sad":
            print(" -> [Robot] Getting SAD...")
            robot.set_tilt(15)        # Head down
            robot.set_screen(image="sad_eyes.jpeg")
            robot.play_sound("Its_Time_To_Focus.wav")
            
        elif mood == "happy":
            print(" -> [Robot] Getting HAPPY!")
            # Recovery Sequence
            robot.set_tilt(0)         # Head up
            robot.set_screen(image="happy_eyes.jpeg")
            # robot.play_sound("Happy.wav")
            time.sleep(2.5)           # Wait for animation
            
            # Return to Normal automatically
            robot.set_screen(image="normal.png")
            # We don't change current_mood variable here to avoid logic conflicts,
            # but visually the robot is now normal.
            
        elif mood == "normal":
            print(" -> [Robot] Normal/Reset")
            robot.set_tilt(0)
            robot.set_screen(image="normal.png")
            
    except Exception as e:
        print(f" -> [Robot Error] {e}")

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

# --- MATH HELPERS ---
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


# ==========================================
#               MAIN SCRIPT
# ==========================================
if __name__ == '__main__':
    # 1. CONNECT TO ROBOT
    if len(sys.argv) < 2:
        print("Error: Missing IP address.")
        print("Usage: python main_robot.py <ROBOT_IP>")
        sys.exit(1)

    print("--- CONNECTING TO ROBOT ---")
    try:
        robot = ElmoV2API(sys.argv[1], debug=False)
        robot.enable_behavior("look_around", False)
        robot.enable_behavior("blush", False)
        time.sleep(0.5)
        
        # Init State
        robot.set_pan_torque(True)
        robot.set_tilt_torque(True)
        robot.set_pan(0) 
        robot.set_tilt(0)
        robot.set_screen(image="normal.png")
        print(" -> Robot Connected & Initialized.")
        
    except Exception as e:
        print(f"Fatal connection error: {e}")
        sys.exit(1)

    # 2. START WEBCAM
    cap = cv2.VideoCapture(0)
    
    # State variables
    distraction_start_time = None
    focus_start_time = None 
    status_text = "Initializing..."
    color_status = (0, 255, 0)
    
    # Tracking changes for Log
    prev_status = ""
    prev_gaze = ""

    print("--- STARTING MONITORING ---")
    print("Press 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret: break
                
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                mesh_points = results.multi_face_landmarks[0].landmark
                
                # --- CALC EYE GEOMETRY ---
                r_width, r_height, r_min_x, r_min_y = get_eye_dimensions(mesh_points, RIGHT_EYE, w, h)
                r_pupil = get_pupil_location(mesh_points, RIGHT_IRIS, w, h)
                l_width, l_height, l_min_x, l_min_y = get_eye_dimensions(mesh_points, LEFT_EYE, w, h)
                l_pupil = get_pupil_location(mesh_points, LEFT_IRIS, w, h)
                
                # --- BLINK DETECTION ---
                is_blinking = ((r_height/r_width) + (l_height/l_width)) / 2 < 0.28
                
                # --- GAZE RATIOS ---
                rx_ratio = (r_pupil[0] - r_min_x) / r_width
                ry_ratio = (r_pupil[1] - r_min_y) / r_height
                lx_ratio = (l_pupil[0] - l_min_x) / l_width
                ly_ratio = (l_pupil[1] - l_min_y) / l_height
                
                avg_h_ratio = (rx_ratio + lx_ratio) / 2
                avg_v_ratio = (ry_ratio + ly_ratio) / 2
                
                # --- ATTENTION CHECK ---
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

                # --- TIMER & ROBOT LOGIC ---
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
                        
                        # TRIGGER ROBOT SAD
                        set_robot_mood("sad")
                
                else:
                    # User is looking at screen (or blinking)
                    if focus_start_time is None:
                        focus_start_time = time.time() 
                    
                    focus_duration = time.time() - focus_start_time
                    
                    if focus_duration > FOCUS_RECOVERY_TIME:
                        # Valid recovery!
                        
                        # If we were previously distracted, stop the timer
                        if distraction_start_time is not None:
                            total_time = time.time() - distraction_start_time
                            log_data("TIMER_STOP", status_text, current_gaze, f"{total_time:.2f}")
                            distraction_start_time = None
                            
                            # If we were actually flagged as STOPPED READING, celebrate!
                            if status_text == "STOPPED READING" or status_text == "SLEEPY":
                                set_robot_mood("happy")

                        status_text = "READING"
                        color_status = (0, 255, 0)
                        
                        # If robot was sad/happy, eventually ensure it goes normal
                        # (handled by happy thread, but we ensure consistency here)
                        if current_mood == "sad":
                             set_robot_mood("normal")

                    else:
                        # Buffer zone (debounce)
                        if distraction_start_time is not None:
                             elapsed = time.time() - distraction_start_time
                             cv2.putText(frame, f"Distraction: {elapsed:.1f}s (Verifying...)", (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

                # --- LOGGING CHANGES ---
                if status_text != prev_status:
                    log_data("STATUS_CHANGE", status_text, current_gaze)
                    prev_status = status_text
                    
                if current_gaze != prev_gaze and current_gaze != "Blinking":
                    log_data("GAZE_CHANGE", status_text, current_gaze)
                    prev_gaze = current_gaze

                # --- DRAW UI ---
                # Draw boxes
                cv2.rectangle(frame, (int(r_min_x), int(r_min_y)), (int(r_min_x+r_width), int(r_min_y+r_height)), (255, 0, 0), 1)
                cv2.rectangle(frame, (int(l_min_x), int(l_min_y)), (int(l_min_x+l_width), int(l_min_y+l_height)), (255, 0, 0), 1)
                # Draw pupils
                cv2.circle(frame, (int(r_pupil[0]), int(r_pupil[1])), 2, (0, 255, 0), -1)
                cv2.circle(frame, (int(l_pupil[0]), int(l_pupil[1])), 2, (0, 255, 0), -1)
                
                cv2.putText(frame, f"Gaze: {current_gaze}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                cv2.putText(frame, f"H:{avg_h_ratio:.2f} V:{avg_v_ratio:.2f}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

            else:
                status_text = "NO READER"
                color_status = (0, 0, 255)

            cv2.putText(frame, f"STATUS: {status_text}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_status, 2)
            cv2.imshow("Robot Eye Tracker", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n -> Interrupted by user.")

    finally:
        # CLEANUP
        cap.release()
        cv2.destroyAllWindows()
        log_file.close()
        
        # Relax Robot
        if robot:
            print(" -> Relaxing Robot Motors...")
            try:
                robot.set_pan_torque(False)
                robot.set_tilt_torque(False)
            except: pass
            
        print(f" -> Log saved to: {log_filename}")
        print(" -> Session Ended.")