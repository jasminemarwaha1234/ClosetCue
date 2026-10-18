import base64
import io

import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image

from backend.schemas import Item
from backend.services.images import decode

mtcnn = MTCNN(keep_all=True, device="cpu", min_face_size=20)
resnet = InceptionResnetV1(pretrained="vggface2").eval()  # downloads weights first run

# --- face settings (tune these) ---
MIN_FACE_PROB = 0.9    # MTCNN confidence that it's a face
MIN_FACE_PX = 24       # ignore tiny faces
CLUSTER_SIM = 0.6      # faces this similar = same person (onboarding)
OWNER_SIM = 0.6        # face this similar to owner = it's you (scan)
MIN_CLUSTER_PHOTOS = 2
MAX_CANDIDATES = 3


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
