from yolo.ClassScreenAssistant import ScreenAssistant


from fastapi import FastAPI
from pydantic import BaseModel

screener = ScreenAssistant()

app = FastAPI()

print("Inicializando")


class ImageRequest(BaseModel):
    image: str
    order: str


@app.post("/simple")
def simple_interpret(req: ImageRequest):
    return screener.simple_interpreter(req.order, req.image)


@app.post("/complex")
def complex_interpret(req: ImageRequest):
    return screener.interpret_screen(
        req.order, req.image
    )
