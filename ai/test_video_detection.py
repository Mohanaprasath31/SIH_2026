import cv2
from ultralytics import YOLO

VIDEO_PATH = "input/traffic.mp4"
MODEL_PATH = "models/license_plate_best.pt"

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("ERROR: Could not open video")
    exit()

frame_count = 0
detection_count = 0

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame_count += 1

    # Test every 5th frame
    if frame_count % 5 != 0:
        continue

    results = model(frame, conf=0.20, verbose=False)

    for result in results:
        boxes = result.boxes

        if boxes is not None and len(boxes) > 0:
            detection_count += len(boxes)

            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

    # Save every 30th processed frame
    if frame_count % 30 == 0:
        output_path = f"output/video_test_{frame_count}.jpg"
        cv2.imwrite(output_path, frame)

cap.release()

print("\n==============================")
print("VIDEO DETECTION TEST")
print("==============================")
print("Total frames:", frame_count)
print("Plate detections:", detection_count)
print("==============================")