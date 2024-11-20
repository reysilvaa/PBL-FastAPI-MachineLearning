from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# FastAPI instance
app = FastAPI()

# Load model once when server starts
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join("model", "acne_classification_model.h5"))  # Default path jika tidak ada
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

model = load_model(MODEL_PATH)

def preprocess_image(image_path):
    """Preprocess image to match model input."""
    img = load_img(image_path, target_size=(224, 224))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array / 255.0  # Normalize

@app.post("/predict")
async def predict_skin_condition(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        temp_file = f"temp_{file.filename}"
        with open(temp_file, "wb") as f:
            f.write(await file.read())

        # Preprocess and predict
        img_array = preprocess_image(temp_file)
        prediction = model.predict(img_array)
        predicted_class = int(np.argmax(prediction[0]))
        confidence = float(prediction[0][predicted_class])

        # Remove temp file after processing
        os.remove(temp_file)

        # Prepare response
        return JSONResponse(content={
            "class": predicted_class,
            "confidence": confidence
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
