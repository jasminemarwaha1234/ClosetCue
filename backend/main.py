import asyncio
import base64
import io
from typing import Optional

import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from fastapi import FastAPI
from PIL import Image, ImageOps
from pydantic import BaseModel
from ultralytics import YOLO

app = FastAPI()
pose_model = YOLO("yolov8n-pose.pt")
mtcnn = MTCNN(keep_all=True, device="cpu", min_face_size=20)
resnet = InceptionResnetV1(pretrained="vggface2").eval()  # downloads weights first run

# --- body / pose settings ---
MIN_PERSON_CONF = 0.5
MIN_KP_CONF = 0.5
MIN_HEIGHT_FRAC = 0.25
MAX_PEOPLE = 3  # only used when no owner face is set
RANK = {"none": 0, "upper": 1, "full": 2}
L_SHOULDER, R_SHOULDER = 5, 6
L_HIP, R_HIP = 11, 12
L_KNEE, R_KNEE = 13, 14
L_ANKLE, R_ANKLE = 15, 16

# --- face settings (tune these) ---
MIN_FACE_PROB = 0.9    # MTCNN confidence that it's a face
MIN_FACE_PX = 24       # ignore tiny faces
CLUSTER_SIM = 0.6      # faces this similar = same person (onboarding)
OWNER_SIM = 0.6        # face this similar to owner = it's you (scan)
MIN_CLUSTER_PHOTOS = 2
MAX_CANDIDATES = 3


class Item(BaseModel):
    id: str
    base64: str


class ScanRequest(BaseModel):
    items: list[Item]
    owner_embedding: Optional[list[float]] = None


def decode(b64: str) -> Image.Image:
    img = Image.open(io.BytesIO(base64.b64decode(b64)))
    return ImageOps.exif_transpose(img).convert("RGB")


# ---------------- faces ----------------

def detect_faces(img: Image.Image):
    """Returns (boxes, embeddings). Embeddings are L2-normalized, shape (n, 512)."""
    boxes, probs = mtcnn.detect(img)
    if boxes is None:
        return [], np.zeros((0, 512), dtype=np.float32)

    keep = [
        i for i, (b, p) in enumerate(zip(boxes, probs))
        if p is not None and p >= MIN_FACE_PROB and (b[2] - b[0]) >= MIN_FACE_PX
    ]
    if not keep:
        return [], np.zeros((0, 512), dtype=np.float32)

    kept = [boxes[i].tolist() for i in keep]
    crops = []
    for x1, y1, x2, y2 in kept:
        crop = img.crop((max(0, x1), max(0, y1), min(img.width, x2), min(img.height, y2)))
        arr = (np.asarray(crop.resize((160, 160)), dtype=np.float32) - 127.5) / 128.0
        crops.append(torch.from_numpy(arr).permute(2, 0, 1))

    with torch.no_grad():
        emb = resnet(torch.stack(crops))
        emb = torch.nn.functional.normalize(emb, dim=1)
    return kept, emb.numpy()


