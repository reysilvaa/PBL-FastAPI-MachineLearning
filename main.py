from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from ultralytics import YOLO
import cv2
import os
import numpy as np

# FastAPI instance
app = FastAPI()

# Load YOLO model
# model1.pt = akurasi tinggi (56.70% an)
# model.pt = akurasi lebih rendah (lupa pokok dibawah e model1.pt)
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join("model", "model1.pt"))
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"YOLO model not found at {MODEL_PATH}")

model = YOLO(MODEL_PATH)

# Define Pydantic model for receiving the input
class ImageRequest(BaseModel):
    image_url: str

def process_yolo_predictions(image_path):
    """Run YOLO model and process predictions."""
    # results = model.predict(source=image_path, imgsz=640, conf=0.1)
    results = model.predict(source=image_path, imgsz=640)
    detections = results[0].boxes

    # Count and confidence for analysis
    acne_count = len(detections)
    confidence_scores = [float(box.conf[0].cpu().numpy()) for box in detections]

    # Average confidence for the detections
    avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0

    return acne_count, avg_confidence

@app.post("/predict")
async def predict_skin_condition(request: ImageRequest):
    try:
        # Download image from URL
        response = requests.get(request.image_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch image from URL")

        temp_file = "temp_image.jpg"
        with open(temp_file, "wb") as f:
            f.write(response.content)

        # Process image through YOLO model
        acne_count, avg_confidence = process_yolo_predictions(temp_file)

        # Cleanup temp file
        os.remove(temp_file)

        # Determine skin condition category
        if acne_count <= 5:
            condition = "Rendah"
        elif 6 <= acne_count <= 15:
            condition = "Sedang"
        elif 16 <= acne_count <= 30:
            condition = "Parah"
        else:
            condition = "Sangat Parah"

        return {
            "acne_count": acne_count,
             "condition": condition
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
