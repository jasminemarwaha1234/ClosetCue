"""/profile routes with Gemini and Supabase stubbed. Run with `python -m pytest backend/test_profile.py`."""

import base64
import io
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from backend.routes import profile
from backend.services import gemini, supabase


def photo(id):
    buf = io.BytesIO()
    Image.new("RGB", (800, 600), "navy").save(buf, "JPEG")
    return {"id": id, "base64": base64.b64encode(buf.getvalue()).decode()}


PHOTOS = [photo("asset-a"), photo("asset-b")]

GEMINI_ANSWER = {
    "summary": " Relaxed streetwear in dark neutrals. ",
    "style_tags": ["streetwear", "edgy", "minimal", "streetwear", "workwear", "sporty"],
    "colors": ["black", "grey", "navy", "cream", "olive", "white"],
    "fits": ["relaxed", "baggy", "oversized", "regular"],
    "departments": ["men", "unisex"],
    "formality": 2,
    "avoid": ["y2k"],
    "looks": [
        {"name": "Weekend errands", "photos": [1, 2, 2, 7]},
        {"name": "Ghost look", "photos": [9]},
        {"name": "", "photos": [1]},
        "not a look",
    ],
    "closet": [
        {"photo": 1, "description": "black hoodie", "slot": "top", "colors": ["black", "charcoal-ish"],
         "formality": 2, "style_tags": ["streetwear", "edgy"], "pattern": "solid", "fit": "baggy",
         "season": ["winter", "fall", "monsoon"]},
        {"photo": 2, "description": "white sneakers", "slot": "shoes", "colors": ["white"], "formality": 2,
         "style_tags": ["minimal"], "pattern": "solid", "fit": "slim", "season": ["summer"]},
        {"photo": 2, "description": "silk scarf", "slot": "scarf", "colors": ["red"], "formality": 3,
         "style_tags": ["minimal"], "pattern": "solid", "fit": None, "season": ["fall"]},
        {"photo": 1, "description": "tie-dye tee", "slot": "top", "colors": ["rainbow"], "formality": 2,
         "style_tags": ["minimal"], "pattern": "solid", "fit": "regular", "season": ["summer"]},
        {"photo": 5, "description": "olive cargos", "slot": "bottom", "colors": ["olive"], "formality": 2,
         "style_tags": ["workwear"], "pattern": "solid", "fit": "relaxed", "season": ["fall"]},
        {"photo": 1, "description": "denim jacket", "slot": "outerwear", "colors": ["denim"], "formality": 9,
         "style_tags": ["workwear"], "pattern": "solid", "fit": "regular", "season": ["spring"]},
        {"photo": 2, "description": "plaid shirt", "slot": "top", "colors": ["red"], "formality": 2,
         "style_tags": ["grunge"], "pattern": "plaid", "fit": "relaxed", "season": ["fall"]},
        {"photo": 1, "description": "olive chinos", "slot": "bottom", "colors": ["olive"], "formality": 3,
         "style_tags": ["workwear"], "pattern": "solid", "fit": "slim", "season": ["spring", "fall"]},
    ],
}

EXPECTED = {
    "summary": "Relaxed streetwear in dark neutrals.",
    "style_tags": ["streetwear", "minimal", "workwear"],
    "colors": ["black", "navy", "cream", "olive"],
    "fits": ["relaxed", "oversized"],
    "avoid": [],
    "departments": ["men"],
    "looks": [{"name": "Weekend errands", "photo_ids": ["asset-a", "asset-b"]}],
    "closet": [
        {"id": "closet_1", "description": "black hoodie", "slot": "top", "colors": ["black"], "formality": 2,
         "style_tags": ["streetwear"], "pattern": "solid", "fit": "regular", "season": ["fall", "winter"],
         "photo_id": "asset-a"},
        {"id": "closet_2", "description": "white sneakers", "slot": "shoes", "colors": ["white"], "formality": 2,
         "style_tags": ["minimal"], "pattern": "solid", "fit": None, "season": ["summer"], "photo_id": "asset-b"},
        {"id": "closet_3", "description": "olive chinos", "slot": "bottom", "colors": ["olive"], "formality": 3,
         "style_tags": ["workwear"], "pattern": "solid", "fit": "slim", "season": ["spring", "fall"],
         "photo_id": "asset-a"},
    ],
}


