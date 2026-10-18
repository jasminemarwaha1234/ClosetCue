"""Run with `python -m pytest training/test_prompt.py`."""

from training.prompt import SYSTEM, render_prompt

PROFILE = {
    "summary": "Relaxed streetwear in dark neutrals.",
    "style_tags": ["streetwear", "grunge"],
    "colors": ["black"],
    "fits": ["relaxed"],
    "avoid": [],
}
TEE = {"id": "top_004", "name": "Heavy Tee", "slot": "top", "price": 60.0, "colors": ["gray"],
       "formality": 2, "style_tags": ["streetwear"]}
CANDIDATES = [
    {"id": "bottom_004", "name": "Work Pant", "slot": "bottom", "price": 100.0, "colors": ["black"],
     "formality": 2, "style_tags": ["streetwear", "grunge"]},
    {"id": "shoes_001", "name": "Canvas Low", "slot": "shoes", "price": 80.0, "colors": ["white"],
     "formality": 2, "style_tags": ["streetwear"]},
]


def test_catalog_anchor_prompt():
    system, user = render_prompt(PROFILE, occasion="casual", budget_min=100, budget_max=250,
                                 anchor=TEE, candidates=CANDIDATES)
    assert system == {"role": "system", "content": SYSTEM}
    assert user == {"role": "user", "content": """Style profile:
Summary: Relaxed streetwear in dark neutrals.
Style tags: streetwear, grunge
Colors they wear: black
Fits: relaxed
Avoid: none

Occasion: casual (formality 1-3)
Budget for the catalog items: $100.00 to $250.00
Anchor, which every outfit must include:
top_004 | Heavy Tee | top | $60.00 | gray | formality 2 | streetwear

Candidates (id | name | slot | price | colors | formality | style tags):
bottom_004 | Work Pant | bottom | $100.00 | black | formality 2 | streetwear, grunge
shoes_001 | Canvas Low | shoes | $80.00 | white | formality 2 | streetwear

Build exactly 3 different outfits. Each outfit uses only the anchor and candidate ids above, and `items` lists every piece, the anchor included. It has a top and a bottom, or a dress with neither, plus one pair of shoes, at most one outerwear, and any accessories. Every item's formality fits the occasion. `total` is the sum of the catalog items' prices. `reason` is one sentence of at most 40 words that names at least one item.

Budget: every outfit's `total` must be between $100.00 and $250.00, the anchor's $60.00 included. An outfit over $250.00 is rejected.

Reply with only this JSON:
{"outfits": [{"items": ["<id>", "<id>"], "total": <number>, "reason": "<one sentence>"}]}"""}


def test_no_anchor_closet_anchor_and_one_outfit():
    _, none = render_prompt(PROFILE, occasion="formal", budget_min=0, budget_max=80,
                            anchor=None, candidates=CANDIDATES, outfits=1)
    assert "Occasion: formal (formality 4-5)\nBudget for the catalog items: $0.00 to $80.00\nAnchor: none.\n" in none["content"]
    assert "Build exactly 1 outfit." in none["content"]
    assert "\n\nBudget: every outfit's `total` must be between $0.00 and $80.00. An outfit over $80.00 is rejected.\n\n" in none["content"]

    shirt = {**TEE, "id": "closet_3", "name": "navy oxford shirt", "price": 0.0}
    _, closet = render_prompt(PROFILE, occasion="work", budget_min=0, budget_max=80,
                              anchor=shirt, candidates=CANDIDATES)
    assert "Anchor (they own it; it costs $0), which every outfit must include:\n" \
           "closet_3 | navy oxford shirt | top | $0.00 | gray | formality 2 | streetwear\n" in closet["content"]
    assert "must be between $0.00 and $80.00. An outfit" in closet["content"]
