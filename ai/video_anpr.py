import cv2
import json
import re
import numpy as np
import easyocr
from ultralytics import YOLO


# ============================================================
# CONFIGURATION
# ============================================================

VIDEO_PATH = "input/traffic.mp4"
MODEL_PATH = "models/license_plate_best.pt"
OUTPUT_PATH = "output/anpr_result.mp4"

# Camera information
CAMERA_ID = "CAM-001"

# JSON output
OBSERVATIONS_PATH = "output/observations.json"

# Process every Nth frame
FRAME_SKIP = 2

# YOLO detection confidence
DETECTION_CONFIDENCE = 0.20

# Minimum OCR confidence
OCR_MIN_CONFIDENCE = 0.20

# Maximum OCR results printed during processing
MAX_OCR_PRINTS = 100


# ============================================================
# LOAD MODELS
# ============================================================

print("Loading YOLO model...")

model = YOLO(MODEL_PATH)

print("YOLO model loaded.")

print("Loading EasyOCR...")

reader = easyocr.Reader(
    ['en'],
    gpu=False
)

print("EasyOCR loaded.")


# ============================================================
# INDIAN NUMBER PLATE NORMALIZATION
# ============================================================

def normalize_indian_plate(text):
    """
    Normalize OCR text into a common Indian private vehicle format:

    AA00AA0000

    Example:
    MH13429456
    ->
    MH13AZ9456
    """

    if not text:
        return None

    # Convert to uppercase
    text = text.upper()

    # Remove spaces and special characters
    text = re.sub(r'[^A-Z0-9]', '', text)

    # Need at least 10 characters
    if len(text) < 10:
        return None

    # Take first 10 characters
    text = text[:10]

    # Position-specific OCR corrections
    #
    # Format:
    # 0 1 = letters
    # 2 3 = numbers
    # 4 5 = letters
    # 6 7 8 9 = numbers

    letter_corrections = {
        '0': 'O',
        '1': 'I',
        '2': 'Z',
        '4': 'A',
        '5': 'S',
        '6': 'G',
        '8': 'B'
    }

    number_corrections = {
        'O': '0',
        'I': '1',
        'Z': '2',
        'S': '5',
        'B': '8',
        'G': '6'
    }

    result = list(text)

    # First two characters -> letters
    for i in [0, 1]:
        if result[i] in letter_corrections:
            result[i] = letter_corrections[result[i]]

    # Characters 2 and 3 -> numbers
    for i in [2, 3]:
        if result[i] in number_corrections:
            result[i] = number_corrections[result[i]]

    # Characters 4 and 5 -> letters
    for i in [4, 5]:
        if result[i] in letter_corrections:
            result[i] = letter_corrections[result[i]]

    # Last four -> numbers
    for i in [6, 7, 8, 9]:
        if result[i] in number_corrections:
            result[i] = number_corrections[result[i]]

    normalized = ''.join(result)

    # Final validation
    if re.match(r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$', normalized):
        return normalized

    return None


# ============================================================
# PLATE IMAGE ENHANCEMENT
# ============================================================

def enhance_plate(plate):
    """
    Improve plate image before OCR.
    """

    if plate is None or plate.size == 0:
        return None

    # Resize
    enlarged = cv2.resize(
        plate,
        None,
        fx=5,
        fy=5,
        interpolation=cv2.INTER_CUBIC
    )

    # Convert to grayscale
    gray = cv2.cvtColor(
        enlarged,
        cv2.COLOR_BGR2GRAY
    )

    # CLAHE for contrast enhancement
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # Sharpen
    kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ])

    sharpened = cv2.filter2D(
        enhanced,
        -1,
        kernel
    )

    return sharpened


# ============================================================
# OCR FUNCTION
# ============================================================

def read_plate(plate):
    """
    Perform OCR on:
    1. Original plate
    2. Enhanced plate

    Return the highest-confidence result.
    """

    if plate is None or plate.size == 0:
        return None, None, 0.0, None

    candidates = []

    # --------------------------------------------------------
    # Original image
    # --------------------------------------------------------

    try:

        results_original = reader.readtext(
            plate,
            detail=1,
            paragraph=False
        )

        for result in results_original:

            if len(result) >= 3:

                text = result[1]
                confidence = float(result[2])

                candidates.append(
                    (
                        text,
                        confidence,
                        "original"
                    )
                )

    except Exception as e:

        print("Original OCR error:", e)

    # --------------------------------------------------------
    # Enhanced image
    # --------------------------------------------------------

    enhanced = enhance_plate(plate)

    if enhanced is not None:

        try:

            results_enhanced = reader.readtext(
                enhanced,
                detail=1,
                paragraph=False
            )

            for result in results_enhanced:

                if len(result) >= 3:

                    text = result[1]
                    confidence = float(result[2])

                    candidates.append(
                        (
                            text,
                            confidence,
                            "enhanced"
                        )
                    )

        except Exception as e:

            print("Enhanced OCR error:", e)

    # --------------------------------------------------------
    # No OCR results
    # --------------------------------------------------------

    if not candidates:
        return None, None, 0.0, None

    # Select highest confidence OCR result
    best_text, best_confidence, best_method = max(
        candidates,
        key=lambda x: x[1]
    )

    # Ignore very low-confidence OCR
    if best_confidence < OCR_MIN_CONFIDENCE:
        return None, best_text, best_confidence, best_method

    # Normalize
    normalized = normalize_indian_plate(
        best_text
    )

    if normalized is None:
        return None, best_text, best_confidence, best_method

    return (
        normalized,
        best_text,
        best_confidence,
        best_method
    )