@pytest.fixture
def api(monkeypatch):
    """A client with Supabase stubbed by an in-memory table. Gemini answers with `api.answer`."""
    saved = {}
    calls = []

    async def get_profile(user_id):
        return saved.get(user_id)

    async def save_profile(user_id, data):
        saved[user_id] = json.loads(json.dumps(data))
        return saved[user_id]

    async def describe_photos(prompt, jpegs):
        calls.append((prompt, jpegs))
        return client.answer

    monkeypatch.setattr(supabase, "get_profile", get_profile)
    monkeypatch.setattr(supabase, "save_profile", save_profile)
    monkeypatch.setattr(gemini, "describe_photos", describe_photos)
    app = FastAPI()
    app.include_router(profile.router)
    app.dependency_overrides[supabase.current_user] = lambda: "user-1"
    client = TestClient(app)
    client.answer = json.dumps(GEMINI_ANSWER)
    client.saved, client.calls = saved, calls
    return client


def test_post_keeps_only_vocab_values_and_numbers_the_closet(api):
    res = api.post("/profile", json={"photos": PHOTOS})
    assert res.status_code == 200
    assert res.json() == EXPECTED
    assert api.saved["user-1"] == EXPECTED
    prompt, jpegs = api.calls[0]
    assert len(jpegs) == 2
    assert Image.open(io.BytesIO(jpegs[0])).size == (512, 384)
    assert "formality" not in prompt.split("closet:")[0]


def test_post_with_an_unusable_answer_saves_an_empty_profile(api):
    api.answer = json.dumps(["not", "an", "object"])
    res = api.post("/profile", json={"photos": PHOTOS})
    assert res.json() == {"summary": "", "style_tags": [], "colors": [], "fits": [], "avoid": [],
                          "departments": [], "looks": [], "closet": []}


def test_post_errors(api):
    assert api.post("/profile", json={"photos": []}).status_code == 422
    assert api.post("/profile", json={"photos": [photo(str(i)) for i in range(31)]}).status_code == 422
    assert api.post("/profile", json={"photos": [{"id": "x", "base64": "bm90IGFuIGltYWdl"}]}).status_code == 422
    api.answer = "not json"
    assert api.post("/profile", json={"photos": PHOTOS}).status_code == 502
    api.answer = None
    assert api.post("/profile", json={"photos": PHOTOS}).status_code == 500
    assert api.saved == {}


def test_get_is_404_until_a_profile_exists(api):
    res = api.get("/profile")
    assert res.status_code == 404
    assert res.json() == {"detail": "Make a style profile first"}


def test_put_then_get_round_trips(api):
    edited = {**EXPECTED, "summary": "Mostly black.", "avoid": ["y2k", "orange"], "closet": EXPECTED["closet"][:1]}
    assert api.put("/profile", json=edited).json() == edited
    assert api.get("/profile").json() == edited


def test_put_rejects_a_bad_closet_id(api):
    bad = {**EXPECTED, "closet": [{**EXPECTED["closet"][0], "id": "hoodie"}]}
    assert api.put("/profile", json=bad).status_code == 422
    assert api.saved == {}


def test_401_without_a_token(monkeypatch):
    monkeypatch.setattr(supabase, "URL", "https://example.supabase.co")
    monkeypatch.setattr(supabase, "KEY", "test")
    app = FastAPI()
    app.include_router(profile.router)
    client = TestClient(app)
    assert client.get("/profile").status_code == 401
    assert client.put("/profile", json=EXPECTED).status_code == 401
    assert client.post("/profile", json={"photos": PHOTOS}).status_code == 401
