"""Run with `python -m pytest training/test_retrieval.py` or `python -m training.test_retrieval`."""

import itertools
import random

from training.retrieval import format_candidates, retrieve

COLORS = ["black", "white", "navy", "olive", "red", "cream"]
TAGS = [["minimal", "preppy"], ["streetwear", "techwear"], ["coastal"], ["old-money", "preppy"], ["y2k", "streetwear"]]
DEPARTMENTS = ["men", "women", "unisex"]


def make_catalog(per_slot: int = 30) -> list[dict]:
    catalog = []
    for slot in ("top", "bottom", "dress", "outerwear", "shoes", "accessory"):
        for i in range(per_slot):
            catalog.append({
                "id": f"{slot}_{i:03d}",
                "name": f"{slot} {i}",
                "brand": "Test",
                "slot": slot,
                "department": "women" if slot == "dress" and i % 3 else DEPARTMENTS[i % 3],
                "price": 20.0 + (i * 7) % 180,
                "colors": [COLORS[i % len(COLORS)]],
                "formality": 1 + i % 5,
                "style_tags": TAGS[i % len(TAGS)],
                "season": ["fall"],
                "image": "",
                "url": "",
            })
    return catalog


PROFILE = {
    "summary": "",
    "style_tags": ["minimal", "coastal"],
    "colors": ["navy", "cream"],
    "fits": [],
    "avoid": [],
    "departments": ["men", "women"],
    "looks": [],
    "closet": [],
}

REQUEST = {"anchor": None, "budget_max": 400.0, "max_item_price": None, "occasion": "everyday", "n": 50}


def run(catalog=None, profile=None, **overrides):
    return retrieve(catalog or make_catalog(), profile or PROFILE, **{**REQUEST, **overrides})


def by_slot(items):
    counts = {}
    for item in items:
        counts[item["slot"]] = counts.get(item["slot"], 0) + 1
    return counts


def test_deterministic_and_order_independent():
    catalog = make_catalog()
    shuffled = catalog[:]
    random.Random(1).shuffle(shuffled)
    first = [item["id"] for item in run(catalog)]
    assert first == [item["id"] for item in run(catalog)]
    assert first == [item["id"] for item in run(shuffled)]


def test_n_respected():
    for n in (10, 25, 50, 75):
        assert len(run(n=n)) == n
    assert len(run(make_catalog(per_slot=3), n=50)) < 50


def test_catalog_anchor_drops_its_slot_itself_and_its_price():
    anchor = next(item for item in make_catalog() if item["id"] == "top_005")
    items = run(anchor=anchor, budget_max=100.0)
    assert not [item for item in items if item["slot"] in ("top", "dress")]
    assert all(item["price"] <= 100.0 - anchor["price"] for item in items)


def test_dress_anchor_drops_tops_and_bottoms():
    anchor = next(item for item in make_catalog() if item["id"] == "dress_000")
    assert not {"top", "bottom", "dress"} & set(by_slot(run(anchor=anchor)))


def test_accessory_anchor_keeps_accessories_but_not_itself():
    anchor = next(item for item in make_catalog() if item["id"] == "accessory_000")
    ids = [item["id"] for item in run(anchor=anchor)]
    assert "accessory_000" not in ids
    assert any(i.startswith("accessory_") for i in ids)


def test_closet_anchor_costs_nothing():
    closet_anchor = {"id": "closet_1", "description": "navy oxford", "slot": "top", "colors": ["navy"],
                     "formality": 3, "style_tags": ["preppy"], "photo_id": "x"}
    items = run(anchor=closet_anchor, budget_max=150.0, n=1000)
    assert max(item["price"] for item in items) > 140.0
    assert all(item["price"] <= 150.0 for item in items)
    assert "top" not in by_slot(items)


def test_max_item_price():
    assert all(item["price"] <= 60.0 for item in run(max_item_price=60.0, n=20))


def test_departments():
    men = run(profile={**PROFILE, "departments": ["men"]})
    assert {item["department"] for item in men} <= {"men", "unisex"}
    assert "dress" not in by_slot(men)
    women = run(profile={**PROFILE, "departments": ["women"]})
    assert {item["department"] for item in women} <= {"women", "unisex"}
    assert "dress" in by_slot(women)


def test_avoid_style_tags_and_colors():
    items = run(profile={**PROFILE, "avoid": ["y2k", "red"]})
    assert not [item for item in items if "y2k" in item["style_tags"] or "red" in item["colors"]]


def test_formality_within_one_level_of_occasion():
    assert {item["formality"] for item in run(occasion="formal", n=40)} == {4, 5}
    assert {item["formality"] for item in run(occasion="athletic", n=40)} == {1, 2, 3}


def test_slot_proportions():
    counts = by_slot(run(make_catalog(per_slot=40), n=100))
    assert counts["top"] == 25 and counts["bottom"] == 25
    assert counts["shoes"] == 20 and counts["outerwear"] == 12
    assert counts["dress"] == 10 and counts["accessory"] == 8


def test_short_slot_is_filled_from_others():
    catalog = [item for item in make_catalog() if item["slot"] != "top" or item["id"] < "top_002"]
    items = run(catalog, n=50)
    assert len(items) == 50
    assert by_slot(items)["top"] == 2


def top(i, colors, tags):
    return {**make_catalog()[0], "id": f"top_{i:03d}", "colors": colors, "style_tags": tags, "formality": 2}


def test_diversity_cap():
    catalog = [top(i, ["black"], ["minimal"]) for i in range(10)]
    catalog += [top(10 + i, [f"color{i}"], ["coastal"]) for i in range(10)]
    items = run(catalog, n=8)
    assert len(items) == 8
    assert sum(1 for item in items if item["colors"] == ["black"]) == 2


def test_diversity_cap_holds_on_the_mixed_catalog():
    items = run(make_catalog(per_slot=60), n=100)
    for slot in by_slot(items):
        in_slot = [item for item in items if item["slot"] == slot]
        for color, tag in itertools.product(COLORS, {t for tags in TAGS for t in tags}):
            assert sum(1 for i in in_slot if color in i["colors"] and tag in i["style_tags"]) <= 2


def test_reserves_about_15_percent_for_lower_scoring_items():
    catalog = [top(i, [f"a{i}"], ["minimal"]) for i in range(20)]
    catalog += [top(20 + i, [f"b{i}"], ["goth"]) for i in range(20)]
    items = run(catalog, n=20)
    assert sum(1 for item in items if item["style_tags"] == ["goth"]) == 3


def test_fit_bonus_ranks_a_matching_fit_first():
    catalog = [{**top(0, ["black"], ["minimal"]), "fit": "slim"},
               {**top(1, ["black"], ["minimal"]), "fit": "relaxed"}]
    assert [item["id"] for item in run(catalog, n=1)] == ["top_000"]
    assert [item["id"] for item in run(catalog, {**PROFILE, "fits": ["relaxed"]}, n=1)] == ["top_001"]


def test_format_candidates():
    item = make_catalog()[0]
    assert format_candidates([item, item]).splitlines() == [
        "top_000 | top 0 | top | $20.00 | black | formality 1 | minimal, preppy"
    ] * 2
    assert format_candidates([{**item, "name": "Buffalo Check Shirt | Hawk"}]) == \
        "top_000 | Buffalo Check Shirt / Hawk | top | $20.00 | black | formality 1 | minimal, preppy"


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_")]
    for name, fn in tests:
        fn()
        print("ok", name)
    print(f"{len(tests)} passed")