# ============================================================
# OPEN VIDEO
# ============================================================

print()
print("Opening video...")

cap = cv2.VideoCapture(
    VIDEO_PATH
)

if not cap.isOpened():

    print("ERROR: Could not open video.")

    raise SystemExit


# ============================================================
# VIDEO INFORMATION
# ============================================================

width = int(
    cap.get(cv2.CAP_PROP_FRAME_WIDTH)
)

height = int(
    cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
)

fps = cap.get(
    cv2.CAP_PROP_FPS
)

total_frames = int(
    cap.get(cv2.CAP_PROP_FRAME_COUNT)
)

if fps <= 0:
    fps = 30.0

duration = total_frames / fps


print()
print("========================================")
print("VIDEO INFORMATION")
print("========================================")

print(f"Width        : {width}")
print(f"Height       : {height}")
print(f"FPS          : {fps:.2f}")
print(f"Total frames : {total_frames}")
print(f"Duration     : {duration:.2f} seconds")
print(f"Camera ID    : {CAMERA_ID}")
print("========================================")


# ============================================================
# OUTPUT VIDEO
# ============================================================

fourcc = cv2.VideoWriter_fourcc(
    *"mp4v"
)

out = cv2.VideoWriter(
    OUTPUT_PATH,
    fourcc,
    fps,
    (width, height)
)

if not out.isOpened():

    print("ERROR: Could not create output video.")

    cap.release()

    raise SystemExit


# ============================================================
# DATA STORAGE
# ============================================================

# Every successful OCR observation
ocr_history = []

# Aggregate plate observations
plate_observations = {}

frame_number = 0

processed_frames = 0

plate_detections = 0

valid_ocr_results = 0

printed_ocr_results = 0


