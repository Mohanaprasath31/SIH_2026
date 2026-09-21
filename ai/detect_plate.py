from ultralytics import YOLO
import cv2
import os


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

MODEL_PATH = "models/license_plate_best.pt"
IMAGE_PATH = "input/car.jpg"
OUTPUT_PATH = "output/plate_detection.jpg"


# --------------------------------------------------
# 2. Load model
# --------------------------------------------------

print("Loading license plate model...")

model = YOLO(MODEL_PATH)

print("Model loaded successfully!")


# --------------------------------------------------
# 3. Read image
# --------------------------------------------------

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("ERROR: Could not read image:")
    print(IMAGE_PATH)
    exit()

print("Image loaded successfully!")

print("Image size:", image.shape)


# --------------------------------------------------
# 4. Run license plate detection
# --------------------------------------------------

print("\nDetecting license plates...")

results = model(
    image,
    conf=0.30
)


# --------------------------------------------------
# 5. Create output directory
# --------------------------------------------------

os.makedirs("output", exist_ok=True)


plate_count = 0


# --------------------------------------------------
# 6. Process detections
# --------------------------------------------------

for result in results:

    boxes = result.boxes

    for box in boxes:

        # Bounding box coordinates
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        # Detection confidence
        confidence = float(box.conf[0])

        print("\nLicense plate detected!")
        print("Confidence:", round(confidence, 3))
        print("Coordinates:", x1, y1, x2, y2)


        # --------------------------------------------------
        # Crop license plate
        # --------------------------------------------------

        plate_crop = image[y1:y2, x1:x2]

        if plate_crop.size == 0:
            continue


        plate_count += 1


        # Save cropped plate
        plate_path = f"output/plate_{plate_count}.jpg"

        cv2.imwrite(
            plate_path,
            plate_crop
        )

        print("Plate saved:", plate_path)


        # --------------------------------------------------
        # Draw bounding box
        # --------------------------------------------------

        cv2.rectangle(
            image,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )


        # Add confidence text
        text = f"Plate {confidence:.2f}"

        cv2.putText(
            image,
            text,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


# --------------------------------------------------
# 7. Save result
# --------------------------------------------------

cv2.imwrite(
    OUTPUT_PATH,
    image
)


# --------------------------------------------------
# 8. Final result
# --------------------------------------------------

print("\n================================")
print("DETECTION COMPLETE")
print("================================")

print("Plates detected:", plate_count)

print("Result image:", OUTPUT_PATH)