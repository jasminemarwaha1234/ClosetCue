# POST /tryon: the outfit on the user's own photo (PLAN.md section 3, screen 6).

from fastapi import APIRouter

from backend.schemas import TryOnRequest, TryOnResponse
from backend.services.tryon import try_on

router = APIRouter()


@router.post("/tryon")
async def tryon(req: TryOnRequest) -> TryOnResponse:
    # Takes 10-20 seconds. The photo isn't stored.
    return TryOnResponse(image_base64=await try_on(req.photo.base64, req.item_ids))
