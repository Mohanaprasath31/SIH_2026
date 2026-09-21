import cv2
import os

VIDEO_PATH = "input/traffic.mp4"

print("Opening video...")

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("ERROR: Could not open video")
    print("Video:", VIDEO_PATH)
    exit()

# Video information
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

duration = frame_count / fps if fps > 0 else 0

print("\n================================")
print("VIDEO INFORMATION")
print("================================")
print("Width       :", width)
print("Height      :", height)
print("FPS         :", fps)
print("Frame count :", frame_count)
print("Duration    :", round(duration, 2), "seconds")
print("================================")

# Create output directory
os.makedirs("output/video_frames", exist_ok=True)

# Extract one frame every 30 frames
frame_number = 0
saved_frames = 0

while True:

    ret, frame = cap.read()

    if not ret:
        break

    if frame_number % 30 == 0:

        output_path = (
            f"output/video_frames/"
            f"frame_{saved_frames:04d}.jpg"
        )

        cv2.imwrite(output_path, frame)

        saved_frames += 1

    frame_number += 1

cap.release()

print("\nVideo processing complete.")
print("Frames read   :", frame_number)
print("Frames saved  :", saved_frames)

print("\nSaved frames:")
print("output/video_frames/")