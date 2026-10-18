"""Generate synthetic style profiles with closets for the training prompts (PLAN section 5, Data).

Run from the repo root: python -m training.gen_profiles [--n 20] [--seed 0] [--out training/data/profiles.jsonl]

Each profile is a dict shaped like backend/schemas.py's StyleProfile, plus the fields the prompt
builder needs: `id`, `occasions`, `budget_min` and `budget_max`. Every value comes from
training/vocab.py. Profile i depends only on (seed, i), so a run with a larger --n starts with the
same profiles as a smaller one.

A profile is built around one primary style (STYLES below): its companion tags, formality range
and fits keep the person coherent, and its colors come from the palettes of the person's styles. Colors are chosen so every pair scores at
least MIN_COLOR_PAIR in vocab.COLOR_COMPATIBILITY, which allows at most one accent. The avoid
list holds style tags and colors the person's style doesn't use, so it never contradicts their
tags, colors or closet.

The closet has CLOSET_PER_SLOT items for each slot the person wears (no dresses for a men-only
profile). Closet items carry ClosetItem's fields plus the `name` and `price` (always 0) that
retrieval and the reward read. Ids are closet_1, closet_2, ...

`summary` is a template written from the fields, so this script needs no network. Gemini could
rewrite the summaries later for more natural wording.
"""

import argparse
import json
import random
from pathlib import Path

from training.vocab import (
    COLOR_COMPATIBILITY, COLOR_GROUP, COLORS, FIT_SLOTS, FITS, OCCASION_FORMALITY, SEASONS, SLOTS,
    STYLE_TAGS,
)

HERE = Path(__file__).parent
CLOSET_PER_SLOT = 5
MIN_COLOR_PAIR = 0.75
BUDGET_STEP = 10
MIN_BUDGET_GAP = 50

