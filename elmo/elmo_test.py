import datetime
import sys
import time
import threading
import json
import os
from ElmoV2API import ElmoV2API
from eye_tracker import EyeTracker

def monitor_attention(robot, tracker, stop_event):
    """
    Monitors user attention, controls the robot, and logs data to JSON.
    Behavior:
    - Focused: Normal eyes, Head center.
    - Distracted OR Zoning Out: Sad eyes, Head down, Sad sound.
    - Recovery: Happy eyes + Sound -> Normal.
    """
    print(" -> [Thread] Vigilance started (JSON Logging enabled).")
    current_mood = "normal"
    
    # --- CREATE LOGS FOLDER ---
    folder_name = "logs_robot"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f" -> [Info] Folder '{folder_name}' created.")

    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Save inside logs_robot folder
    filename = os.path.join(folder_name, f"robot_session_{timestamp_str}.json")
    # ------------------------------------
    
    # Log buffer
    session_data = []
    
    # Initial Robot State
    try:
        robot.set_screen(image="normal.png")
        robot.set_tilt(0)
    except:
        print(" -> [Warning] Failed to set initial state.")
    
    count_bad = 0
    count_good = 0
    # Stability limit: 3 cycles * 0.5s = 1.5 seconds to confirm state change
    STABILITY_LIMIT = 3
    
    gaze_history = [] 
    HISTORY_SIZE = 10 

    try:
        while not stop_event.is_set():
            is_looking = tracker.is_focused()
            current_ratio = tracker.get_iris_ratio()
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            
            # Zoning Out Calculation
            gaze_history.append(current_ratio)
            if len(gaze_history) > HISTORY_SIZE:
                gaze_history.pop(0)

            is_zoning_out = False
            variation = 0.0
            if len(gaze_history) == HISTORY_SIZE:
                variation = max(gaze_history) - min(gaze_history)
                if variation < 0.015: 
                    is_zoning_out = True

            # --- JSON LOGGING ---
            state_log = "FOCUSED"
            if is_zoning_out: state_log = "ZONING_OUT"
            elif not is_looking: state_log = "DISTRACTED"

            entry = {
                "timestamp": current_time,
                "iris_ratio": round(current_ratio, 4),
                "state": state_log,
                "variation_5s": round(variation, 4),
                "robot_mood": current_mood
            }
            session_data.append(entry)
            # --------------------

            # --- ROBOT LOGIC ---
            # User is failing if they are distracted OR zoning out
            is_behaving_badly = (not is_looking) or is_zoning_out

            if is_behaving_badly:
                count_bad += 1
                count_good = 0
                
                if count_bad >= STABILITY_LIMIT:
                    if current_mood != "sad":
                        reason = "ZONING OUT" if is_zoning_out else "DISTRACTED"
                        print(f"\n -> [Eye] {reason}! Getting sad...")
                        
                        # Sad Behavior
                        robot.set_tilt(15)  # Head down
                        robot.set_screen(image="sad_eyes.jpeg")
                        robot.play_sound("Sad.wav") 
                        
                        current_mood = "sad"
                    count_bad = STABILITY_LIMIT 

            else: # Focused
                count_good += 1
                count_bad = 0
                
                if count_good >= STABILITY_LIMIT:
                    if current_mood != "normal":
                        print("\n -> [Eye] Regained focus! Celebrating...")
                        
                        # Recovery Behavior
                        robot.set_tilt(0) # Head up
                        
                        # Only celebrate if coming from a sad state
                        if current_mood == "sad":
                            robot.set_screen(image="happy_eyes.jpeg")
                            robot.play_sound("Happy.wav") 
                            time.sleep(2.5) # Wait for animation/sound
                        
                        # Back to work
                        print(" -> [Eye] Back to study mode (Normal).")
                        robot.set_screen(image="normal.png")
                        current_mood = "normal"
                    count_good = STABILITY_LIMIT

            print(f" -> Log: {len(session_data)} | Eye: {current_ratio:.3f} | Var: {variation:.3f}   ", end='\r')
            time.sleep(0.5)

    finally:
        # SAVE JSON AT END
        print(f"\n -> [Saving] Writing log to {filename}...")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=4)
            print(f" -> [Success] JSON Log saved.")
        except Exception as e:
            print(f" -> [Error] Failed to save JSON: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Error: Missing IP address.")
        print("Usage: python elmo_test.py <ROBOT_IP>")
        sys.exit(1)

    print("--- CONNECTING TO ROBOT (EYE TRACKING STUDY) ---")
    
    # 1. INITIALIZE ROBOT
    try:
        robot = ElmoV2API(sys.argv[1], debug=False)
        robot.enable_behavior("look_around", False)
        robot.enable_behavior("blush", False)
        time.sleep(0.5)
        # Enable motors to hold head position
        robot.set_pan_torque(True)
        robot.set_tilt_torque(True)
        robot.set_pan(0) 
        robot.set_tilt(0)
    except Exception as e:
        print(f"Fatal connection error: {e}")
        sys.exit(1)

    # 2. START EYE TRACKER
    print(" -> Starting Webcam...")
    tracker = EyeTracker()
    tracker.start()
    
    stop_event = threading.Event()
    
    # 3. START VIGILANCE THREAD
    attention_thread = threading.Thread(
        target=monitor_attention, 
        args=(robot, tracker, stop_event)
    )
    attention_thread.start()
    
    print("--- VIGILANCE ACTIVE ---")
    print("Press CTRL+C to stop.")

    # 4. MAIN LOOP
    try:
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n!!! STOPPING ROBOT !!!")
        
    finally:
        # Cleanup
        print(" -> Shutting down systems...")
        stop_event.set()        # Stop thread
        tracker.stop()          # Stop webcam
        attention_thread.join() # Wait for thread to finish
        
        try:
            # Relax motors
            robot.set_pan_torque(False)
            robot.set_tilt_torque(False)
        except:
            pass
            
        print("--- SESSION ENDED ---")