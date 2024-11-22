from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import os

# FastAPI instance
app = FastAPI()

# Load model
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join("model", "acne_classification_model.h5"))
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

model = load_model(MODEL_PATH)

# Define Pydantic model for receiving the input
class ImageRequest(BaseModel):
    image_url: str

def preprocess_image(image_path):
    """Preprocess image to match model input."""
    img = load_img(image_path, target_size=(224, 224))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array / 255.0  # Normalize

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

        # Preprocess and predict
        img_array = preprocess_image(temp_file)
        prediction = model.predict(img_array)
        predicted_class = int(np.argmax(prediction[0]))
        confidence = float(prediction[0][predicted_class])

        # Cleanup temp file
        os.remove(temp_file)

        return {"class": predicted_class, "confidence": confidence}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")