# Primary style -> what a person dressing that way tends to wear.
STYLES = {
    "minimal": {
        "companions": ["clean-girl", "old-money", "coastal", "workwear"],
        "palette": ["white", "cream", "beige", "gray", "charcoal", "black", "navy", "denim"],
        "formality": (2, 4), "fits": ["slim", "regular"], "patterns": ["stripe"],
    },
    "old-money": {
        "companions": ["preppy", "minimal", "coastal"],
        "palette": ["white", "cream", "beige", "khaki", "brown", "navy", "burgundy", "forest-green"],
        "formality": (3, 5), "fits": ["slim", "regular"], "patterns": ["stripe", "check"],
    },
    "western": {
        "companions": ["workwear", "bohemian", "outdoors"],
        "palette": ["white", "cream", "tan", "brown", "black", "denim", "burgundy", "khaki"],
        "formality": (1, 3), "fits": ["regular", "relaxed"], "patterns": ["check", "small-print"],
    },
    "preppy": {
        "companions": ["old-money", "coastal", "sporty"],
        "palette": ["white", "khaki", "navy", "light-blue", "burgundy", "forest-green", "pink", "red"],
        "formality": (2, 4), "fits": ["slim", "regular"], "patterns": ["stripe", "check"],
    },
    "streetwear": {
        "companions": ["y2k", "techwear", "athleisure", "grunge", "sporty"],
        "palette": ["white", "gray", "black", "olive", "denim", "red", "orange"],
        "formality": (1, 3), "fits": ["relaxed", "oversized"], "patterns": ["graphic", "large-print"],
    },
    "techwear": {
        "companions": ["streetwear", "outdoors", "athleisure", "minimal"],
        "palette": ["gray", "charcoal", "black", "olive", "navy", "silver"],
        "formality": (1, 3), "fits": ["slim", "regular", "relaxed"], "patterns": ["graphic"],
    },
    "workwear": {
        "companions": ["western", "outdoors", "minimal", "grunge"],
        "palette": ["cream", "tan", "khaki", "brown", "navy", "denim", "olive"],
        "formality": (1, 3), "fits": ["regular", "relaxed"], "patterns": ["check", "stripe"],
    },
    "outdoors": {
        "companions": ["workwear", "techwear", "sporty", "coastal"],
        "palette": ["tan", "khaki", "brown", "olive", "forest-green", "navy", "orange"],
        "formality": (1, 3), "fits": ["regular", "relaxed"], "patterns": ["check"],
    },
    "athleisure": {
        "companions": ["sporty", "streetwear", "clean-girl"],
        "palette": ["white", "gray", "black", "navy", "lilac", "muted-green", "pink"],
        "formality": (1, 2), "fits": ["slim", "regular", "oversized"], "patterns": ["graphic"],
    },
    "bohemian": {
        "companions": ["western", "coastal", "soft-girl"],
        "palette": ["cream", "tan", "brown", "olive", "muted-green", "burgundy", "gold", "orange"],
        "formality": (1, 3), "fits": ["relaxed", "oversized"], "patterns": ["small-print", "large-print"],
    },
    "y2k": {
        "companions": ["streetwear", "soft-girl"],
        "palette": ["white", "black", "denim", "light-blue", "lilac", "silver", "pink", "purple"],
        "formality": (1, 4), "fits": ["slim", "oversized"], "patterns": ["graphic", "small-print"],
    },
    "goth": {
        "companions": ["grunge", "minimal"],
        "palette": ["charcoal", "black", "burgundy", "silver", "purple"],
        "formality": (1, 5), "fits": ["slim", "regular", "oversized"], "patterns": ["large-print"],
    },
    "coastal": {
        "companions": ["old-money", "preppy", "minimal", "bohemian"],
        "palette": ["white", "cream", "beige", "khaki", "navy", "blue", "light-blue"],
        "formality": (1, 3), "fits": ["regular", "relaxed"], "patterns": ["stripe"],
    },
    "sporty": {
        "companions": ["athleisure", "preppy", "streetwear", "outdoors"],
        "palette": ["white", "gray", "black", "navy", "blue", "red", "yellow"],
        "formality": (1, 2), "fits": ["regular", "relaxed"], "patterns": ["stripe", "graphic"],
    },
    "clean-girl": {
        "companions": ["minimal", "soft-girl", "athleisure", "old-money"],
        "palette": ["white", "cream", "beige", "tan", "brown", "black", "gold"],
        "formality": (2, 4), "fits": ["slim", "regular"], "patterns": ["stripe"],
    },
    "soft-girl": {
        "companions": ["clean-girl", "y2k", "bohemian", "coastal"],
        "palette": ["white", "cream", "light-blue", "lilac", "pink", "yellow"],
        "formality": (1, 3), "fits": ["regular", "relaxed"], "patterns": ["small-print", "stripe"],
    },
    "grunge": {
        "companions": ["goth", "streetwear", "workwear"],
        "palette": ["gray", "charcoal", "black", "brown", "denim", "olive", "burgundy", "red"],
        "formality": (1, 3), "fits": ["relaxed", "oversized"], "patterns": ["check", "graphic"],
    },
}
WOMEN_STYLES = {"clean-girl", "soft-girl"}

