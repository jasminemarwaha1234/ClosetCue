import asyncio

from fastapi import APIRouter

from backend.schemas import Item
from backend.services.faces import find_owner_sync

router = APIRouter()


@router.post("/faces/find-owner")
async def find_owner(items: list[Item]):
    return await asyncio.to_thread(find_owner_sync, items)
