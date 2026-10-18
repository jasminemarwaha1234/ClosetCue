from pathlib import Path
from typing import Optional

import numpy as np
from ultralytics import YOLO

from backend.schemas import Item
from backend.services.faces import OWNER_SIM, detect_faces
from backend.services.images import decode

pose_model = YOLO(str(Path(__file__).resolve().parents[1] / "yolov8n-pose.pt"))

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