# (name, lowest formality, highest formality) per slot. Every slot covers formality 1 to 5,
# also without WOMEN_ONLY names. Each name has a word of 4+ letters the reward can match.
GARMENTS = {
    "top": [
        ("t-shirt", 1, 2), ("tank top", 1, 2), ("hoodie", 1, 2), ("sweatshirt", 1, 2),
        ("henley", 2, 3), ("polo shirt", 2, 3), ("knit sweater", 2, 4), ("oxford shirt", 3, 4),
        ("button-down shirt", 3, 4), ("blouse", 3, 5), ("turtleneck", 3, 5), ("dress shirt", 4, 5),
    ],
    "bottom": [
        ("joggers", 1, 1), ("leggings", 1, 2), ("shorts", 1, 2), ("cargo pants", 1, 2), ("jeans", 1, 3),
        ("chinos", 2, 4), ("midi skirt", 2, 4), ("wide-leg trousers", 3, 5), ("tailored trousers", 4, 5),
    ],
    "dress": [
        ("sundress", 1, 3), ("knit dress", 2, 3), ("wrap dress", 2, 4), ("shirt dress", 2, 4),
        ("midi dress", 3, 4), ("sheath dress", 4, 5), ("evening gown", 5, 5),
    ],
    "outerwear": [
        ("windbreaker", 1, 2), ("fleece jacket", 1, 2), ("puffer jacket", 1, 3), ("denim jacket", 1, 3),
        ("bomber jacket", 2, 3), ("chore coat", 2, 3), ("leather jacket", 2, 4), ("trench coat", 3, 5),
        ("wool coat", 3, 5), ("blazer", 4, 5),
    ],
    "shoes": [
        ("slides", 1, 1), ("running shoes", 1, 1), ("sneakers", 1, 3), ("canvas sneakers", 1, 3),
        ("boots", 2, 3), ("ankle boots", 2, 4), ("loafers", 3, 4), ("heels", 4, 5),
        ("derby shoes", 4, 5), ("oxford shoes", 5, 5),
    ],
    "accessory": [
        ("baseball cap", 1, 2), ("beanie", 1, 2), ("tote bag", 1, 3), ("crossbody bag", 2, 4),
        ("scarf", 2, 4), ("leather belt", 2, 5), ("watch", 3, 5), ("silk tie", 4, 5),
    ],
}
WOMEN_ONLY = {"blouse", "midi skirt", "heels"}
PATTERN_WORDS = {
    "solid": "", "stripe": "striped ", "check": "check ", "small-print": "print ",
    "large-print": "bold-print ", "graphic": "graphic ",
}
PATTERN_SLOTS = {"top", "dress", "outerwear"}
SEASON_SETS = [
    ["spring", "summer"], ["summer"], ["fall", "winter"], ["spring", "fall"],
    ["spring", "summer", "fall"], ["spring", "fall", "winter"], list(SEASONS),
]
WARM_SEASONS = [["summer"], ["spring", "summer"], ["spring", "summer", "fall"]]
COLD_SEASONS = [["fall", "winter"], ["spring", "fall"], ["spring", "fall", "winter"]]
WARM = {"tank top", "shorts", "sundress", "slides"}
COLD = {"knit sweater", "turtleneck", "beanie", "scarf", "ankle boots", "boots"}


def generate(n: int, seed: int) -> list[dict]:
    return [make_profile(random.Random(f"{seed}-{i}"), i) for i in range(n)]


def make_profile(rng: random.Random, index: int) -> dict:
    primary = rng.choice(STYLE_TAGS)
    style = STYLES[primary]
    departments = _departments(rng, primary)

    companions = [t for t in style["companions"] if departments != ["men"] or t not in WOMEN_STYLES]
    style_tags = [primary] + rng.sample(companions, rng.randint(0, min(2, len(companions))))
    palette = [c for c in COLORS if any(c in STYLES[t]["palette"] for t in style_tags)]
    colors = _colors(rng, palette)
    fits = sorted(rng.sample(style["fits"], rng.randint(1, min(2, len(style["fits"])))), key=FITS.index)
    avoid = _avoid(rng, style_tags, palette)

    low, high = style["formality"]
    occasions = [o for o, (lo, hi) in OCCASION_FORMALITY.items() if lo <= high and hi >= low]
    occasions = sorted(rng.sample(occasions, min(len(occasions), rng.randint(2, 4))),
                       key=list(OCCASION_FORMALITY).index)

    budget_min = rng.randrange(0, 150 + 1, BUDGET_STEP)
    budget_max = rng.randrange(max(60, budget_min + MIN_BUDGET_GAP), 400 + 1, BUDGET_STEP)

    profile = {
        "id": f"profile_{index:04d}",
        "summary": "",
        "style_tags": style_tags,
        "colors": colors,
        "fits": fits,
        "avoid": avoid,
        "departments": departments,
        "occasions": occasions,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "looks": [],
        "closet": _closet(rng, style, style_tags, colors, palette, fits, departments),
    }
    profile["summary"] = summarize(profile)
    return profile


def _departments(rng: random.Random, primary: str) -> list[str]:
    if primary in WOMEN_STYLES:
        return ["women"]
    return rng.choices([["men"], ["women"], ["men", "women"]], weights=[45, 45, 10])[0]


def _colors(rng: random.Random, palette: list[str]) -> list[str]:
    """3 or 4 palette colors whose every pair is compatible enough."""
    want = rng.choice([3, 4])
    chosen: list[str] = []
    for color in rng.sample(palette, len(palette)):
        if len(chosen) < want and all(_compatibility(color, other) >= MIN_COLOR_PAIR for other in chosen):
            chosen.append(color)
    return sorted(chosen, key=COLORS.index)


