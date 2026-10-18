"""/rate routes and the pair builder, with Supabase stubbed. Run with `python -m pytest backend/test_rate.py`."""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import build_rate_pairs
from backend.routes import rate
from backend.services import supabase


def item(id, slot, price):
    return {"id": id, "name": id.upper(), "brand": "Acme", "slot": slot, "department": "unisex", "price": price,
            "colors": ["black"], "formality": 2, "style_tags": ["minimal"], "season": ["fall"], "pattern": "solid",
            "fit": None if slot == "shoes" else "regular", "image": f"https://img/{id}", "url": f"https://shop/{id}"}


ITEMS = {i["id"]: i for i in [item("top_1", "top", 40.0), item("top_2", "top", 60.0), item("shoes_1", "shoes", 80.0)]}
JEANS = {"id": "closet_1", "description": "black jeans", "slot": "bottom", "colors": ["black"], "formality": 2,
         "style_tags": ["minimal"], "pattern": "solid", "fit": "slim", "season": ["fall"], "photo_id": "synthetic_1"}
PROFILE = {"id": "profile_7", "summary": "Mostly black, minimal.", "closet": [JEANS]}
PROMPT = {
    "messages": [], "occasion": "everyday", "budget_min": 100, "budget_max": 150,
    "anchor": {"source": "closet", "id": "closet_1"},
    "candidates": [{**JEANS, "name": "black jeans", "price": 0}] + list(ITEMS.values()),
    "profile_style_tags": ["minimal"], "profile_fits": ["regular"], "profile_avoid": [], "profile_id": "profile_7",
}


def answer(row, ids, total, reason="Black on black."):
    raw = json.dumps({"outfits": [{"items": ids, "total": total, "reason": reason}]})
    return {"row": row, "profile_id": "profile_7", "raw": raw}


def outfit(ids, total, reason="Black on black."):
    bought = [ITEMS[i] for i in ids]
    return {"items": bought, "owned": [JEANS], "total": total, "reason": reason, "swaps": {i: [] for i in ids}}


def pair(pair_id):
    shown = {"pair_id": pair_id, "profile_summary": "Mostly black, minimal.",
             "request": {"anchor": None, "budget_min": 50.0, "budget_max": 150.0, "max_item_price": None,
                         "occasion": "casual", "upgrade_of": None, "retry": None},
             "a": {**outfit(["top_1", "shoes_1"], 120.0), "id": "o1"},
             "b": {**outfit(["top_2", "shoes_1"], 140.0), "id": "o2"}}
    return {"pair": shown, "a_model": "gemini", "b_model": "base-llama"}


@pytest.fixture
def api(monkeypatch, tmp_path):
    """A client with three pairs on disk and an in-memory feedback table."""
    feedback = {}

    async def rated_pair_ids(user_id):
        return {pair_id for (user, pair_id) in feedback if user == user_id}

    async def add_feedback(user_id, pair_id, choice, pair, a_model, b_model):
        feedback[(user_id, pair_id)] = {"choice": choice, "pair": pair, "a_model": a_model, "b_model": b_model}

    path = tmp_path / "rate_pairs.jsonl"
    path.write_text("".join(json.dumps(pair(p)) + "\n" for p in ("pair_1", "pair_2", "pair_3")))
    monkeypatch.setattr(rate, "PAIRS", path)
    monkeypatch.setattr(supabase, "rated_pair_ids", rated_pair_ids)
    monkeypatch.setattr(supabase, "add_feedback", add_feedback)
    app = FastAPI()
    app.include_router(rate.router)
    app.dependency_overrides[supabase.current_user] = lambda: "user-1"
    client = TestClient(app)
    client.feedback, client.path = feedback, path
    return client


def test_next_skips_pairs_the_user_rated(api):
    api.feedback[("user-1", "pair_1")] = {}
    api.feedback[("user-1", "pair_3")] = {}
    api.feedback[("user-2", "pair_2")] = {}
    res = api.get("/rate/next")
    assert res.status_code == 200
    assert res.json() == pair("pair_2")["pair"]


def test_next_is_404_when_every_pair_is_rated(api):
    for p in ("pair_1", "pair_2", "pair_3"):
        assert api.post("/rate", json={"pair_id": p, "choice": "a"}).status_code == 204
    res = api.get("/rate/next")
    assert res.status_code == 404
    assert res.json() == {"detail": "You've rated every pair. Thanks for helping!"}


