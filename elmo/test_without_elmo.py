import time
import threading
from eye_tracking import EyeTracker

# Removed imports: json, datetime, os (no longer needed for logging)

def monitor_session(tracker, stop_event):
    """
    Monitors attention and prints state to console.
    """
    print(" -> [System] Monitoring session started (No Logging).")
    
    # Variables for detecting Zoning Out
    gaze_history = [] 
    HISTORY_SIZE = 10 # 10 samples * 0.5s = 5 seconds

    try:
        while not stop_event.is_set():
            # A. Collect data
            is_looking = tracker.is_focused()
            current_ratio = tracker.get_iris_ratio()
            
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

            # D. Feedback on screen (No dictionary storage)
            print(f" -> State: {state} | Var: {variation:.3f} | Eye: {current_ratio:.3f}   ", end='\r')

            time.sleep(0.5)

    finally:
        # Stop message (No file writing)
        print("\n -> [System] Monitoring stopped.")

if __name__ == '__main__':
    print("--- ATTENTION MONITOR (NO ROBOT / NO LOGS) ---")
    
    print(" -> Starting Webcam...")
    tracker = EyeTracker()
    tracker.start()
    
    stop_event = threading.Event()
    # Renamed function to reflect it just monitors, doesn't log
    monitor_thread = threading.Thread(target=monitor_session, args=(tracker, stop_event))
    monitor_thread.start()
    
    print("--- MONITORING ACTIVE ---")
    print("Press CTRL+C to end the session.")

    try:
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n!!! ENDING SESSION !!!")
        
    finally:
        stop_event.set()
        tracker.stop()
        monitor_thread.join()
        print("--- DONE ---")