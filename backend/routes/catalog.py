# GET /catalog: every tagged catalog item, for browsing and picking an anchor.

from fastapi import APIRouter

from backend.schemas import CatalogItem
from backend.services import catalog

router = APIRouter()


@router.get("/catalog")
async def get_catalog() -> list[CatalogItem]:
    return list(catalog.items().values())
