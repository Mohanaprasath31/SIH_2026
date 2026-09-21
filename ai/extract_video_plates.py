import cv2
from ultralytics import YOLO
import os

VIDEO_PATH = "input/traffic.mp4"
MODEL_PATH = "models/license_plate_best.pt"
OUTPUT_DIR = "output/video_plates"

os.makedirs(OUTPUT_DIR, exist_ok=True)

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_PATH)

frame_count = 0
plate_count = 0

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame_count += 1

    # Process every 5th frame
    if frame_count % 5 != 0:
        continue

    results = model(frame, conf=0.20, verbose=False)

    for result in results:

        if result.boxes is None:
            continue

        for box in result.boxes:

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Keep coordinates inside image
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)

            plate = frame[y1:y2, x1:x2]

            if plate.size == 0:
                continue

            plate_count += 1

            filename = os.path.join(
                OUTPUT_DIR,
                f"plate_{plate_count}.jpg"
            )

            cv2.imwrite(filename, plate)

            # Only save first 20 plates
            if plate_count >= 20:
                break

        if plate_count >= 20:
            break

    if plate_count >= 20:
        break

cap.release()

print("\n==============================")
print("PLATE EXTRACTION COMPLETE")
print("==============================")
print("Frames checked:", frame_count)
print("Plates saved:", plate_count)
print("Location:", OUTPUT_DIR)
print("==============================")
