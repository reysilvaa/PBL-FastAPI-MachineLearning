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
    """Create elegant bounding box visualization."""
    img = cv2.imread(image_path)
    overlay = img.copy()
    
    # Design constants
    BOX_COLOR = (255, 128, 0)
    TEXT_COLOR = (255, 255, 255)  # White text
    OVERLAY_ALPHA = 0.2
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    
    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
        conf = float(box.conf[0].cpu().numpy())
        
        # Draw semi-transparent overlay
        cv2.rectangle(overlay, (x1, y1), (x2, y2), BOX_COLOR, -1)
        
        # Draw border with rounded corners
        corner_radius = 10
        thickness = 2
        
        # Draw rounded corners
        cv2.line(img, (x1 + corner_radius, y1), (x2 - corner_radius, y1), BOX_COLOR, thickness)
        cv2.line(img, (x2, y1 + corner_radius), (x2, y2 - corner_radius), BOX_COLOR, thickness)
        cv2.line(img, (x2 - corner_radius, y2), (x1 + corner_radius, y2), BOX_COLOR, thickness)
        cv2.line(img, (x1, y2 - corner_radius), (x1, y1 + corner_radius), BOX_COLOR, thickness)
        
        cv2.ellipse(img, (x1 + corner_radius, y1 + corner_radius), (corner_radius, corner_radius), 180, 0, 90, BOX_COLOR, thickness)
        cv2.ellipse(img, (x2 - corner_radius, y1 + corner_radius), (corner_radius, corner_radius), 270, 0, 90, BOX_COLOR, thickness)
        cv2.ellipse(img, (x2 - corner_radius, y2 - corner_radius), (corner_radius, corner_radius), 0, 0, 90, BOX_COLOR, thickness)
        cv2.ellipse(img, (x1 + corner_radius, y2 - corner_radius), (corner_radius, corner_radius), 90, 0, 90, BOX_COLOR, thickness)

        # Add modern confidence label
        label_bg_color = BOX_COLOR
        text = f'{conf:.2f}'
        text_size = cv2.getTextSize(text, FONT, 0.6, 2)[0]
        
        # Draw label background
        cv2.rectangle(img, 
                     (x1, y1 - text_size[1] - 10), 
                     (x1 + text_size[0] + 10, y1), 
                     label_bg_color, -1)
                     
        # Add text
        cv2.putText(img, text, 
                    (x1 + 5, y1 - 5), 
                    FONT, 0.6, TEXT_COLOR, 2)

    # Blend overlay with original image
    img = cv2.addWeighted(overlay, OVERLAY_ALPHA, img, 1 - OVERLAY_ALPHA, 0)
    
    return img

def process_yolo_predictions(image_path):
    """Run YOLO model with modern visualization."""
    results = model.predict(source=image_path, imgsz=640, conf=0.25)  # Added confidence threshold
    detections = results[0].boxes
    
    annotated_image = draw_predictions(image_path, detections)
    annotated_path = "temp_predicted.jpg"
    cv2.imwrite(annotated_path, annotated_image)
    
    predicted_url = cloudinary.uploader.upload(
        annotated_path,
        folder="predicted-images",
        quality="auto:best",  # Optimized quality
        fetch_format="auto"   # Auto format optimization
    )['secure_url']
    
    os.remove(annotated_path)
    
    boxes = [{
        'x1': float(box.xyxy[0][0].cpu().numpy()),
        'y1': float(box.xyxy[0][1].cpu().numpy()),
        'x2': float(box.xyxy[0][2].cpu().numpy()),
        'y2': float(box.xyxy[0][3].cpu().numpy()),
        'confidence': float(box.conf[0].cpu().numpy())
    } for box in detections]
    
    return (len(detections), 
            np.mean([b['confidence'] for b in boxes]) if boxes else 0.0,
            boxes, 
            predicted_url)

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
