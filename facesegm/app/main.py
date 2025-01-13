from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import io
import torch
import numpy as np
from pydantic import BaseModel

app = FastAPI()

print("Загрузка модели на CPU")
model = torch.hub.load(
    'ultralytics/yolov5', 
    'custom', 
    path='model/best.pt', 
    force_reload=True
).to('cpu')  # Указываем использование CPU
model.conf = 0.25  # Устанавливаем порог уверенности

EXPECTED_SIZE = (640, 640)

class DetectionResult(BaseModel):
    boxes: list  # Список координат боксов [x1, y1, x2, y2]

@app.post("/predict", response_model=DetectionResult)
async def predict(file: UploadFile = File(...)):
    print("Start")
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Only JPEG and PNG are supported.")
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    if image.size != EXPECTED_SIZE:
        raise HTTPException(status_code=400, detail=f"Invalid image size. Expected {EXPECTED_SIZE}, got {image.size}.")

    img = np.array(image)

    # # Инференс на CPU
    results = model(img)
    detections = results.xyxy[0].cpu().numpy()  # Преобразуем результаты на CPU

    boxes = [[float(x1), float(y1), float(x2), float(y2)] for x1, y1, x2, y2, conf, cls in detections]
    print("End ")
    # boxes = [[float(1), float(1), float(1), float(1)]]
    return DetectionResult(boxes=boxes)
