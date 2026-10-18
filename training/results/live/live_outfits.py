"""Exercise POST /outfits on the running backend the way the app does.

Signs in as a throwaway anonymous Supabase user, saves a profile, asks for outfits in several
situations, prints what a user would see, then deletes the user. Never prints keys or tokens.
Usage: python live_outfits.py <repo dir> <profile_id> [<profile_id> ...]
"""
import json
import sys
import time
from pathlib import Path

import httpx

API = "http://localhost:8000"
repo = Path(sys.argv[1])
env = dict(l.split("=", 1) for l in (repo / ".env").read_text().splitlines() if "=" in l and not l.startswith("#"))
SB_URL, SB_KEY = env["EXPO_PUBLIC_SUPABASE_URL"].strip(), env["EXPO_PUBLIC_SUPABASE_KEY"].strip()
profiles = {p["id"]: p for p in map(json.loads, (repo.parent / "LaHacksAI/training/data/profiles.jsonl").open())}
catalog = {i["id"]: i for i in json.loads((repo / "training/catalog.json").read_text())}
PROFILE_KEYS = ("summary", "style_tags", "colors", "fits", "avoid", "departments", "looks")
CLOSET_KEYS = ("id", "description", "slot", "colors", "formality", "style_tags", "pattern", "fit", "season", "photo_id")


def show(label, res, seconds):
    print(f"\n=== {label}: HTTP {res.status_code}, {seconds:.1f}s")
    if res.status_code != 200:
        print("   ", res.text[:300])
        return None
    body = res.json()
    print(f"    generated_by: {body['generated_by']}")
    for n, o in enumerate(body["outfits"], 1):
        print(f"  {n}. ${o['total']:.2f}  {o['reason']}")
        for i in o["items"]:
            print(f"       - {i['name']} ({i['slot']}, ${i['price']:.2f}, formality {i['formality']}, {', '.join(i['style_tags'])})")
        for c in o["owned"]:
            print(f"       - [owned] {c['description']} ({c['slot']})")
        print(f"       swaps offered for {len(o['swaps'])} item(s)")
    return body


def run(profile_id, client):
    p = profiles[profile_id]
    profile = {k: p[k] for k in PROFILE_KEYS} | {"closet": [{k: c.get(k) for k in CLOSET_KEYS} for c in p["closet"]]}
    print(f"\n##### {profile_id}: {p['summary']}  departments={p['departments']} occasions={p['occasions']} budget ${p['budget_min']}-{p['budget_max']}")
    r = client.put(f"{API}/profile", json=profile)
    assert r.status_code == 200, r.text[:300]

    lo, hi = p["budget_min"], p["budget_max"]
    occ = p["occasions"][0]
    top = next((i for i in catalog.values() if i["slot"] == "top" and set(i["style_tags"]) & set(p["style_tags"])
                and i["price"] <= hi / 3 and (i.get("department") in p["departments"] or i.get("department") == "unisex")), None)
    closet_bottom = next((c for c in p["closet"] if c["slot"] == "bottom"), None)
    asks = [(f"{occ}, no anchor, ${lo}-{hi}", {"budget_min": lo, "budget_max": hi, "occasion": occ})]
    if top:
        asks.append((f"{occ}, catalog anchor '{top['name']}' ${top['price']}",
                     {"budget_min": lo, "budget_max": hi, "occasion": occ, "anchor": {"source": "catalog", "id": top["id"]}}))
    if closet_bottom:
        asks.append((f"{occ}, closet anchor '{closet_bottom['description']}'",
                     {"budget_min": lo, "budget_max": hi, "occasion": occ, "anchor": {"source": "closet", "id": closet_bottom["id"]}}))
    if "athletic" in p["occasions"] or "athletic" not in [a[1]["occasion"] for a in asks]:
        asks.append((f"athletic, no anchor, ${lo}-{hi}", {"budget_min": lo, "budget_max": hi, "occasion": "athletic"}))

    first = None
    for label, req in asks:
        t = time.monotonic()
        body = show(label, client.post(f"{API}/outfits", json=req), time.monotonic() - t)
        first = first or (req, body)
    if first and first[1]:
        req, body = first
        o = body["outfits"][0]
        ids = [i["id"] for i in o["items"]] + [c["id"] for c in o["owned"]]
        t = time.monotonic()
        show(f"make it nicer (upgrade of outfit 1, ${o['total']:.2f})",
             client.post(f"{API}/outfits", json=req | {"upgrade_of": ids}), time.monotonic() - t)


r = httpx.post(f"{SB_URL}/auth/v1/signup", headers={"apikey": SB_KEY}, json={}, timeout=30)
r.raise_for_status()
token = r.json()["access_token"]
with httpx.Client(headers={"Authorization": f"Bearer {token}"}, timeout=180) as client:
    try:
        assert client.get(f"{API}/health").json() == {"ok": True}
        for pid in sys.argv[2:]:
            run(pid, client)
    finally:
        print("\ncleanup: DELETE /me ->", client.delete(f"{API}/me").status_code)
