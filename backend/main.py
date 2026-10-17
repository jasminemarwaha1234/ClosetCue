import asyncio
import base64
import io

from fastapi import FastAPI
from PIL import Image
from pydantic import BaseModel
from ultralytics import YOLO

app = FastAPI()
model = YOLO("yolov8n.pt")  # downloads automatically the first time

MIN_CONF = 0.5          # how sure it must be that it's a person
MIN_HEIGHT_FRAC = 0.4   # person must be at least 40% of the photo height


class Item(BaseModel):
    id: str
    base64: str


def check_sync(item: Item) -> dict:
    try:
        img = Image.open(io.BytesIO(base64.b64decode(item.base64))).convert("RGB")
        res = model.predict(img, classes=[0], conf=MIN_CONF, verbose=False)[0]  # class 0 = person

        best_frac, best_conf = 0.0, 0.0
        for box in res.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            frac = (y2 - y1) / img.height
            if frac > best_frac:
                best_frac, best_conf = frac, float(box.conf[0])

        return {
            "id": item.id,
            "has_outfit": best_frac >= MIN_HEIGHT_FRAC,
            "confidence": best_conf,
        }
    except Exception as e:
        return {"id": item.id, "has_outfit": False, "confidence": 0, "error": str(e)}


@app.post("/scan")
async def scan(items: list[Item]):
    results = await asyncio.to_thread(lambda: [check_sync(i) for i in items])
    return {"results": results}


@app.get("/health")
async def health():
    return {"ok": True}