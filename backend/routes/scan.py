import asyncio

import numpy as np
from fastapi import APIRouter

from backend.schemas import ScanRequest
from backend.services.pose import check_sync

router = APIRouter()


@router.post("/scan")
async def scan(req: ScanRequest):
    owner = None
    if req.owner_embedding and len(req.owner_embedding) == 512:
        owner = np.asarray(req.owner_embedding, dtype=np.float32)
        owner = owner / np.linalg.norm(owner)
    results = await asyncio.to_thread(lambda: [check_sync(i, owner) for i in req.items])
    return {"results": results}
