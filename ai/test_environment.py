import cv2
import numpy as np
import easyocr
from ultralytics import YOLO


print("Checking OpenCV...")
print("OpenCV version:", cv2.__version__)

print("\nChecking NumPy...")
print("NumPy version:", np.__version__)

print("\nLoading YOLO...")
model = YOLO("yolo11n.pt")
print("YOLO loaded successfully!")

print("\nLoading EasyOCR...")
reader = easyocr.Reader(["en"])
print("EasyOCR loaded successfully!")

print("\n================================")
print("AI ENVIRONMENT READY")
print("================================")