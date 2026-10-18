"""Hand-written outfits for the reward (PLAN.md section 6).

Run from the repo root: `python -m pytest training/test_reward.py` or `python -m training.test_reward`.
"""

import json

from training import reward as R
from training import vocab


def item(id, slot, price, colors, formality, tags, name):
    return {"id": id, "slot": slot, "price": price, "colors": colors,
            "formality": formality, "style_tags": tags, "name": name}


CANDIDATES = [
    item("top_001", "top", 40.0, ["cream"], 2, ["minimal", "relaxed"], "Relaxed cotton crewneck"),
    item("top_002", "top", 60.0, ["red"], 3, ["classic"], "Silk camp shirt"),
    item("bottom_001", "bottom", 70.0, ["denim"], 2, ["classic", "relaxed"], "Straight leg jeans"),
    item("bottom_002", "bottom", 90.0, ["black"], 4, ["tailored"], "Pleated wool trousers"),
    item("bottom_003", "bottom", 50.0, ["pink"], 2, ["trendy"], "Satin mini skirt"),
    item("dress_001", "dress", 120.0, ["green"], 2, ["romantic", "relaxed"], "Linen midi dress"),
    item("shoes_001", "shoes", 80.0, ["white"], 2, ["minimal"], "Leather court sneakers"),
    item("shoes_002", "shoes", 150.0, ["black"], 5, ["classic"], "Patent derby shoes"),
    item("outerwear_001", "outerwear", 110.0, ["olive"], 2, ["workwear"], "Waxed chore jacket"),
    item("accessory_001", "accessory", 25.0, ["orange"], 2, ["graphic", "logos"], "Canvas baseball cap"),
    item("accessory_002", "accessory", 30.0, ["silver"], 2, ["minimal"], "Chain bracelet"),
    item("accessory_003", "accessory", 20.0, ["black"], 2, ["classic"], "Leather belt"),
    item("closet_3", "top", 0.0, ["navy"], 2, ["classic", "minimal"], "navy oxford shirt"),
]


def ctx(**over):
    row = {
        "occasion": "everyday", "budget_min": 100.0, "budget_max": 250.0, "anchor": None,
        "candidates": CANDIDATES, "profile_style_tags": ["minimal", "relaxed", "classic"],
        "profile_avoid": ["logos"],
    }
    row.update(over)
    return row


def outfit(items, total, reason="The cream crewneck and jeans keep it easy with white sneakers."):
    return {"items": items, "total": total, "reason": reason}


GOOD = outfit(["top_001", "bottom_001", "shoes_001"], 190.0)


def score(o, **over):
    return R.score_outfit(o, ctx(**over))


def text(*outfits, **extra):
    return json.dumps({"outfits": list(outfits), **extra})


def test_vocab_copy_matches():
    assert R.NEUTRALS == vocab.NEUTRALS
    assert R.CLASHES == vocab.CLASHES
    assert R.STYLE_TAGS == vocab.STYLE_TAGS
    assert R.OCCASION_FORMALITY == vocab.OCCASION_FORMALITY


def test_clearly_good_scores_max():
    s, ok, b = score(GOOD)
    assert ok and s == 6.5, b


def test_closet_anchor_free_and_counted_at_budget_min():
    o = outfit(["closet_3", "bottom_002", "shoes_001"], 170.0,
               "The oxford shirt dresses up the trousers without trying too hard.")
    s, ok, b = score(o, anchor={"source": "closet", "id": "closet_3"}, budget_min=170.0)
    # Formality 2 and 4 are two levels apart, so only that check fails.
    assert ok and b["budget"] == 1.0 and b["anchor"] == 1.0 and b["formality"] == 0.0, b
    # Stating the closet shirt at a price breaks the stated total.
    assert score({**o, "total": 195.0}, anchor={"source": "closet", "id": "closet_3"})[2]["budget"] == 0.0


