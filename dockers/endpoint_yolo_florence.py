import requests
from PIL import ImageGrab
import io
import base64
import os
from dotenv import load_dotenv

from CUA.util.logger import logger

load_dotenv()

def yolo_florence_inference(order:str,simplex:bool):
    image = ImageGrab.grab()
    buffer = io.BytesIO()
    image.save(buffer, format="jpeg")

    img_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

    if simplex:
        url = "http://localhost:8000/simple"
        data = {"image": img_data,
        "order": order}
        response = requests.post(url,json=data)
        logger.debug(f"Response for simplex: {response.json()}")
        return response.json()
    else:
        url = "http://localhost:8000/complex"
        data = {"image": img_data,
        "order": order}
        response = requests.post(url,json=data)
        logger.debug(f"Response for complex: {response.json()}")
        return response.json()