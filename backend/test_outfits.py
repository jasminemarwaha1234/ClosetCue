"""POST /outfits with the profile, catalog and models stubbed. Run with `python -m pytest backend/test_outfits.py`."""

import asyncio
import json

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routes import outfits
from backend.schemas import CatalogItem
from backend.services import catalog, gemini, supabase, veri


def item(id, price, color, fit="regular", tags=("streetwear",), department="men"):
    slot = id.split("_")[0]
    return CatalogItem(
        id=id, name=f"{color} {slot}", brand="Test", slot=slot, department=department, price=price,
        colors=[color], formality=2, style_tags=list(tags), season=["fall"], pattern="solid",
        fit=None if slot in ("shoes", "accessory") else fit, image="", url="",
    )


CATALOG = [
    item("top_001", 40, "black", "relaxed"),
    item("top_002", 60, "white"),
    item("bottom_001", 50, "denim"),
    item("bottom_002", 70, "olive", "relaxed"),
    item("bottom_003", 200, "gray"),
    item("bottom_004", 60, "black", "relaxed"),
    item("bottom_005", 90, "khaki", tags=("workwear",)),
    item("bottom_006", 45, "white"),
    item("shoes_001", 80, "white"),
    item("shoes_002", 100, "brown", tags=("workwear",)),
    item("outerwear_001", 120, "black"),
    item("dress_001", 90, "black", department="women"),
]
PROFILE = {
    "summary": "Relaxed streetwear in dark neutrals.",
    "style_tags": ["streetwear"],
    "colors": ["black", "white"],
    "fits": ["relaxed"],
    "avoid": ["y2k"],
    "departments": ["men"],
    "looks": [],
    "closet": [{
        "id": "closet_1", "description": "navy oxford shirt", "slot": "top", "colors": ["navy"],
        "formality": 2, "style_tags": ["streetwear"], "pattern": "solid", "fit": "regular",
        "season": ["fall"], "photo_id": "p1",
    }],
}
REQUEST = {"anchor": {"source": "catalog", "id": "top_001"}, "budget_min": 100, "budget_max": 250, "occasion": "casual"}

A = ["top_001", "bottom_001", "shoes_001"]  # $170
B = ["top_001", "bottom_002", "shoes_002"]  # $210


def answer(*outfits):
    return json.dumps({"outfits": [{"items": ids, "total": 999, "reason": "The black top works."} for ids in outfits]})


@pytest.fixture
def run(monkeypatch):
    """run(answers, request) -> (response, calls). answers maps a model to its replies in order;
    a reply is a string, None (not configured) or an exception to raise."""
    calls = []

    async def profile(user_id):
        return PROFILE

    monkeypatch.setattr(supabase, "get_profile", profile)
    monkeypatch.setattr(catalog, "items", lambda: {i.id: i for i in CATALOG})
    app = FastAPI()
    app.include_router(outfits.router)
    app.dependency_overrides[supabase.current_user] = lambda: "user-1"
    client = TestClient(app)

    def go(answers, request=REQUEST):
        replies = {model: list(r) for model, r in answers.items()}

        async def reply(model, messages):
            calls.append((model, messages[1]["content"]))
            r = replies[model].pop(0) if replies.get(model) else None
            if isinstance(r, Exception):
                raise r
            return r

        monkeypatch.setattr(veri, "chat", reply)
        monkeypatch.setattr(gemini, "chat", lambda messages: reply("gemini", messages))
        calls.clear()
        return client.post("/outfits", json=request), calls

    return go


def ids(outfit):
    return [i["id"] for i in outfit["items"]] + [o["id"] for o in outfit["owned"]]


def test_guard_drops_invented_items_and_recomputes_totals(run):
    res, calls = run({"OUR_LLAMA": [answer(A, B, ["top_001", "bottom_009", "shoes_001"])]})
    body = res.json()
    assert res.status_code == 200
    assert body["generated_by"] == "our-llama"
    assert [ids(o) for o in body["outfits"]] == [A, B]
    assert [o["total"] for o in body["outfits"]] == [170.0, 210.0]
    assert [m for m, _ in calls] == ["OUR_LLAMA"]


def test_guard_drops_repeated_outfits_and_strips_code_fences(run):
    res, _ = run({"OUR_LLAMA": ["```json\n" + answer(A, list(reversed(A)), B) + "\n```"]})
    assert [ids(o) for o in res.json()["outfits"]] == [A, B]