def test_closet_price_in_column_is_ignored():
    cands = [dict(c, price=99.0) if c["id"] == "closet_3" else c for c in CANDIDATES]
    o = outfit(["closet_3", "bottom_001", "shoes_001"], 150.0, "Your oxford shirt with jeans.")
    assert score(o, candidates=cands, anchor={"source": "closet", "id": "closet_3"})[2]["budget"] == 1.0


def test_catalog_anchor_missing_costs_one():
    s, ok, b = score(GOOD, anchor={"source": "catalog", "id": "outerwear_001"})
    assert ok and b["anchor"] == 0.0 and s == 5.5


def test_budget_edges():
    assert score(GOOD, budget_min=190.0)[2]["budget"] == 1.0
    assert score(GOOD, budget_max=190.0)[2]["budget"] == 1.0
    assert score(GOOD, budget_max=189.99)[2]["budget"] == 0.0
    assert score(GOOD, budget_min=190.01)[2]["budget"] == 0.0


def test_stated_total_must_match_within_a_cent():
    assert score({**GOOD, "total": 190.01})[2]["budget"] == 1.0
    assert score({**GOOD, "total": 190.02})[2]["budget"] == 0.0
    assert score({**GOOD, "total": 190})[2]["budget"] == 1.0


def test_dress_without_bottom_is_complete():
    o = outfit(["dress_001", "shoes_001"], 200.0, "The linen dress with white sneakers is easy and fresh.")
    s, ok, b = score(o)
    assert ok and b["complete"] == 1.0 and s == 6.5, b


def test_incomplete_outfits():
    assert score(outfit(["dress_001", "bottom_001", "shoes_001"], 270.0))[2]["complete"] == 0.0
    assert score(outfit(["top_001", "bottom_001"], 110.0))[2]["complete"] == 0.0
    assert score(outfit(["top_001", "closet_3", "bottom_001", "shoes_001"], 190.0))[2]["complete"] == 0.0
    assert score(outfit(["top_001", "top_001", "bottom_001", "shoes_001"], 230.0))[2]["complete"] == 0.0


def test_two_accessories_and_outerwear_allowed():
    o = outfit(["top_001", "bottom_001", "shoes_001", "accessory_002", "accessory_003"], 240.0)
    s, ok, b = score(o)
    assert ok and b["complete"] == 1.0 and s == 6.5, b


def test_invented_item_fails_gate():
    s, ok, b = score(outfit(["top_001", "bottom_999", "shoes_001"], 190.0))
    assert (s, ok) == (0.0, False) and b == {"invented": ["bottom_999"]}


def test_color_rules():
    clash = outfit(["top_002", "bottom_003", "shoes_001"], 190.0, "The camp shirt and mini skirt pop.")
    assert score(clash)[2]["color"] == 0.0
    two_accents = outfit(["top_002", "bottom_001", "shoes_001", "outerwear_001"], 320.0)
    assert score(two_accents, budget_max=400.0)[2]["color"] == 0.5
    assert score(GOOD)[2]["color"] == 1.0


def test_formality_rules():
    mixed = outfit(["top_001", "bottom_001", "shoes_002"], 260.0, "Jeans and derby shoes.")
    assert score(mixed, budget_max=300.0)[2]["formality"] == 0.0
    assert score(GOOD, occasion="work")[2]["formality"] == 0.0
    assert score(GOOD, occasion="not_an_occasion")[2]["formality"] == 0.0


def test_profile_avoid_and_overlap():
    with_logo = outfit(["top_001", "bottom_001", "shoes_001", "accessory_001"], 215.0)
    assert score(with_logo)[2]["profile"] == 0.0
    assert score(GOOD, profile_style_tags=["minimal"])[2]["profile"] == 2 / 3
    assert score(GOOD, profile_style_tags=[])[2]["profile"] == 1.0
    # A closet anchor the user chose is never held against them.
    o = outfit(["closet_3", "bottom_001", "shoes_001"], 150.0, "Your oxford shirt with jeans.")
    assert score(o, anchor={"source": "closet", "id": "closet_3"}, profile_avoid=["navy"])[2]["profile"] == 1.0