def _compatibility(a: str, b: str) -> float:
    return COLOR_COMPATIBILITY[COLOR_GROUP[a]][COLOR_GROUP[b]]


def _avoid(rng: random.Random, style_tags: list[str], palette: list[str]) -> list[str]:
    """1 or 2 style tags far from the person's styles, sometimes plus a color outside their palette."""
    near = set(style_tags)
    for tag in style_tags:
        near.update(STYLES[tag]["companions"])
    far_tags = [t for t in STYLE_TAGS if t not in near]
    far_colors = [c for c in COLORS if c not in palette]
    avoid = rng.sample(far_tags, min(len(far_tags), rng.randint(1, 2)))
    if far_colors and rng.random() < 0.5:
        avoid.append(rng.choice(far_colors))
    return avoid


def _closet(rng, style, style_tags, colors, palette, fits, departments) -> list[dict]:
    slots = [s for s in SLOTS if s != "dress" or "women" in departments]
    women = "women" in departments
    others = [c for c in palette if c not in colors]
    closet: list[dict] = []
    for slot in slots:
        seen: set[str] = set()
        for _ in range(CLOSET_PER_SLOT):
            for _attempt in range(20):
                item = _closet_item(rng, slot, style, style_tags, colors, others, fits, women)
                if item["name"] not in seen:
                    break
            seen.add(item["name"])
            closet.append({"id": f"closet_{len(closet) + 1}", **item, "photo_id": f"synthetic_{len(closet) + 1}"})
    return closet


def _closet_item(rng, slot, style, style_tags, colors, others, fits, women) -> dict:
    """Mostly the person's own colors, sometimes another color from their styles' palettes."""
    formality = rng.randint(*style["formality"])
    garments = [name for name, lo, hi in GARMENTS[slot]
                if lo <= formality <= hi and (women or name not in WOMEN_ONLY)]
    garment = rng.choice(garments)

    item_colors = [rng.choice(colors) if not others or rng.random() < 0.75 else rng.choice(others)]
    if rng.random() < 0.3:
        second = rng.choice(colors + others)
        if second not in item_colors and _compatibility(second, item_colors[0]) >= MIN_COLOR_PAIR:
            item_colors.append(second)

    pattern = "solid"
    if slot in PATTERN_SLOTS and rng.random() < 0.3:
        pattern = rng.choice(style["patterns"])

    fit = None
    if slot in FIT_SLOTS:
        fit = rng.choice(fits) if rng.random() < 0.8 else rng.choice(FITS)

    if garment in WARM:
        seasons = WARM_SEASONS
    elif garment in COLD or slot == "outerwear":
        seasons = COLD_SEASONS
    else:
        seasons = SEASON_SETS
    name = f"{item_colors[0]} {PATTERN_WORDS[pattern]}{garment}"
    return {
        "name": name,
        "description": name,
        "slot": slot,
        "price": 0,
        "colors": item_colors,
        "formality": formality,
        "style_tags": sorted(rng.sample(style_tags, rng.randint(1, min(2, len(style_tags)))),
                             key=STYLE_TAGS.index),
        "pattern": pattern,
        "fit": fit,
        "season": rng.choice(seasons),
    }


def summarize(profile: dict) -> str:
    """One templated sentence, like PLAN's "Mostly neutrals with one accent color, relaxed fits, ..."."""
    return (
        f"{_join(profile['style_tags']).capitalize()} style, mostly {_join(profile['colors'])}, "
        f"{_join(profile['fits'])} fits; avoids {_join(profile['avoid'])}."
    )


def _join(words: list[str]) -> str:
    if len(words) <= 1:
        return "".join(words)
    return f"{', '.join(words[:-1])} and {words[-1]}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20, help="number of profiles")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=HERE / "data" / "profiles.jsonl")
    args = parser.parse_args()

    profiles = generate(args.n, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(p) + "\n" for p in profiles))
    print(f"wrote {len(profiles)} profiles to {args.out}")


if __name__ == "__main__":
    main()