def test_503_without_a_pairs_file(api):
    api.path.unlink()
    res = api.get("/rate/next")
    assert res.status_code == 503
    assert res.json() == {"detail": "There are no outfits to compare yet. Check back soon."}
    assert api.post("/rate", json={"pair_id": "pair_1", "choice": "a"}).status_code == 503


def test_post_stores_the_choice_with_both_models(api):
    res = api.post("/rate", json={"pair_id": "pair_2", "choice": "b"})
    assert res.status_code == 204
    assert res.content == b""
    assert api.feedback == {("user-1", "pair_2"): {
        "choice": "b", "pair": pair("pair_2")["pair"], "a_model": "gemini", "b_model": "base-llama"}}


def test_post_rejects_an_unknown_pair_or_choice(api):
    res = api.post("/rate", json={"pair_id": "pair_9", "choice": "a"})
    assert res.status_code == 422
    assert res.json() == {"detail": "pair_9 isn't a pair we showed"}
    assert api.post("/rate", json={"pair_id": "pair_1", "choice": "c"}).status_code == 422
    assert api.feedback == {}


def test_401_without_a_token(monkeypatch):
    monkeypatch.setattr(supabase, "URL", "https://example.supabase.co")
    monkeypatch.setattr(supabase, "KEY", "test")
    app = FastAPI()
    app.include_router(rate.router)
    client = TestClient(app)
    assert client.get("/rate/next").status_code == 401
    assert client.post("/rate", json={"pair_id": "pair_1", "choice": "a"}).status_code == 401


def build(first, second, seed=0):
    return build_rate_pairs.build_pairs((first, second), ("base", "ours"), [PROMPT, PROMPT, PROMPT, PROMPT],
                                        {"profile_7": PROFILE}, ITEMS, seed)


def test_build_skips_rows_where_either_side_has_no_usable_outfit():
    base = [
        answer(0, ["closet_1", "top_1", "shoes_1"], 120.0),
        answer(1, ["closet_1", "top_1", "shoes_1"], 120.0),
        {"row": 2, "profile_id": "profile_7", "raw": None, "error": "TimeoutError()"},
        answer(3, ["closet_1", "top_1", "shoes_1"], 120.0),
    ]
    ours = [
        answer(0, ["closet_1", "top_2", "shoes_1"], 140.0, "Sharper."),
        answer(1, ["closet_1", "top_9", "shoes_1"], 140.0),  # invented item
        answer(2, ["closet_1", "top_2", "shoes_1"], 140.0),
        answer(3, ["top_2", "shoes_1"], 140.0),  # leaves out the anchor
    ]
    pairs = build(base, ours)
    assert len(pairs) == 1
    built = pairs[0]
    shown = built["pair"]
    assert shown["request"] == {"anchor": {"source": "closet", "id": "closet_1"}, "budget_min": 100.0,
                                "budget_max": 150.0, "max_item_price": None, "occasion": "everyday",
                                "upgrade_of": None, "retry": None}
    assert shown["profile_summary"] == "Mostly black, minimal."
    by_model = {built["a_model"]: shown["a"], built["b_model"]: shown["b"]}
    assert {k: {**v, "id": None} for k, v in by_model.items()} == {
        "base": {**outfit(["top_1", "shoes_1"], 120.0), "id": None},
        "ours": {**outfit(["top_2", "shoes_1"], 140.0, "Sharper."), "id": None},
    }


def test_build_order_is_seeded_and_ids_ignore_file_order():
    base = [answer(n, ["closet_1", "top_1", "shoes_1"], 120.0) for n in range(4)]
    ours = [answer(n, ["closet_1", "top_2", "shoes_1"], 140.0) for n in range(4)]
    first, again = build(base, ours), build(base, ours)
    assert [(p["a_model"], p["b_model"]) for p in first] == [(p["a_model"], p["b_model"]) for p in again]
    assert {p["a_model"] for p in first} == {"base", "ours"}
    swapped = build_rate_pairs.build_pairs((ours, base), ("ours", "base"), [PROMPT] * 4, {"profile_7": PROFILE}, ITEMS)
    assert [p["pair"]["pair_id"] for p in swapped] == [p["pair"]["pair_id"] for p in first]
    assert len({p["pair"]["pair_id"] for p in first}) == 4
