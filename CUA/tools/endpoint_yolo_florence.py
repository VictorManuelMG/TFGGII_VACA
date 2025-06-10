import requests
from PIL import ImageGrab
import io
import base64
import os
from dotenv import load_dotenv

load_dotenv()

url = f"{os.getenv("BASE_URL")}"

headers = {"Authorization": f"Bearer {os.getenv("API_KEY")}"}

def yolo_florence_inference(order:str,simplex:bool):

    image = ImageGrab.grab()
    buffer = io.BytesIO()
    image.save(buffer, format="jpeg")

    img_data = base64.b64encode(buffer.getvalue()).decode("utf-8")


    data = {"image": img_data, "order": order, "simplex": simplex}

    response = requests.post(url=url, data=data, headers=headers)

    return(response.json())