def face_crop_b64(img: Image.Image, box) -> str:
    x1, y1, x2, y2 = box
    m = 0.4 * (x2 - x1)
    crop = img.crop((max(0, x1 - m), max(0, y1 - m), min(img.width, x2 + m), min(img.height, y2 + m)))
    crop.thumbnail((200, 200))
    buf = io.BytesIO()
    crop.save(buf, "JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode()


def find_owner_sync(items: list[Item]) -> dict:
    faces = []
    for pi, item in enumerate(items):
        try:
            img = decode(item.base64)
        except Exception:
            continue
        boxes, embs = detect_faces(img)
        for b, e in zip(boxes, embs):
            faces.append({
                "photo": pi, "emb": e, "box": b, "img": img,
                "size": (b[2] - b[0]) * (b[3] - b[1]),
            })

    # greedy clustering, biggest faces first (better embeddings seed the clusters)
    clusters = []
    for f in sorted(faces, key=lambda f: -f["size"]):
        best, best_sim = None, 0.0
        for c in clusters:
            s = float(np.dot(c["centroid"], f["emb"]))
            if s > best_sim:
                best, best_sim = c, s
        if best is not None and best_sim >= CLUSTER_SIM:
            best["members"].append(f)
            m = np.mean([x["emb"] for x in best["members"]], axis=0)
            best["centroid"] = m / np.linalg.norm(m)
        else:
            clusters.append({"centroid": f["emb"], "members": [f]})

    for c in clusters:
        c["photos"] = len({m["photo"] for m in c["members"]})
    clusters = [c for c in clusters if c["photos"] >= MIN_CLUSTER_PHOTOS]
    clusters.sort(key=lambda c: -c["photos"])

    candidates = []
    for c in clusters[:MAX_CANDIDATES]:
        rep = max(c["members"], key=lambda m: m["size"])
        candidates.append({
            "embedding": [round(float(x), 4) for x in c["centroid"]],
            "crop": face_crop_b64(rep["img"], rep["box"]),
            "photos": c["photos"],
        })
    return {"candidates": candidates}


# ---------------- body framing ----------------

def classify_framing(kp_conf: list[float]) -> str:
    def vis(i: int) -> bool:
        return kp_conf[i] >= MIN_KP_CONF

    upper = (vis(L_SHOULDER) or vis(R_SHOULDER)) and (vis(L_HIP) or vis(R_HIP))
    if not upper:
        return "none"
    if (vis(L_KNEE) or vis(R_KNEE)) and (vis(L_ANKLE) or vis(R_ANKLE)):
        return "full"
    return "upper"


def inside(person_box, face_box) -> bool:
    cx = (face_box[0] + face_box[2]) / 2
    cy = (face_box[1] + face_box[3]) / 2
    return person_box[0] <= cx <= person_box[2] and person_box[1] <= cy <= person_box[3]


def check_sync(item: Item, owner: Optional[np.ndarray] = None) -> dict:
    try:
        img = decode(item.base64)
        res = pose_model.predict(img, conf=MIN_PERSON_CONF, verbose=False)[0]

        candidates = []
        kps = res.keypoints
        if len(res.boxes) > 0 and kps is not None and kps.conf is not None:
            kp_rows = kps.conf.tolist()
            for i, box in enumerate(res.boxes):
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                frac = (y2 - y1) / img.height
                if frac < MIN_HEIGHT_FRAC:
                    continue
                framing = classify_framing(kp_rows[i])
                if framing == "none":
                    continue
                candidates.append({
                    "framing": framing, "frac": frac,
                    "conf": float(box.conf[0]), "box": [x1, y1, x2, y2],
                })

        owner_sim = None
        if owner is not None and candidates:
            # keep only people whose face matches the owner
            boxes, embs = detect_faces(img)
            owner_sim = 0.0
            matched = []
            for b, e in zip(boxes, embs):
                s = float(np.dot(owner, e))
                owner_sim = max(owner_sim, s)
                if s >= OWNER_SIM:
                    matched.append(b)
            candidates = [c for c in candidates if any(inside(c["box"], fb) for fb in matched)]
        elif owner is None and len(candidates) > MAX_PEOPLE:
            candidates = []

        if not candidates:
            return {"id": item.id, "has_outfit": False, "framing": "none",
                    "confidence": 0, "owner_sim": owner_sim}

        best = max(candidates, key=lambda c: (RANK[c["framing"]], c["frac"]))
        return {"id": item.id, "has_outfit": True, "framing": best["framing"],
                "confidence": best["conf"], "owner_sim": owner_sim}
    except Exception as e:
        return {"id": item.id, "has_outfit": False, "framing": "none",
                "confidence": 0, "error": str(e)}


# ---------------- routes ----------------

@app.post("/faces/find-owner")
async def find_owner(items: list[Item]):
    return await asyncio.to_thread(find_owner_sync, items)


@app.post("/scan")
async def scan(req: ScanRequest):
    owner = None
    if req.owner_embedding and len(req.owner_embedding) == 512:
        owner = np.asarray(req.owner_embedding, dtype=np.float32)
        owner = owner / np.linalg.norm(owner)
    results = await asyncio.to_thread(lambda: [check_sync(i, owner) for i in req.items])
    return {"results": results}


@app.get("/health")
async def health():
    return {"ok": True}