# ============================================================
# MAIN VIDEO LOOP
# ============================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    current_frame = frame_number

    # --------------------------------------------------------
    # Frame skipping
    # --------------------------------------------------------

    if frame_number % FRAME_SKIP != 0:

        # Still write original frame
        out.write(frame)

        frame_number += 1

        continue

    processed_frames += 1

    # --------------------------------------------------------
    # YOLO plate detection
    # --------------------------------------------------------

    results = model.predict(
        frame,
        conf=DETECTION_CONFIDENCE,
        verbose=False
    )

    annotated_frame = frame.copy()

    # --------------------------------------------------------
    # Process detections
    # --------------------------------------------------------

    for result in results:

        if result.boxes is None:
            continue

        for box in result.boxes:

            try:

                # Bounding box
                coordinates = box.xyxy[0].cpu().numpy()

                x1, y1, x2, y2 = coordinates.astype(int)

                # Detection confidence
                detection_confidence = float(
                    box.conf[0].cpu().numpy()
                )

            except Exception:

                continue

            # ------------------------------------------------
            # Clamp coordinates
            # ------------------------------------------------

            x1 = max(
                0,
                min(x1, width - 1)
            )

            y1 = max(
                0,
                min(y1, height - 1)
            )

            x2 = max(
                0,
                min(x2, width - 1)
            )

            y2 = max(
                0,
                min(y2, height - 1)
            )

            # Ignore invalid bounding boxes
            if x2 <= x1 or y2 <= y1:
                continue

            plate_detections += 1

            # ------------------------------------------------
            # Crop plate
            # ------------------------------------------------

            plate = frame[
                y1:y2,
                x1:x2
            ]

            if plate.size == 0:
                continue

            # ------------------------------------------------
            # OCR
            # ------------------------------------------------

            (
                plate_number,
                raw_ocr,
                ocr_confidence,
                ocr_method
            ) = read_plate(plate)

            # ------------------------------------------------
            # Draw detection box
            # ------------------------------------------------

            cv2.rectangle(
                annotated_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # ------------------------------------------------
            # OCR succeeded
            # ------------------------------------------------

            if plate_number is not None:

                valid_ocr_results += 1

                # Timestamp
                timestamp_seconds = (
                    frame_number / fps
                )

                # ------------------------------------------------
                # STEP 5.3
                # Store structured ANPR observation
                # ------------------------------------------------

                observation = {

                    "camera_id": CAMERA_ID,

                    "plate_number": plate_number,

                    "raw_ocr": raw_ocr,

                    "confidence": round(
                        float(ocr_confidence),
                        3
                    ),

                    "detection_confidence": round(
                        float(detection_confidence),
                        3
                    ),

                    "frame_number": int(
                        frame_number
                    ),

                    "timestamp_seconds": round(
                        float(timestamp_seconds),
                        2
                    ),

                    "bbox": [
                        int(x1),
                        int(y1),
                        int(x2),
                        int(y2)
                    ],

                    "ocr_method": ocr_method,

                    "video_source": VIDEO_PATH
                }

                ocr_history.append(
                    observation
                )

                # ------------------------------------------------
                # Multi-frame aggregation
                # ------------------------------------------------

                if plate_number not in plate_observations:

                    plate_observations[
                        plate_number
                    ] = {

                        "count": 0,

                        "best_confidence": 0.0,

                        "first_frame": frame_number,

                        "last_frame": frame_number
                    }

                plate_observations[
                    plate_number
                ]["count"] += 1

                plate_observations[
                    plate_number
                ]["best_confidence"] = max(

                    plate_observations[
                        plate_number
                    ]["best_confidence"],

                    float(ocr_confidence)
                )

                plate_observations[
                    plate_number
                ]["last_frame"] = frame_number

                # ------------------------------------------------
                # Print OCR result
                # ------------------------------------------------

                if printed_ocr_results < MAX_OCR_PRINTS:

                    print(
                        f"Frame {frame_number}: "
                        f"{plate_number} | "
                        f"Confidence: "
                        f"{ocr_confidence:.3f}"
                    )

                    printed_ocr_results += 1

                # ------------------------------------------------
                # Draw plate information
                # ------------------------------------------------

                label = (
                    f"{plate_number} "
                    f"{ocr_confidence:.2f}"
                )

                cv2.putText(
                    annotated_frame,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

            else:

                # No valid OCR
                cv2.putText(
                    annotated_frame,
                    "Plate detected",
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )

    # --------------------------------------------------------
    # Add camera information
    # --------------------------------------------------------

    cv2.putText(
        annotated_frame,
        f"Camera: {CAMERA_ID}",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Frame: {frame_number}",
        (20, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Time: {frame_number / fps:.2f}s",
        (20, 105),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # --------------------------------------------------------
    # Write processed frame
    # --------------------------------------------------------

    out.write(
        annotated_frame
    )

    frame_number += 1


# ============================================================
# RELEASE RESOURCES
# ============================================================

cap.release()

out.release()


# ============================================================
# SAVE OBSERVATIONS JSON
# ============================================================

print()
print("Saving ANPR observations...")

with open(
    OBSERVATIONS_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        ocr_history,
        f,
        indent=4
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("========================================")
print("VIDEO ANPR SUMMARY")
print("========================================")

print(
    f"Total video frames      : {total_frames}"
)

print(
    f"Processed frames        : {processed_frames}"
)

print(
    f"Plate detections        : {plate_detections}"
)

print(
    f"Valid OCR results       : {valid_ocr_results}"
)

print(
    f"Unique plates detected  : "
    f"{len(plate_observations)}"
)

print(
    f"Output video            : "
    f"{OUTPUT_PATH}"
)

print(
    f"Observations JSON       : "
    f"{OBSERVATIONS_PATH}"
)

print("========================================")


# ============================================================
# MULTI-FRAME OCR RESULTS
# ============================================================

print()
print("========================================")
print("MULTI-FRAME OCR RESULTS")
print("========================================")

if plate_observations:

    # Sort by number of observations
    sorted_plates = sorted(
        plate_observations.items(),
        key=lambda x: (
            x[1]["count"],
            x[1]["best_confidence"]
        ),
        reverse=True
    )

    for plate, data in sorted_plates:

        print(
            f"{plate} | "
            f"Occurrences: {data['count']} | "
            f"Best confidence: "
            f"{data['best_confidence']:.3f} | "
            f"First frame: "
            f"{data['first_frame']} | "
            f"Last frame: "
            f"{data['last_frame']}"
        )

    # --------------------------------------------------------
    # Stable plate
    # --------------------------------------------------------

    stable_plate = sorted_plates[0][0]

    stable_data = sorted_plates[0][1]

    print()
    print("----------------------------------------")

    print(
        f"STABLE PLATE: {stable_plate}"
    )

    print(
        f"Occurrences: {stable_data['count']}"
    )

    print(
        f"Best confidence: "
        f"{stable_data['best_confidence']:.3f}"
    )

    print(
        f"First frame: "
        f"{stable_data['first_frame']}"
    )

    print(
        f"Last frame: "
        f"{stable_data['last_frame']}"
    )

    print("----------------------------------------")

else:

    print(
        "No valid plates were detected."
    )


# ============================================================
# FINISHED
# ============================================================

print()
print("ANPR processing completed successfully.")