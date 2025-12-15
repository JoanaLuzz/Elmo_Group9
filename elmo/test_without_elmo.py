import time
import threading
import json
import datetime
import os
from eye_tracker import EyeTracker

def log_session(tracker, stop_event):
    """
    Monitors attention and saves data to a JSON file.
    Does NOT send commands to the robot.
    """
    print(" -> [System] Registration session started (JSON Mode).")
    
    # --- CREATE LOGS FOLDER ---
    folder_name = "logs_control"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f" -> [Info] Folder '{folder_name}' created.")
    
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Save inside logs_control folder
    filename = os.path.join(folder_name, f"study_session_{timestamp_str}.json")
    # ------------------------------------
    
    # List to store all data in memory before saving
    session_data = []
    
    # Variables for detecting Zoning Out
    gaze_history = [] 
    HISTORY_SIZE = 10 # 10 samples * 0.5s = 5 seconds

    try:
        while not stop_event.is_set():
            # A. Collect data
            is_looking = tracker.is_focused()
            current_ratio = tracker.get_iris_ratio()
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            
            # B. Calculate Zoning Out
            gaze_history.append(current_ratio)
            if len(gaze_history) > HISTORY_SIZE:
                gaze_history.pop(0)

            is_zoning_out = False
            variation = 0.0
            
            # Only calculate if we have full history (5 seconds)
            if len(gaze_history) == HISTORY_SIZE:
                variation = max(gaze_history) - min(gaze_history)
                # If variation is tiny, eyes are fixed/staring
                if variation < 0.015: 
                    is_zoning_out = True

            # C. Determine State
            state = "FOCUSED"
            if is_zoning_out:
                state = "ZONING_OUT"
            elif not is_looking:
                state = "DISTRACTED"

            # D. Create data object (Dictionary)
            entry = {
                "timestamp": current_time,
                "iris_ratio": round(current_ratio, 4),
                "state": state,
                "variation_5s": round(variation, 4)
            }
            
            # Add to list
            session_data.append(entry)
            
            # E. Feedback on screen
            print(f" -> Buffer: {len(session_data)} records | State: {state} | Var: {variation:.3f}   ", end='\r')

            time.sleep(0.5)

    finally:
        # F. SAVE JSON FILE AT THE END
        print(f"\n -> [Saving] Writing {len(session_data)} records to {filename}...")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=4)
            print(f" -> [Success] File saved successfully!")
        except Exception as e:
            print(f" -> [Error] Failed to save JSON: {e}")

if __name__ == '__main__':
    print("--- ATTENTION LOGGER (NO ROBOT) ---")
    
    print(" -> Starting Webcam...")
    tracker = EyeTracker()
    tracker.start()
    
    stop_event = threading.Event()
    logger_thread = threading.Thread(target=log_session, args=(tracker, stop_event))
    logger_thread.start()
    
    print("--- RECORDING DATA TO JSON ---")
    print("Press CTRL+C to end the session.")

    try:
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n!!! ENDING SESSION !!!")
        
    finally:
        stop_event.set()
        tracker.stop()
        logger_thread.join()
        print("--- DONE ---")