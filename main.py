from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from ultralytics import YOLO
import cv2
import os
import numpy as np
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'), 
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

app = FastAPI()
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join("model", "model3.pt"))
model = YOLO(MODEL_PATH)

class ImageRequest(BaseModel):
    image_url: str

def draw_predictions(image_path, boxes):
    """Draw bounding boxes on image and return annotated image."""
    img = cv2.imread(image_path)
    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
        conf = float(box.conf[0].cpu().numpy())
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, f'{conf:.2f}', (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return img

def process_yolo_predictions(image_path):
    """Run YOLO model and process predictions."""
    # with threshold 
    # results = model.predict(source=image_path, imgsz=640, conf=0.20)
    # without threshold 
    results = model.predict(source=image_path, imgsz=640, conf=0.20)
    detections = results[0].boxes
    
    # Draw predictions on image
    annotated_image = draw_predictions(image_path, detections)
    annotated_path = "temp_predicted.jpg"
    cv2.imwrite(annotated_path, annotated_image)
    
    # Upload predicted image to Cloudinary
    predicted_url = cloudinary.uploader.upload(
        annotated_path,
        folder="predicted-images"
    )['secure_url']
    
    # Clean up temporary files
    os.remove(annotated_path)
    
    # Extract bounding boxes
    boxes = []
    for box in detections:
        x1, y1, x2, y2 = map(float, box.xyxy[0].cpu().numpy())
        conf = float(box.conf[0].cpu().numpy())
        boxes.append({
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'confidence': conf
        })
    
    acne_count = len(detections)
    confidence_scores = [float(box.conf[0].cpu().numpy()) for box in detections]
    avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
    
    return acne_count, avg_confidence, boxes, predicted_url

@app.post("/predict")
async def predict_skin_condition(request: ImageRequest):
    try:
        response = requests.get(request.image_url)
        temp_file = "temp_image.jpg"
        with open(temp_file, "wb") as f:
            f.write(response.content)
        
        acne_count, avg_confidence, boxes, predicted_url = process_yolo_predictions(temp_file)
        os.remove(temp_file)
        
        condition = "Rendah" if acne_count <= 5 else \
                   "Sedang" if acne_count <= 15 else \
                   "Parah" if acne_count <= 30 else "Sangat Parah"
        
        return {
            "acne_count": acne_count,
            "condition": condition,
            "avg_confidence": avg_confidence,
            "boxes": boxes,
            "predicted_url": predicted_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
