"""Scrape the stores in training/stores.json into training/catalog_raw.json.

Run from the repo root: python -m training.scrape_catalog [--stores NAME ...] [--cache DIR]

With --stores, every other store's items keep their ids, and the named stores' items are
numbered after the highest existing id in each slot, so tags cached by id stay valid.

Each store is a Shopify shop that serves /products.json. stores.json fields:
  name, domain, currency (the shop's base currency, which products.json prices are in),
  usd_rate (required when currency isn't USD), department (optional hint for one-department stores),
  max_items (optional; defaults to PER_STORE, lower for one-slot stores so they don't swamp a slot).

Requests go strictly one at a time, at least DELAY seconds apart: a parallel run once got
our IP blocked across all of Shopify.
"""

import argparse
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from training.vocab import COLORS, SLOTS

HERE = Path(__file__).parent
DELAY = 3.5
MAX_PAGES = 4
PER_STORE = 50
MAX_PRICE = 1000
USER_AGENT = "Mozilla/5.0"

# Matched against "<product_type> <title>", lowercased; tag_catalog.py drops matches from catalog_raw.json
# too, so items scraped before a pattern was added stay out of catalog.json.
DROP = re.compile(
    r"gift ?card|e-?gift|\bkids?\b|\binfant|\btoddler|\byouth\b|\bbundle|\bsample|sticker|\bcandle|"
    r"\bhome\b|homeware|\bmug\b|poster|\bbook\b|magazine|\btowel|blanket|pillow|cushion|skate ?deck|"
    r"skateboard|lighter|keychain|key ?ring|\bpin\b|\bpatch(es)?\b|\bsocks?\b|underwear|boxer|\bbriefs?\b|"
    r"\bbra\b|bralette|lingerie|\bthong|swim|bikini|insurance|shipping|package protection|\bdonation|"
    r"\bincense|ashtray|\brug\b|\bvase\b|\bcup\b|\bplate\b|\bbowl\b|\btoy\b|\bfigure\b|\bplush|"
    r"(?<!8 )\bball\b(?! cap)|frisbee|\bcd\b|vinyl|\blp\b|cassette|\bdvd\b|zine|"
    r"\bcase\b|airpod|phone|\bumbrella|\bbottle\b|\bflask|\bfragrance|perfume|parfum|\bcandle|"
    r"\bbeauty|lip ?gloss|\bnail|\bhair (clip|tie)|scrunchie|\bgift\b|voucher|\btest\b|chaussette|porte.?cl|pince|chouchou|barrette|[ée]tuis?\b|bo[iî]te|undershirt|\b\d+ ?pack\b|wetsuit|\btable\b|filler|hair accessor|tech accessor|playmat|kendama|dampener|\bsoap\b|shoe ?horn|shoe care|care kit|shoe tree|polishing|shine brush|"
    r"\bbrush\b|\bcloth\b|microfiber|dust bag|\blaces\b|\bpencil|notebook|\bwand\b|halloween|accessories:equipment|"
    r"^offerings\b|^hickies\b|^charms\b"
)

# Checked in order, so "shirt jacket" is outerwear and "dress shirt" and "dress shoes" (rewritten
# below) are a top and shoes.
SLOT_PATTERNS = [
    ("dress", r"dress|gown|jumpsuit|romper|playsuit"),
    ("outerwear", r"jacket|coat|parka|blazer|puffer|vest|gilet|windbreaker|anorak|bomber|trench|"
                  r"overshirt|shacket|outerwear"),
    ("shoes", r"shoe|sneaker|boot|sandal|heel|loafer|mule|slide|trainer|flats|clog|footwear|ballet|"
              r"pump|slipper"),
    ("bottom", r"pant|trouser|jean|short|skirt|skort|legging|jogger|sweatpant|cargo|chino|bottom"),
    ("top", r"tee|t-shirt|tshirt|shirt|top|sweater|sweatshirt|hoodie|hooded|crewneck|crew|knit|"
            r"knitwear|polo|blouse|tank|cami|camisole|bodysuit|cardigan|jersey|longsleeve|pullover|"
            r"jumper|corset|tube|henley|quarter.zip|half.zip|zip.up|bustier"),
    ("accessory", r"hat|cap|beanie|bag|belt|scarf|sunglass|sunglasses|eyewear|jewel|jewelry|bijoux|"
                  r"jewellery|necklace|earring|ring|bracelet|wallet|tote|backpack|gloves?|bandana|"
                  r"headband|visor|accessory|accessorie|bucket|snapback|purse|clutch|tie|cardholder|trucker|balaclava|headwear|fedora|beret|boater|pillbox|cowboy|rancher"),
]
SLOT_RE = [(slot, re.compile(rf"\b(?:{p})(?:e?s)?\b")) for slot, p in SLOT_PATTERNS]
assert {s for s, _ in SLOT_PATTERNS} == set(SLOTS)

