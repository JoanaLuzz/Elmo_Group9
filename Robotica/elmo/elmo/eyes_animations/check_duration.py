import cv2
import os

# List of your video files
video_files = [
    "sad_eyes.mp4",
    "sad_to_normal_eyes.mp4",
    "angry_eyes.mp4",
    "angry_to_normal_eyes.mp4"
]

def get_duration(filename):
    if not os.path.exists(filename):
        print(f"Warning: '{filename}' not found in this folder.")
        return 0
        
    # Open the video file
    cap = cv2.VideoCapture(filename)
    
    # Get frame count and fps (frames per second)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    
    duration = 0
    if fps > 0:
        duration = frame_count / fps
    
    cap.release()
    return duration

print("--- VIDEO DURATIONS ---")
for video in video_files:
    duration = get_duration(video)
    print(f"{video}: {duration:.2f} seconds")
print("-----------------------")