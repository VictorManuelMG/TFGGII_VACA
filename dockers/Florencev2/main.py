from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import base64
from PIL import Image
import os
from florencev2.ClassFlorence import FlorenceCaptioner
from pathlib import Path
import shutil
import io

captioner = FlorenceCaptioner()


os.makedirs(captioner.crop_dir, exist_ok=True)

app = FastAPI()

class BatchImageRequest(BaseModel):
    images: List[str]

@app.post("/batch-captions")
def caption_by_batches(req: BatchImageRequest):
    id = 0
    root_dir = Path(__file__).parent
    if os.path.exists(root_dir / "florencev2/tmpcrops"):
        shutil.rmtree(root_dir / "florencev2/tmpcrops")
    os.makedirs(root_dir / "florencev2/tmpcrops")

    for imageb64 in req.images:
        image_data = base64.b64decode(imageb64)
        image = Image.open(io.BytesIO(image_data))
        image.save(f"florencev2/tmpcrops/cropped{id}.jpeg")
        id+=1

    return captioner.generate_captions()