def test_missing_anchor_and_over_budget_retry_then_fall_back(run):
    weak = answer(A, ["bottom_001", "shoes_001"], ["top_001", "bottom_003", "shoes_002"])  # 1 good, no anchor, $340
    res, calls = run({"OUR_LLAMA": [weak, weak], "BASE_LLAMA": [None], "gemini": [answer(A, B)]})
    body = res.json()
    assert body["generated_by"] == "gemini"
    assert [ids(o) for o in body["outfits"]] == [A, B]
    assert [m for m, _ in calls] == ["OUR_LLAMA", "OUR_LLAMA", "BASE_LLAMA", "gemini"]


def test_model_error_skips_to_the_next_model(run):
    res, calls = run({"OUR_LLAMA": [httpx.ConnectError("down")], "BASE_LLAMA": [answer(A, B)]})
    assert res.json()["generated_by"] == "base-llama"
    assert [m for m, _ in calls] == ["OUR_LLAMA", "BASE_LLAMA"]


def test_best_partial_answer_when_no_model_reaches_two(run):
    one = answer(A)
    res, _ = run({"OUR_LLAMA": [one, one], "BASE_LLAMA": [one, one], "gemini": [one, one]})
    body = res.json()
    assert body["generated_by"] == "our-llama"
    assert [ids(o) for o in body["outfits"]] == [A]


def test_503_when_every_model_fails(run):
    res, calls = run({"OUR_LLAMA": [httpx.ConnectError("down")], "gemini": ["not json", "{}"]})
    assert res.status_code == 503
    assert [m for m, _ in calls] == ["OUR_LLAMA", "BASE_LLAMA", "gemini", "gemini"]


@pytest.mark.parametrize("request_", [
    {**REQUEST, "anchor": {"source": "catalog", "id": "top_999"}},
    {**REQUEST, "anchor": {"source": "closet", "id": "closet_9"}},
    {**REQUEST, "upgrade_of": ["top_001", "bottom_999"]},
])
def test_unknown_ids_are_422(run, request_):
    res, calls = run({}, request_)
    assert res.status_code == 422
    assert calls == []


def test_swaps_are_same_slot_in_budget_best_profile_match_first(run):
    res, _ = run({"OUR_LLAMA": [answer(A, B)]})
    swaps = {k: [s["id"] for s in v] for k, v in res.json()["outfits"][0]["swaps"].items()}
    # bottom_003 would make the total $320 and bottom_005 matches the profile least.
    assert swaps == {"bottom_001": ["bottom_004", "bottom_002", "bottom_006"], "shoes_001": ["shoes_002"]}


def test_closet_anchor_is_owned_and_free(run):
    closet_outfit = ["closet_1", "bottom_002", "shoes_001"]
    res, calls = run({"OUR_LLAMA": [answer(closet_outfit, ["closet_1", "bottom_004", "shoes_002"])]},
                     {**REQUEST, "anchor": {"source": "closet", "id": "closet_1"}})
    first = res.json()["outfits"][0]
    assert ids(first) == ["bottom_002", "shoes_001", "closet_1"]
    assert first["total"] == 150.0
    assert "closet_1" not in first["swaps"]
    assert "Anchor (they own it; it costs $0), which every outfit must include:\n" \
           "closet_1 | navy oxford shirt | top | $0.00 | navy | formality 2 | streetwear" in calls[0][1]


def test_upgrade_moves_the_budget_up_and_returns_one_outfit(run):
    nicer = ["top_001", "bottom_003", "shoes_001"]  # $320, over the request's $250
    res, calls = run({"OUR_LLAMA": [answer(nicer, B)]}, {**REQUEST, "upgrade_of": A})
    body = res.json()
    assert [ids(o) for o in body["outfits"]] == [nicer]
    assert body["outfits"][0]["total"] == 320.0
    assert "Budget for the catalog items: $170.01 to $320.00" in calls[0][1]
    assert "Build exactly 1 outfit." in calls[0][1]


def test_404_without_a_profile(run, monkeypatch):
    async def no_profile(user_id):
        return None

    monkeypatch.setattr(supabase, "get_profile", no_profile)
    res, _ = run({})
    assert res.status_code == 404


def test_veri_is_skipped_when_its_url_is_unset(monkeypatch):
    monkeypatch.delenv("OUR_LLAMA_URL", raising=False)
    assert asyncio.run(veri.chat("OUR_LLAMA", [])) is None
