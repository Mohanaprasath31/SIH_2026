import easyocr
import cv2
import numpy as np
import re

IMAGE_PATH = "output/plate_1.jpg"

print("Loading EasyOCR...")

reader = easyocr.Reader(["en"])

print("EasyOCR loaded successfully!")

# --------------------------------
# Read plate image
# --------------------------------

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("ERROR: Could not read plate image")
    exit()

print("Original image size:", image.shape)

# --------------------------------
# Resize
# --------------------------------

image = cv2.resize(
    image,
    None,
    fx=5,
    fy=5,
    interpolation=cv2.INTER_CUBIC
)

# --------------------------------
# Preprocessing
# --------------------------------

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

clahe = cv2.createCLAHE(
    clipLimit=2.0,
    tileGridSize=(8, 8)
)

clahe_image = clahe.apply(gray)

blur = cv2.GaussianBlur(
    clahe_image,
    (3, 3),
    0
)

_, otsu = cv2.threshold(
    blur,
    0,
    255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)

adaptive = cv2.adaptiveThreshold(
    clahe_image,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    11,
    2
)

images = {
    "original": image,
    "grayscale": gray,
    "clahe": clahe_image,
    "otsu": otsu,
    "adaptive": adaptive
}

# --------------------------------
# OCR
# --------------------------------

allowlist = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

all_results = []

print("\n================================")
print("RUNNING MULTI-PASS OCR")
print("================================")

for name, img in images.items():

    print("\nProcessing:", name)

    results = reader.readtext(
        img,
        allowlist=allowlist,
        detail=1,
        paragraph=False
    )

    if not results:
        print("No text detected")
        continue

    for result in results:

        bbox, text, confidence = result

        cleaned = "".join(
            c for c in text.upper()
            if c.isalnum()
        )

        print(
            "Text:",
            cleaned,
            "| Confidence:",
            round(confidence, 3)
        )

        all_results.append({
            "method": name,
            "text": cleaned,
            "confidence": float(confidence)
        })


# --------------------------------
# Indian plate normalization
# --------------------------------

LETTER_CORRECTIONS = {
    "0": "O",
    "1": "I",
    "2": "Z",
    "4": "A",
    "5": "S",
    "6": "G",
    "8": "B"
}

NUMBER_CORRECTIONS = {
    "O": "0",
    "I": "1",
    "Z": "2",
    "S": "5",
    "B": "8",
    "G": "6"
}


def normalize_indian_plate(text):

    text = "".join(
        c for c in text.upper()
        if c.isalnum()
    )

    # Expected format:
    # AA00AA0000

    if len(text) != 10:
        return None

    chars = list(text)

    # State code
    for i in [0, 1]:

        if chars[i].isdigit():
            chars[i] = LETTER_CORRECTIONS.get(
                chars[i],
                chars[i]
            )

    # District number
    for i in [2, 3]:

        if chars[i].isalpha():
            chars[i] = NUMBER_CORRECTIONS.get(
                chars[i],
                chars[i]
            )

    # Series letters
    for i in [4, 5]:

        if chars[i].isdigit():
            chars[i] = LETTER_CORRECTIONS.get(
                chars[i],
                chars[i]
            )

    # Registration number
    for i in [6, 7, 8, 9]:

        if chars[i].isalpha():
            chars[i] = NUMBER_CORRECTIONS.get(
                chars[i],
                chars[i]
            )

    normalized = "".join(chars)

    # Final validation
    pattern = r"^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$"

    if re.match(pattern, normalized):
        return normalized

    return None


# --------------------------------
# Normalize OCR results
# --------------------------------

print("\n================================")
print("PLATE NORMALIZATION")
print("================================")

normalized_results = []

for result in all_results:

    normalized = normalize_indian_plate(
        result["text"]
    )

    if normalized:

        print(
            result["text"],
            "→",
            normalized,
            "| confidence:",
            round(result["confidence"], 3)
        )

        normalized_results.append({
            "original": result["text"],
            "plate": normalized,
            "confidence": result["confidence"],
            "method": result["method"]
        })


# --------------------------------
# Final result
# --------------------------------

print("\n================================")
print("FINAL ANPR RESULT")
print("================================")

if normalized_results:

    best = max(
        normalized_results,
        key=lambda x: x["confidence"]
    )

    print("Plate Number :", best["plate"])
    print("OCR Input    :", best["original"])
    print("Confidence   :", round(best["confidence"], 3))
    print("Method       :", best["method"])

else:

    print("No valid Indian plate detected.")

print("================================")