COLOR_WORDS = set(COLORS) | {
    "grey", "ivory", "ecru", "sand", "stone", "bone", "chocolate", "coffee", "mocha", "sage",
    "forest", "natural", "oatmeal", "heather", "washed", "light", "dark", "indigo", "multi",
    "leopard", "rose", "mint", "lavender", "teal", "cobalt", "maroon", "wine", "plum", "rust",
    "camel", "taupe", "mustard", "lime", "coral", "peach", "sky", "royal", "jet", "faded",
    "off", "pale", "dusty", "vintage", "acid", "raw", "rinse", "slate", "ash", "smoke", "pewter",
    "olive", "aqua", "fuchsia", "magenta", "lilac", "blush", "nude", "sepia", "espresso", "ink",
    "midnight", "tobacco", "brick", "caramel", "honey", "butter", "lemon", "emerald", "kelly",
    "powder", "baby", "cherry", "scarlet", "crimson", "violet", "mauve", "denim", "print", "floral",
}


def fetch_json(url, state):
    wait = state["last"] + DELAY - time.time()
    if wait > 0:
        time.sleep(wait)
    backoff = 60
    while True:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
            state["last"] = time.time()
            return data
        except urllib.error.HTTPError as e:
            state["last"] = time.time()
            if e.code != 429 or backoff > 480:
                raise
            retry_after = int(e.headers.get("Retry-After") or 0)
            print(f"  429 on {url}, waiting {max(backoff, retry_after)} s")
            time.sleep(max(backoff, retry_after))
            backoff *= 2


def fetch_products(store, state, cache):
    products = []
    for page in range(1, MAX_PAGES + 1):
        cached = cache / f"{store['domain']}_{page}.json" if cache else None
        if cached and cached.exists():
            batch = json.loads(cached.read_text())["products"]
        else:
            url = f"https://{store['domain']}/products.json?limit=250&page={page}"
            print(f"  GET {url}")
            data = fetch_json(url, state)
            if cached:
                cached.write_text(json.dumps(data))
            batch = data["products"]
        products += batch
        if len(batch) < 250:
            break
    return products


def norm(text):
    text = text.lower().replace("_", " ")
    text = re.sub(r"dress (?=shirt|shoe|pant|trouser|boot)", "", text)
    text = re.sub(r"(short|long|cap)[ -]sleeves?", "sleeve", text)
    text = re.sub(r"shirt dress", "dress", text)
    return text


def slot_of(product):
    for text in [product["product_type"], product["title"], " ".join(product["tags"])]:
        text = norm(text)
        for slot, pattern in SLOT_RE:
            if pattern.search(text):
                return slot
    return None


def department_of(product, store):
    words = norm(" ".join([product["product_type"], *product["tags"]]))
    women = bool(re.search(r"\bwom[ae]n'?s?\b|\bladies\b", words))
    men = bool(re.search(r"\bmen'?s?\b|\bmens\b", words))
    if re.search(r"\bunisex\b", words) or (women and men):
        return "unisex"
    if women:
        return "women"
    if men:
        return "men"
    return store.get("department")


def base_name(title):
    name = re.split(r" [-–|/] ", title)[0].strip()
    words = name.split()
    while len(words) > 1 and words[-1].lower().strip("()") in COLOR_WORDS:
        words.pop()
    return " ".join(words).lower()