def test_reason_rules():
    assert score({**GOOD, "reason": "Looks great. Very comfy."})[2]["reason"] == 0.0
    assert score({**GOOD, "reason": "A comfortable everyday look."})[2]["reason"] == 0.0
    assert score({**GOOD, "reason": "Pairs top_001 with denim."})[2]["reason"] == 0.5
    assert score({**GOOD, "reason": "The jean and sneaker combo is easy!"})[2]["reason"] == 0.5
    assert score({**GOOD, "reason": " ".join(["jeans"] * 41)})[2]["reason"] == 0.0


def test_parse_rejects_bad_shapes():
    assert R.parse_output(text(GOOD)) == [GOOD]
    assert R.parse_output(text(GOOD, note="hi")) is None
    assert R.parse_output(text({**GOOD, "extra": 1})) is None
    assert R.parse_output('{"outfits": [') is None
    assert R.parse_output("```json\n" + text(GOOD) + "\n```") is None
    assert R.parse_output(text(GOOD, GOOD, GOOD, GOOD)) is None
    assert R.parse_output(text()) is None
    assert R.parse_output(text({**GOOD, "items": []})) is None
    assert R.parse_output(text({**GOOD, "total": "190"})) is None
    assert R.parse_output(text({**GOOD, "total": True})) is None


def test_completion_mean_over_three_and_repeats():
    other = outfit(["dress_001", "shoes_001"], 200.0, "The linen dress with white sneakers.")
    third = outfit(["closet_3", "bottom_001", "shoes_001"], 150.0, "Your oxford shirt with jeans.")
    c = ctx()
    assert R.score_completion(text(GOOD, other, third), c) == 6.5
    assert R.score_completion(text(GOOD), c) == round(6.5 / 3, 4)
    assert R.score_completion(text(GOOD, GOOD, GOOD), c) == round(6.5 / 3, 4)
    assert R.score_completion("not json", c) == 0.0


def test_reward_entry_point_handles_messages_and_json_columns():
    good = text(GOOD)
    completions = [good, [{"role": "assistant", "content": good}], "oops"]
    row = ctx()
    kwargs = {k: [json.dumps(row[k])] * 3 for k in R.CONTEXT_COLUMNS}
    kwargs["occasion"] = ["everyday"] * 3
    kwargs["prompts"] = ["p"] * 3
    got = R.reward(completions, **kwargs)
    assert got == [round(6.5 / 3, 4)] * 2 + [0.0]


def test_ranking_and_spread():
    good2 = outfit(["dress_001", "shoes_001"], 200.0, "The linen dress with white sneakers.")
    good3 = outfit(["closet_3", "bottom_001", "shoes_001"], 150.0, "Your oxford shirt with jeans.")
    meh = outfit(["top_002", "bottom_001", "shoes_001", "outerwear_001"], 300.0, "A bold red layered look.")
    bad = outfit(["top_002", "bottom_003", "shoes_002", "accessory_001"], 285.0, "Great. Fun.")
    cases = {
        "three good": text(GOOD, good2, good3),
        "two good": text(GOOD, good2),
        "good + meh + bad": text(GOOD, meh, bad),
        # Returning fewer outfits than asked costs more than returning weaker ones.
        "meh + meh + bad": text(meh, outfit(["top_002", "bottom_002", "shoes_002"], 300.0, "Sharp."), bad),
        "one good": text(GOOD),
        "all bad": text(bad),
        "invented": text(outfit(["top_001", "bottom_999", "shoes_001"], 190.0)),
        "malformed": text(GOOD)[:-2],
    }
    scores = {k: R.score_completion(v, ctx()) for k, v in cases.items()}
    for k, v in scores.items():
        print(f"{v:6.3f}  {k}")
    order = list(scores.values())
    assert order == sorted(order, reverse=True), scores
    assert len(set(order)) >= 6


if __name__ == "__main__":
    tests = [f for n, f in sorted(globals().items()) if n.startswith("test_")]
    for f in tests:
        f()
    print(f"{len(tests)} tests passed")
