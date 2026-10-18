# The tagged catalog (training/catalog.json, written by training/tag_catalog.py), validated as
# CatalogItem and loaded once per process. Restart the server to pick up a re-tagged file.

import json
from functools import cache
from pathlib import Path

from backend.schemas import CatalogItem

PATH = Path(__file__).resolve().parents[2] / "training" / "catalog.json"


@cache
def items() -> dict[str, CatalogItem]:
    """Catalog items by id, in file order."""
    return {row["id"]: CatalogItem(**row) for row in json.loads(PATH.read_text())}