def plain_text(body_html, limit=300):
    text = html.unescape(re.sub(r"<[^>]+>", " ", body_html or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit].rsplit(" ", 1)[0] + "…" if len(text) > limit else text


def stable_order(handle):
    return hashlib.md5(handle.encode()).hexdigest()


def scrape_store(store, state, cache, drops):
    rate = 1.0 if store["currency"] == "USD" else store["usd_rate"]
    by_slot = defaultdict(list)
    seen = set()
    raw = fetch_products(store, state, cache)
    for p in raw:
        text = f"{p['product_type']} {p['title']}".lower()
        if DROP.search(text):
            drops[store["name"], "non-apparel"] += 1
            continue
        slot = slot_of(p)
        if not slot:
            drops[store["name"], "no slot match"] += 1
            continue
        if not p["images"]:
            drops[store["name"], "no image"] += 1
            continue
        available = [v for v in p["variants"] if v.get("available", True)]
        if not available:
            drops[store["name"], "sold out"] += 1
            continue
        price = round(float(available[0]["price"]) * rate, 2)
        if not 0 < price <= MAX_PRICE:
            drops[store["name"], f"price $0 or over ${MAX_PRICE}"] += 1
            continue
        key = (slot, base_name(p["title"]))
        if key in seen:
            drops[store["name"], "color variant"] += 1
            continue
        seen.add(key)
        by_slot[slot].append({
            "name": p["title"],
            "brand": store["name"],
            "slot": slot,
            "price": price,
            "image": p["images"][0]["src"].split("?")[0],
            "url": f"https://{store['domain']}/products/{p['handle']}",
            "handle": p["handle"],
            "product_type": p["product_type"],
            "tags": p["tags"],
            "description": plain_text(p.get("body_html")),
            "department_hint": department_of(p, store),
        })

    # Round-robin across slots so a store heavy in one slot still gives a spread.
    queues = {s: sorted(items, key=lambda i: stable_order(i["handle"])) for s, items in by_slot.items()}
    cap = store.get("max_items", PER_STORE)
    picked = []
    while len(picked) < cap and any(queues.values()):
        for slot in SLOTS:
            if queues.get(slot) and len(picked) < cap:
                picked.append(queues[slot].pop(0))
    drops[store["name"], "over the store cap"] += sum(len(q) for q in queues.values())
    print(f"  {len(raw)} products in feed, kept {len(picked)}")
    return picked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stores", nargs="*", help="store names to scrape (default: all)")
    parser.add_argument("--cache", type=Path, help="directory to save and reuse raw feed pages")
    args = parser.parse_args()

    stores = json.loads((HERE / "stores.json").read_text())
    if args.stores:
        stores = [s for s in stores if s["name"] in args.stores]
    if args.cache:
        args.cache.mkdir(parents=True, exist_ok=True)

    state = {"last": 0.0}
    drops = Counter()
    items = []
    for store in stores:
        print(store["name"])
        try:
            items += scrape_store(store, state, args.cache, drops)
        except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
            print(f"  skipped: {e}")

    out = HERE / "catalog_raw.json"
    kept = []
    if args.stores and out.exists():
        kept = [i for i in json.loads(out.read_text()) if i["brand"] not in args.stores]
    store_rank = {s["name"]: i for i, s in enumerate(stores)}
    items.sort(key=lambda i: (store_rank[i["brand"]], i["handle"]))
    counters = Counter()
    for item in kept:
        slot, n = item["id"].rsplit("_", 1)
        counters[slot] = max(counters[slot], int(n))
    for item in items:
        counters[item["slot"]] += 1
        item["id"] = f"{item['slot']}_{counters[item['slot']]:03d}"
        del item["handle"]
    items = kept + [{"id": i.pop("id"), **i} for i in items]
    out.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(items)} items to training/catalog_raw.json")
    per_store = defaultdict(Counter)
    for item in items:
        per_store[item["brand"]][item["slot"]] += 1
    for name, slots in per_store.items():
        print(f"  {name}: {sum(slots.values())} " + ", ".join(f"{s} {slots[s]}" for s in SLOTS))
    print("Dropped:")
    for (name, reason), n in sorted(drops.items()):
        print(f"  {name}: {reason} {n}")


if __name__ == "__main__":
    main()
