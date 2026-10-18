# PLAN: an AI stylist that builds whole outfits and checks out safely

Name: **ClosetCue** (it was **As If** until Sunday morning). The name shows in [app.json](app.json) (the app name and the photo and Face ID prompts) and on the welcome screen.

LA Hacks AI Hackathon 2026, team of 2. **Feature freeze about 11:00 AM, submit by 11:30 AM, hacking ends 12:00 PM PDT, Sunday Oct 18.** See [LA_HACKS.md](LA_HACKS.md) for rules, judging and schedule.

This file is the plan of record. The code is the source of truth: when they disagree, fix this file. Last rewritten Sun Oct 18, 06:10 PDT.

## Contents

- [1. Pitch](#1-pitch)
- [2. Track and challenge strategy](#2-track-and-challenge-strategy)
- [3. Product](#3-product)
- [4. Architecture and which model does what](#4-architecture-and-which-model-does-what)
- [5. The model: what we train](#5-the-model-what-we-train)
- [6. How we validate the model](#6-how-we-validate-the-model)
- [7. The training journal: how we explain it to judges](#7-the-training-journal-how-we-explain-it-to-judges)
- [8. Trust, privacy and checkout](#8-trust-privacy-and-checkout)
- [9. Scope: must-have, stretch, later](#9-scope-must-have-stretch-later)
- [10. Who does what, and when](#10-who-does-what-and-when)
- [11. Demo script](#11-demo-script)
- [12. Risks and fallbacks](#12-risks-and-fallbacks)
- [13. Open questions](#13-open-questions)
- [14. Submission checklist](#14-submission-checklist)

---

## 1. Pitch

**One line:** Pick a piece you love, and a small stylist model that we post-trained ourselves builds the rest of the outfit around it from your own style and within your budget, shows it on you, and checks out with a Visa spending limit the agent can't go over.

**The problem.** Online clothes shopping fails in three places:

1. **People think in outfits; stores sell single items.** You find a jacket and then have to work out the shoes, the trousers and what you already own that goes with it.
2. **You can't see it on you until it arrives.** So you guess, and you return it.
3. **Letting an AI buy for you feels unsafe.** A shopping agent that can spend money needs limits you set and can see.

**The user.** Someone who shops online, has a recognizable personal style, and is tired of returns. In the demo it's one of us, with our real photos.

**Why this is a Model Learning project.** The stylist is a 3B open Llama model that we post-trained on Veri. Our reward function encodes what a good outfit is: within budget, only real catalog items, complete, colors, patterns, seasons and formality that go together, and true to the user's style. We measure the base model and each training stage on held-out data, with Gemini as the reference, and with blind human ratings. A small model that follows these rules reliably is fast, ours to run, and small enough that it could one day run on the phone, so photos would never need to leave it.

**Gemini versus our Llama.** Our Llama, post-trained and served on Veri, does one job: pick the outfit and explain why. That's the job we train, measure and pitch. Gemini does what our model can't do or isn't trained for: reading photos into a style profile, tagging the catalog, generating try-on images, and serving as the reference row in the eval. Section 4 has the full table.

---

## 2. Track and challenge strategy

### Main track: Model Learning

The track asks us to "Build systems that learn, adapt, and improve from data. Create innovative models that uncover patterns, make predictions, or solve complex problems." We qualify because the trained model is the core of the product and we can show it improved. Sections 5–7 are the heart of the project.

| Model Learning asks for | What we show |
| --- | --- |
| Learns from data | Supervised fine-tuning (SFT: training on example answers) on the highest-scoring outfits for each training prompt, found by a search over the reward. Then GRPO, a reinforcement learning method that trains against the reward, if time allows. |
| Improves | A held-out eval of base Llama, then SFT (then GRPO), with Gemini as the reference, plus a blind human A/B test. |
| Adapts | Every "which outfit is better?" answer is stored as a preference pair, the data for a DPO round (training on preferred versus rejected answers). DPO itself is a backup-plan item (section 5). |

The judges' likely question is "Why not just prompt Gemini?" The answer has to be numbers: how often each model breaks budget, invents items or loses points on our rules, plus latency. Gemini scores 92.9% of the best possible reward on our prompts but takes a median 25 s per request (section 6). Our model's case is speed, owning the model, and learning the rules Gemini isn't shown (pattern, fit, season and color harmony aren't in the prompt; the reward scores them).

**Why it's worth attempting even though beating Gemini is uncertain.** The Model Learning track and Veri's prize judge the post-training story, not a win over Gemini. The comparison that matters most is against untrained base Llama, where SFT should show large gains. Latency is a near-certain win. The cost is about $5 of Veri credit, and `/outfits` falls back to Gemini, so a weak model can't break the demo.

**Fallback.** If at the **9:30 AM decision** (section 10) the SFT model misses the quality bars in section 6, the app keeps Gemini as the live generator and we report the honest numbers. Switch the Devpost entry to Applied Intelligence only if there's no trained model at all by then. We pick exactly one main track.

### Company challenges

| Challenge | Fit | What it takes from us | Priority |
| --- | --- | --- | --- |
| **veri.studio**, best use of an open model ($800) | Strong. Requirement: "Use our platform to train an open-source model." | Sections 5–7. The training journal doubles as our Veri write-up. | Core |
| **Visa**, Future of Shopping ($2,000) | Strong. It's an AI shopping product end to end. Weights: innovation 25%, UX 25%, technical execution 20%, commerce impact 15%, trust and responsibility 15%. | The spending-limit checkout on a Stripe Issuing virtual card and the trust screen (section 8), plus a commerce-impact claim about fewer returns, with a cited source. | Core |
| **Paper**, Best Designed Hack ($1,500 / $1,000 / $500) | Strong. Fashion is visual, and the judging rewards "personal craft and character" over AI-looking design. | Screens designed in Paper first, with a real style guide, and built to match (`src/theme/`). | Core |
| **Sentry**, Best Use of Sentry (guaranteed interviews) | Good. Needs Sentry plus at least two products beyond error monitoring, and "show how observability shaped what you built". | The app initializes Sentry (`src/lib/sentry.ts`); the backend uses `sentry-sdk`. Add tracing and logs on the model calls, and write "what it showed us". | Medium |
| **MLH Best Use of Gemini API** (Google swag) | Free. We use Gemini for the profile, catalog tagging, try-on and the eval reference. | Mention it on Devpost. | Low effort |
| **MLH Best Domain Name, GoDaddy Registry** (digital gift card) | Good. The site is a landing page that sends people to the app. | Register the domain. One static page with the pitch, the demo video, a QR code that opens the app, and the privacy policy. About an hour. | Must-have (small) |

**Skipped, and why:**

- **Fetch.ai:** the whole workflow has to run inside ASI:One with no custom app.
- **Browser Use:** live product search on the web is slow and flaky in a demo. A curated catalog of real products is safer.
- **Workday, Intuit, QNX, Espressif, Even Realities, Base44, Creao, Photon, StepFun, Cognition:** the problem or the required platform doesn't match.

---

## 3. Product

### Core loop

1. **Open the app.** The welcome screen offers a username and password, or Continue as guest. Supabase signs the user in (email and password under the hood, with each username mapped to `<username>@users.asif.app`, or an anonymous account for a guest). A guest can save a username and password later from Your style and keeps the same account and profile. A signed-in user sees "Continue as <name>".
2. **Style profile and closet from your photos.** You share photos of outfits you wear (see "Getting your photos"). "Next: your style" sends up to 30 of them to `POST /profile`, where Gemini reads them into a style profile you can read and edit ("Mostly neutrals with relaxed fits…", style tags, colors, fits, looks), and lists each garment it sees as a **closet item**, a piece you already own. The profile and closet are saved to your account. Photos are not stored.
3. **Pick an anchor, a budget range and an occasion.** Everything is prefilled, so one tap builds outfits:
   - **Anchor (optional), one of three kinds:** a catalog item you'd buy, a closet item you already own ("find pants for this shirt"), or none. The app suggests the catalog item that best matches your style tags, once per profile; clearing it sticks.
   - **Budget range:** a two-handle slider. Default $50–$200. The checkout spending limit defaults to the maximum.
   - **Max price per item (optional):** in the API and retrieval. Whether Build shows a control is Jasmine's call.
   - **Occasion:** one of 8, default `everyday` (section 5).
4. **Outfit cards.** The stylist returns 2–3 complete outfits built around the anchor, each with a total price and a one-sentence reason. Owned pieces show as "from your closet" and cost nothing. Swap any piece you'd buy, or open it with **View at retailer**. If a fallback model made the outfits, the screen says so.
5. **Try it on.** See the outfit on your own full-body photo (Gemini image editing). The flat-lay view is the fallback.
6. **Checkout under a limit.** The agent proposes a cart. You approve it against a spending limit you set, and the backend refuses anything over it. Confirm with Face ID or the passcode, then see a receipt (section 8). The "Pay with" picker (Apple Pay, Visa, PayPal) is simulated and labeled as a demo.

**Available at any time, outside the loop:**

- **Trust:** what data is used, and Delete my data.
- **Which is better?:** the blind A/B screen (section 6). Pairs are prepared ahead of time from the eval (base Llama against our model on held-out prompts), so it works without a profile. Each answer is a preference pair.

### Getting your photos

Two ways to share photos, as equal options.

| Option | How | Expo package | Status |
| --- | --- | --- | --- |
| **Pick photos** | The system picker, multi-select. On iOS the picker runs outside our app, so it needs no photo-library permission and no face matching: the user already chose photos of themselves. The private option. | `expo-image-picker` | **To build (Jasmine).** Pick → shrink with the scan's thumbnail code → `createProfile` |
| **Scan the camera roll** | Read the 500 newest photos and keep only the ones that show you in an outfit, using outfit detection and face matching. | `expo-media-library` (its `legacy` API), plus pose and face models on the server | Built: [src/app/onboarding/photos.tsx](src/app/onboarding/photos.tsx) |

How the scan works:

1. The app skips screenshots and iCloud-only photos, then shrinks each photo on the phone to a 512 px wide JPEG. Full-size photos never leave the phone.
2. The first time, the app finds the user's face (face matching, below).
3. The app sends the thumbnails to `POST /scan` in batches of 10, with the user's face embedding if there is one. The server returns which photos show the user in an outfit, and how they're framed.
4. The results screen shows the outfit photos and counts. If it found none, it says so and offers to scan again instead of "Next: your style". On iOS a user can grant access to only some photos; the screen then offers "Choose more photos".

### Outfit detection

The server runs a pose model (`yolov8n-pose`) on each thumbnail and labels the framing of each person: **`full`** (a shoulder, a hip, a knee and an ankle visible), **`upper`** (a shoulder and a hip), or **`none`**. A photo counts when its best person is `full` or `upper` and fills at least 25% of the photo's height. With no face chosen, photos with more than 3 people are skipped. With a face chosen, only people whose face matches count. [backend/SCAN_FIXES.md](backend/SCAN_FIXES.md) has the full rules.

### Face matching ("only look at photos of me")

Matching your face against your photos, not identity verification. No selfie: in your own camera roll, the face that shows up most is usually yours.

1. The app sends its 80 newest thumbnails to `POST /faces/find-owner`.
2. The server finds every face (MTCNN) and turns each into a face embedding, 512 numbers that summarize a face (FaceNet, `InceptionResnetV1`, VGGFace2 weights).
3. It returns up to 3 face groups that appear in at least 2 photos, most frequent first, each with a crop.
4. The app asks **"Is this you?"** for each in turn. "None of these" turns face matching off for this scan.
5. Every `/scan` request then carries the user's embedding, and the server keeps only people whose face is close enough (similarity ≥ 0.6).
6. The embedding lives only in the app's memory for the session. "Not you? Reset my face" clears it. The server stores nothing.

It runs on the server for the demo. On-device matching is the production design (it needs a development build). **Decision (Oct 18): no separate consent screen.** "Pick photos" is the option for users who don't want the scan; the trust screen and privacy policy say what the scan computes. Tell judges plainly that finding your face computes embeddings for everyone in the 80 photos and stores none of them.

### Screens

Designed in Paper. The first six are the demo path.

1. **Welcome:** sign in, create an account, or continue as guest; what we read and what we keep.
2. **Share your photos:** pick photos or scan the camera roll, with the "Is this you?" card inline.
3. **Your style:** the editable summary, style tags, colors, "Fits you wear", "Leave out" (the `avoid` list), looks, and the closet (remove a wrongly tagged garment). Also where a guest saves their account.
4. **Build:** anchor (suggested), two-handle budget range slider, occasion.
5. **Outfits:** 2–3 cards, total price, reasons, owned pieces marked "from your closet", swap a piece, "make it nicer".
6. **Try-on:** your photo wearing the outfit, plus a flat-lay view.
7. **Checkout:** the cart, the spending limit, the agent card, the simulated "Pay with" picker, confirm, and the receipt.
8. **Which is better?:** the blind A/B screen.
9. **Trust:** what data is used, Delete my data, AI use policy, merchant impact.

There is no "How did it fit?" screen: the app can't know when an order arrives, and no real order is placed.

### Routes

Every file in `src/app/` is a screen in Expo Router. Build is `(tabs)/build.tsx`, not `(tabs)/index.tsx`, because `index` would claim `/`, which the redirect uses.

```
src/app/
├── _layout.tsx              root Stack (welcome and photos have no header)
├── index.tsx                always redirects to the welcome screen
├── onboarding/
│   ├── welcome.tsx          1. Welcome: sign in, create an account, continue as guest, or "Continue as <name>"
│   └── photos.tsx           2. Share your photos, then POST /profile on "Next: your style"
├── (tabs)/
│   ├── _layout.tsx          tab bar: Style · Build · Rate · Trust
│   ├── style.tsx            3. Your style (also where onboarding lands)
│   ├── build.tsx            4. Build
│   ├── rate.tsx             8. Which is better?
│   └── trust.tsx            9. Trust
├── pick-item.tsx            modal: the anchor from the catalog or your closet, or none
├── outfits.tsx              5. Outfits
├── tryon/[outfitId].tsx     6. Try-on
└── checkout/
    ├── index.tsx            7. Checkout, including the refusal and the "Pay with" sheet
    └── receipt.tsx          receipt and what's left of the mandate
```

An account that already finished onboarding skips the photo screen (`src/lib/onboarding.ts`: a per-account flag on the phone, or a saved profile from `GET /profile`).

---

## 4. Architecture and which model does what

### Which model does what

Rule of thumb: **our Llama does the job we trained it for; Gemini does what our model can't do or wasn't trained for.**

| Job | Model | Why |
| --- | --- | --- |
| Pick and explain the outfit | **Our Llama, on Veri** | The trained task. It's what the eval measures and the judges score. |
| Read photos into a profile and closet | Gemini | Needs vision. Veri's trainer is text-only. |
| Tag the catalog | Gemini (`gemini-3.8-flash`) | Reads each product's title and photo into the fixed vocabularies. Done. |
| Try-on image | Gemini image editing | Needs image generation. Needs billing on the key's Google project: on the free tier, image models have a quota of 0. |
| SFT answers | **No model:** a search over the reward finds each prompt's best outfits, and a template writes the reasons | Saves the Gemini free-tier quota for the demo, and the answers score near the maximum by construction. |
| Reference row in the eval | Gemini | Shows how close our 3B model gets to a frontier model. |
| Fallback when Veri is down | Base Llama, then Gemini | Labeled in the app so we never pass Gemini off as our model. |

### System

```
Expo app (Expo Router)                 FastAPI backend                      Models and data
─────────────────────                  ───────────────                      ───────────────
sign-in (username or guest) ─────────────────────────────────────────────▶ Supabase Auth
newest photos ─────────────────────────▶ POST /faces/find-owner ─────────▶ face models: most common faces
thumbnails + your face ────────────────▶ POST /scan ─────────────────────▶ pose + face models: photos of you in outfits
outfit photos (≤ 30) ──────────────────▶ POST /profile ──────────────────▶ Gemini: profile + closet
                                          vocab-checked, saved ──────────▶ Supabase: profiles
edit profile ──────────────────────────▶ GET, PUT /profile ──────────────▶ Supabase: profiles
browse, anchor ────────────────────────▶ GET /catalog ───────────────────▶ training/catalog.json
anchor, budget range, make it nicer ───▶ POST /outfits ── candidates ────▶ Veri: our Llama 3B (then base Llama, then Gemini)
                                          retrieve, call, guard, retry once
photo + items ─────────────────────────▶ POST /tryon ────────────────────▶ Gemini image editing
cart ──────────────────────────────────▶ POST /checkout/mandate, /cart, /confirm ▶ Stripe Issuing (sandbox): card with a spending limit
A/B choice ────────────────────────────▶ GET /rate/next, POST /rate ─────▶ backend/data/rate_pairs.jsonl; Supabase: feedback
trust screen ──────────────────────────▶ DELETE /me ─────────────────────▶ Supabase: delete user's rows and account
                 Sentry on both sides
```

- **App:** this repo. Expo SDK 57, TypeScript, Expo Router (see [AGENTS.md](AGENTS.md)). `src/api/client.ts` answers from `src/api/mocks.ts` unless `EXPO_PUBLIC_USE_MOCKS=false`; `/tryon` always calls the real backend.
- **Backend:** FastAPI in `backend/`, run from the repo root with `uvicorn backend.main:app --host 0.0.0.0 --port 8000`. For the demo it runs on a laptop behind a tunnel. The pose and face models run in the server process, on CPU.
- **Supabase** stores accounts, profiles, feedback and mandates ([backend/supabase_schema.sql](backend/supabase_schema.sql)):
  - **Sign-in:** username and password, or anonymous for guests. Needs "Confirm email" **off** and "Allow manual linking" **on** in the Supabase dashboard; the app checks the first and shows an error if it's on.
  - Tables: `profiles` (the style profile and closet as JSON), `feedback` (A/B choices, with the pair shown and which model made each side), `mandates`.
  - The phone only talks to Supabase to sign in. Reads and writes go through the backend, which checks the access token and holds the service key. Delete my data deletes the user's rows and the account.
- **Secrets:** Gemini, Veri, Supabase service and Stripe secret keys live only in `backend/.env` (template: `backend/.env.example`). The app's settings go in the root `.env`, and everything in it ships inside the app. The repo goes public for submission.
- **The guard:** the backend runs the reward's checks on every model answer (section 5).

### Repo layout

```
LaHacksAI/
├── package.json, app.json, tsconfig.json   the Expo app
├── src/
│   ├── app/          routes only (section 3)
│   ├── components/   AccountCard, AccountFields, PaySheet, RangeSlider, Placeholder, logos, ui
│   ├── api/          client.ts, types.ts, mocks.ts (18 real catalog products with their real ids)
│   ├── lib/          session.tsx, supabase.ts, onboarding.ts, photos.ts, payment.ts, confirm.ts, sentry.ts
│   └── theme/        Paper style guide tokens: colors, type, spacing, radii, swatches, brands
├── backend/
│   ├── main.py, schemas.py, supabase_schema.sql, requirements.txt, .env.example
│   ├── routes/       profile, outfits, catalog, rate, tryon, checkout, me, scan, faces
│   ├── services/     gemini, veri, supabase, stripe_issuing, catalog, tryon, pose, faces, images
│   ├── build_rate_pairs.py   two models' eval answers → data/rate_pairs.jsonl
│   └── test_profile.py, test_outfits.py, test_rate.py, test_framing.py
├── training/
│   ├── stores.json, scrape_catalog.py, catalog_raw.json   the store list and the raw pull
│   ├── tag_catalog.py, catalog.json   Gemini's tags; the server reads catalog.json too
│   ├── vocab.py      slots, colors, style tags, patterns, fits, seasons, occasion formality
│   ├── prompt.py     the one prompt builder, used by build_prompts and /outfits
│   ├── retrieval.py, reward.py   shared with the server
│   ├── gen_profiles.py, build_prompts.py, eval.py   (gen_sft.py next)
│   ├── data/         profiles and prompts; gitignored, rebuilt by script (section 5)
│   ├── results/      eval answers and summaries, committed
│   ├── test_*.py
│   └── JOURNAL.md
└── README.md, PLAN.md, LA_HACKS.md, JANGES_FOR_JASMINE.md, CHANGES_FOR_CHARLIE.md
```

Planned: `training/gen_sft.py`, Veri configs under `training/configs/`, and the landing page.

Rules that matter more than the exact folders:

- **One copy of `catalog.json`, `prompt.py`, `retrieval.py` and `reward.py`.** The same reward trains the model and guards live answers, and the same prompt and retrieval build training prompts and live prompts, so the model meets the same inputs in the app as in training. Veri runs `reward.py` as a single file, so it carries its own copy of the vocabularies from `vocab.py`; `test_reward.py` fails if the two drift.
- **API shapes in two places:** `backend/schemas.py` and `src/api/types.ts`. A contract change updates both, plus `mocks.ts`, and gets a note to the other person (JANGES_FOR_JASMINE.md or CHANGES_FOR_CHARLIE.md).
- **One file per endpoint in `backend/routes/`**, so both of us can work on the server without conflicts.

Tests: `python3 -m pytest -q training/ backend/test_profile.py backend/test_outfits.py backend/test_rate.py`; app: `npx tsc --noEmit` and `npx expo lint`.

---

## 5. The model: what we train

### Task

Input: the style profile, budget range, occasion, the anchor (if any), and a candidate list that `training/retrieval.py` picked from the catalog. Output: strict JSON, no code fences.

```json
{
  "outfits": [
    {
      "items": ["closet_3", "bottom_004", "shoes_009", "outerwear_002"],
      "total": 186.0,
      "reason": "One short sentence a person would say."
    }
  ]
}
```

`items` lists every piece, the anchor included. A closet anchor appears by its `closet_<n>` id and adds nothing to `total`, the sum of the catalog items only. The prompt states the budget as a hard limit next to the output instructions; before that fix, Gemini went far over budget.

The backend retrieves; the model chooses and explains. That keeps prompts short enough for a 3B model and makes every rule checkable.

**Three kinds of prompt, one pipeline:** a catalog anchor, a closet anchor, or none, mixed about 45% / 35% / 20%. Same prompt builder (`training/prompt.py`), retrieval and reward for all three.

**What the prompt shows and what the reward scores.** Each candidate line shows id, name, slot, price, colors, formality and style tags. The reward also scores pattern, fit, season and color harmony, which the prompt doesn't spell out. Gemini has to guess those; our model learns them from the SFT answers. That's our model's main way to beat Gemini on reward.

**Candidate list size.** The catalog is every product we have (1,040). The candidate list is the slice one prompt shows the model. Each item is about 30 tokens, so 25 items is about 1,000 tokens and 100 is about 4,000. The prompts are built with 25, 50, 75 and 100 candidates. **Current plan:** train on the 25- and 50-candidate rows only, which makes SFT and GRPO faster; the live default is 50. The backup plan trains on all four sizes and measures 150 and 200 too.

### Retrieval

`training/retrieval.py`, used by both `build_prompts.py` and `/outfits`. Deterministic.

1. **Filter out** items that can't work: the anchor's slot (accessories excepted; a dress anchor also drops tops and bottoms, and a top or bottom anchor drops dresses), items priced above `budget_max` minus the anchor's price (a closet anchor costs $0), items above `max_item_price`, departments the profile doesn't shop (unisex always passes; empty `departments` means shop everything), dresses for a men-only profile, anything with a style tag or color on the `avoid` list, and items more than one formality level outside the occasion's range, or outside it at all for work (accessories included). There is no `budget_min` filter.
2. **Score** the rest: shared style tags, plus 0.5 if any color is one the user wears, plus 0.5 if its fit is one of the profile's `fits`. Ties break by id.
3. **Keep the top N, split across slots:** tops 25%, bottoms 25%, shoes 20%, outerwear 12%, dresses 10%, accessories 8%, renormalized over slots that have items, with a diversity cap (at most two items in a slot sharing both a color and a style tag; never relaxed). A short slot's places go to the best items left anywhere.
4. **Leave some imperfect options in:** about 15% of each slot's places come from the lower-scoring half, so the model does real choosing.

The result is sorted by slot, then id. Swaps on the outfit cards come from the whole catalog, computed by the backend after the model answers.

### Occasions

Each occasion has a formality range that retrieval and the reward use (`OCCASION_FORMALITY` in `training/vocab.py`, copied in `reward.py`).

| Occasion | Formality |
| --- | --- |
| `formal` | 4–5 |
| `semi-formal` | 4–5 |
| `work` | 3–4 |
| `everyday` | 2–4 |
| `party` | 2–4 |
| `casual` | 1–3 |
| `athletic` | 1–2 |
| `comfy` | 1–2 |

`formal` shares `semi-formal`'s range because no shoe is tagged 5. **`comfy` was widened from 1 to 1–2 on Oct 18:** only 5 shoes are tagged 1, so no comfy prompt could reach the full score, and comfy is the most common occasion in the eval set. After the change, the average best possible score over the 200 eval prompts rose from 6.82 to 7.03, and prompts below 6.0 fell from 21 to 9. Formal and semi-formal prompts still top out around 5.1–5.2: the catalog has few formality-4 shoes and none at 5 (section 13).

### Base model

`unsloth/Llama-3.2-3B-Instruct`, an **ungated mirror** on Hugging Face (gated `meta-llama/*` repos fail after the GPU has booted and started billing). Trains on one L4 and serves on one L4. The Oct 18 smoke runs confirmed Veri trains it and pushes merged weights (`training/JOURNAL.md`).

### Catalog

**1,040 real products** (real brand, price, image and product-page URL) from **24 US-dollar stores**, pulled Oct 18, in `training/catalog.json`: 207 tops, 185 bottoms, 133 dresses, 147 outerwear, 161 shoes, 207 accessories; 504 women's, 368 men's, 168 unisex; $4–$998.

1. **Stores** (`training/stores.json`): Shopify stores with a public `products.json` feed, from streetwear (Stüssy, Brain Dead, Kith) to menswear (Taylor Stitch, Todd Snyder), activewear (Alo Yoga, Set Active, Outdoor Voices), womenswear (Christy Dawn, Edikted, Princess Polly), shoes (Allbirds, Thursday Boot Co., Koio, Birdies, Steve Madden), jewelry (Gorjana), and formal wear (Jack Victor, Paul Evans, Mac Duggal). Decisions: US-dollar stores only, English names only, **no Brixton** (its terms ban AI training by name). Bonobos is in the list but returns HTTP 500 partway through its feed, so it has no items.
2. **`scrape_catalog.py`** maps product types to six slots, keeps one price and image per product, sets `url` to the product's own page, drops color variants, and caps each store (50 by default, lower via `max_items`). Requests go strictly one at a time, at least 3.5 s apart: a parallel run once got our IP blocked across all of Shopify. Add a store: append it to `stores.json`, run `python -m training.scrape_catalog --stores "<name>"` (keeps every other item's id), then `python -m training.tag_catalog`.
3. **`tag_catalog.py`** had Gemini (`gemini-3.8-flash`, 84 calls) tag each item's `department`, `colors`, `formality`, `style_tags`, `season`, `pattern` and `fit` from its title and photo, choosing only from `training/vocab.py`, with every answer validated against the vocab. Button-ups and dress shirts are rated dressy (formality 4).

```json
{
  "id": "top_012", "name": "Relaxed cotton crewneck", "brand": "…",
  "slot": "top", "department": "unisex", "price": 38.0,
  "colors": ["cream"], "formality": 2, "style_tags": ["minimal"],
  "season": ["fall", "winter", "spring"], "pattern": "solid", "fit": "relaxed",
  "image": "https://…", "url": "https://…"
}
```

Vocabularies, in `training/vocab.py`:

- **Colors (25),** in three groups. Neutrals: white, cream, beige, tan, khaki, brown, gray, charcoal, black. Versatiles: navy, denim, olive, blue, forest-green, muted-green, burgundy, light-blue, lilac, gold, silver. Accents: yellow, orange, red, pink, purple.
- **Style tags (17,** 1 to 3 per item): minimal, old-money, western, preppy, streetwear, techwear, workwear, outdoors, athleisure, bohemian, y2k, goth, coastal, sporty, clean-girl, soft-girl, grunge.
- **Patterns:** solid, stripe, check, small-print, large-print, graphic. Check, large-print and graphic are loud.
- **Fits:** slim, regular, relaxed, oversized, for tops, bottoms, dresses and outerwear. Shoes and accessories have none.

Changing a list means re-tagging the catalog and regenerating the training data.

### Data

All built by code with fixed seeds, no AI, and rebuilt byte for byte in under a second, so `training/data/` is gitignored (the files are about 23 MB and went stale once when the catalog changed mid-build):

```
python -m training.gen_profiles --n 400 && python -m training.build_prompts
```

(`gen_profiles` defaults to 20 profiles, so `--n 400` is required.)

1. **Profiles** (`gen_profiles.py`): 400 synthetic profiles across styles, departments, budgets (minimum $0–$150, maximum $60–$400), occasions and `avoid` lists, each with a templated summary and a closet of 25 items (30 when the profile wears dresses). Charlie reviewed them.
2. **Prompts** (`build_prompts.py`): 2 per profile, split **by profile** 75/25 → **600 training rows (300 profiles) and 200 eval rows (100 profiles)**; no profile is in both. Anchor mix 45/35/20, candidate sizes 25/50/75/100. Rows are interleaved in shuffled rounds, so the first N eval rows come from N different profiles. `veri datasets check` passes on both files. 190 of 200 eval rows allow a complete outfit.
3. **Row format:** `{"messages": [system, user], occasion, budget_min, budget_max, anchor, candidates, profile_style_tags, profile_fits, profile_avoid, profile_id}`: the chat prompt plus the reward's context columns (`reward.CONTEXT_COLUMNS`).
4. **SFT answers** (`gen_sft.py`, next): for each training row, `build_prompts.best_outfits` finds the 3 best distinct outfits (about 2 minutes for 600 rows), and a template writes each one-sentence reason naming an item. Keep only answers that score near the maximum with `reward.score_completion`. Plain JSON, no fences.

Veri needs one prompt format per JSONL file; mixing formats crashes the trainer after the GPU boots.

### Reward function: our definition of a good outfit

`training/reward.py`. Deterministic, fast, standard library only, because Veri runs it inside the trainer as a single file. Each row's context arrives as dataset columns in `**kwargs`.

| Check | Score |
| --- | --- |
| Output is exactly the JSON schema: one `outfits` key holding 1–3 outfits, each with exactly `items`, `total` and `reason`. JSON in code fences fails | Gate: 0 overall |
| Every item ID is in that prompt's candidate set or is the anchor (no invented items) | Gate: 0 for that outfit |
| Includes the anchor (full score when there is none) | +1 |
| Complete outfit: top + bottom, or a dress with neither, plus exactly one pair of shoes; at most one outerwear; no repeated IDs | +1 |
| Total of catalog items is within `budget_min`–`budget_max` (pass or fail), and the stated total is within $0.01 of the real sum. Closet items count as $0 | +1 |
| Color harmony: the lowest score of any two different colors, by group (neutral with neutral or versatile 1, neutral with accent 0.9, versatile with versatile 0.9, versatile with accent 0.75, accent with accent 0.6); one color scores 1 | 0.6 to +1 |
| Pattern: at most one loud pattern | +0.5 |
| Season: the items share at least one season | +0.5 |
| Formality: all items, anchor included, within 1 level of each other and inside the occasion's range (pass or fail) | +1 |
| Matches the profile: the mean over non-anchor items of their style-tag and fit matches; 0 if any item has a tag or color from `avoid` | 0 to +1 |
| Reason is one sentence of at most 40 words and names an item (by ID, or a 4+ letter word from its name that isn't a color or tag). "Dr.", "St.", "Jr." and similar don't end a sentence | +0.5 |

One outfit scores at most 7.5. A completion's reward is the sum of its outfits' scores divided by 3, so a missing, failed or duplicate outfit counts as 0. Bad outfits still earn about 3 of 7.5. **Known gap:** nothing stops "always pick the cheapest items"; add a budget-use bonus only if GRPO finds that trick.

**The live guard** (`backend/routes/outfits.py`). The same code checks every live answer: it drops outfits that fail a gate or score 0 on anchor or budget (except for "make it nicer"), recomputes every total from catalog prices, and retries once if fewer than 2 outfits survive. A network or quota error skips the retry. Then it falls back to base Llama, then Gemini, setting `generated_by`. If no model reaches 2 good outfits, it returns the best partial answer; a 503 only when nothing survives. No profile: 404. An unknown anchor: 422. The Veri models are configured by `OUR_LLAMA_*` and `BASE_LLAMA_*` in `backend/.env` (`_URL`, `_NAME`, `_API_KEY`). The guard does **not** drop incomplete outfits, since completeness isn't a gate (section 13).

### Training runs: current plan

Time-boxed so a usable model exists by the 9:30 decision, while still aiming for the best model we can get.

1. **`gen_sft.py`:** solver answers with templated reasons, on the 25- and 50-candidate training rows (step 4 of Data).
2. **v0 baseline:** deploy base Llama (`--min-replicas 0`) and run the eval on the same prompts as everyone else. About $0.50. Runs while SFT trains.
3. **v1-sft:** `sft_text`, LoRA, merged push to Hugging Face. A 5-step smoke run first, because prompts are now up to about 4,000 tokens and `max_seq_length` must cover them. About $1–2.
4. **Deploy v1-sft, eval it,** decide at 9:30 against the bars in section 6.
5. **v1-grpo,** only if SFT passes the bars and there's time: from the SFT checkpoint, `max_steps` 50, 4 rollouts per prompt. About $2. If it isn't done by the freeze, ship SFT.

Skipped for now: training on 75- and 100-candidate rows, the candidate-size table, and v2-dpo.

### Training runs: backup plan, if there's more time

The original full plan, to pick up after the hackathon or if the current plan finishes early:

- Train on all four candidate sizes (25, 50, 75, 100), and measure accuracy at 25–200, including 150 and 200 that it never trained on, to pick the live candidate size.
- SFT reasons written by Gemini (or base Llama) instead of a template.
- GRPO for about 100 steps with 4–8 rollouts per prompt.
- Eval on all 200 held-out prompts, for every model, including Gemini.
- v2-dpo from the A/B answers collected at the event.

### Veri facts

- Account balance **$19.65** (L4 is $1.05 per GPU-hour). Hugging Face account: **CharlieBrown364**.
- In a training TOML the Hugging Face table is **`[huggingface]`** with `repo`, `artifact = "merged"` and `private = false`, because Veri can't serve a bare LoRA adapter. The veri skill's `[hf_push]` is wrong: the CLI silently ignores unknown tables, which is why smoke run 1 pushed nothing.
- `veri jobs estimate` validates nothing (it prices a nonexistent model), so only a real run proves a config. Price every run first anyway and get Charlie's OK before anything that spends credits.
- Run `veri datasets check` before uploading. Serve with `--min-replicas 0` and stop deployments that aren't in use.
- This config ran and pushed (job 633352df677e):

  ```toml
  kind = "train"
  [job]
  name = "llama-smoke-test-2"
  [model]
  base = "unsloth/Llama-3.2-3B-Instruct"
  [dataset]
  id = "<dataset id from veri datasets upload>"
  [method]
  type = "sft_text"
  learning_rate = 1e-4
  max_steps = 5
  max_seq_length = 1024   # raise to cover the longest prompt plus answer
  lora_rank = 16
  lora_alpha = 32
  [resources]
  gpu_type = "L4-24GB"
  gpu_count = 1
  [provider]
  name = "aws"
  [huggingface]
  repo = "CharlieBrown364/llama-smoke-test"
  artifact = "merged"
  private = false
  ```

---

## 6. How we validate the model

We don't trust a number until we've checked it ourselves. Five layers, cheapest first:

1. **Reward unit tests** (`training/test_reward.py`): hand-written outfits that must rank the way we would.
2. **Data checks:** `veri datasets check` on every file; no eval profile in training data; read 10 random rows.
3. **Automatic eval** (`training/eval.py`) on held-out prompts: same prompts and settings for every model. Each answer is also scored against its row's best possible score (from `build_prompts.best_outfits`, a strong lower bound on the true maximum).

   ```
   python -m training.eval --model gemini|base-llama|our-llama --data training/data/prompts_eval.jsonl --limit 50 --out training/results
   ```

4. **Read the outputs** after each run: 20 random answers and the 10 highest-reward ones, where reward hacking shows up. If we find a hack, fix the reward, log it, rerun.
5. **Blind human A/B test** on the "Which is better?" screen: base Llama against our model on held-out prompts, in random order with no labels. Build the pairs from two eval runs over the same prompts: `python -m backend.build_rate_pairs training/results/base-llama.jsonl training/results/our-llama.jsonl --labels v0-base v1-sft`. Report the win rate.

**Quality bars for shipping our model** (agreed Oct 18): at least 90% of answers valid JSON with nothing invented, at least 80% of answers keeping 2+ outfits through the live guard, and at least 85% of each row's best possible reward.

### Gemini reference: first results

20 eval prompts, before the comfy change (`training/results/gemini*.jsonl`, commit 9ea68f7). 19 answered; 1 timed out at 60 s.

| Metric | Gemini |
| --- | --- |
| Valid JSON, nothing invented | 100% |
| Complete outfits / anchor included | 100% / 100% |
| Within budget (real prices) | 94.7% |
| Answers with 2+ outfits kept by the live guard | 94.7% |
| Mean reward | 6.52 of 7.5 |
| Share of each row's best possible reward | 92.9% |
| Median / p90 latency | 25 s / 57 s |

Gemini passes every quality bar and fails on speed. What the answers show:

- **Where it loses points:** formality (mean 0.74 of 1), profile match (0.69 of 1), color (0.83 of 1), pattern and season (about 0.4 of 0.5 each). Most formality zeros were comfy prompts that couldn't pass at formality 1, now fixed. Pattern and season aren't in the prompt; that's where our model can gain.
- **Budget:** the hard-limit line worked. A smoke run before it had Gemini at $478–$502 on a $20–$270 budget; now 1 of 19 answers went over (a $30–$100 budget with a catalog anchor already in it; the guard dropped all 3 outfits).
- **Latency** isn't tied to candidate count: 25-candidate prompts were as slow as 100. An untested guess is Gemini's default "thinking"; try a lower thinking budget in `backend/services/gemini.py` on about 5 prompts.
- **The outfits read well:** a believable Y2K party look, and athletic streetwear built on the user's own closet jeans.

**Rerun it before comparing:** the comfy change regenerated the prompts, so this run's rows no longer match the current eval file. Rerun Gemini on the same 50 rows as the other models.

### The eval table that carries the pitch

Fill it in from real runs only, all on the same 50 held-out prompts.

| Metric | v0 base Llama | v1-sft | v1-grpo | Gemini (reference) |
| --- | --- | --- | --- | --- |
| Valid JSON, nothing invented | | | | |
| Complete outfit | | | | |
| Within budget | | | | |
| Answers with 2+ outfits kept | | | | |
| Mean reward / share of best possible | | | | |
| Human A/B win rate against v0 | n/a | | | |
| Median latency per request | | | | |

If GRPO doesn't beat SFT, report that and ship SFT. An honest negative result with a clear explanation still scores, and judges trust the other numbers more.

---

## 7. The training journal: how we explain it to judges

**`training/JOURNAL.md`** gets an entry for every decision and every run, written when it happens, failed runs included. Every run records its Veri job ID, the git commit of `reward.py` and the data, the cost, and the result, so anyone can rerun it. "We found the model gaming the reward and fixed it" is one of the strongest things we can tell a Model Learning judge.

Entries still to write: the Gemini eval and what it changed (the budget line, the comfy range), and every run from here on.

**Turning it into the pitch.** Condense the journal into a five-step story for Devpost, the README and one slide:

1. We defined the task and an output schema.
2. We wrote down what a good outfit is, as a reward function, and tested it.
3. We generated training data and filtered it with the reward.
4. We trained in stages and fixed what the outputs showed us.
5. We measured it two ways (automatic eval, blind human test) and kept collecting preference data.

---

## 8. Trust, privacy and checkout

Trust is 15% of Visa's score and the main worry people have about agents that spend money, so it gets real screens.

**Photos and accounts**

- You choose what to share: specific photos (no library permission needed), or a scan of your 500 newest photos. Only small thumbnails leave the phone.
- Finding your face during the scan computes face embeddings for everyone in your 80 newest photos. None are stored. Your own embedding stays in the app's memory for the session.
- Photos are processed for one request and not stored. Only the profile and closet are kept, and you can read and edit both.
- Delete my data deletes your profile, closet, ratings and spending limits, and the account, then signs you out.

**Checkout: a spending mandate the agent can't exceed**

A **mandate** is a set of rules you give the agent before it can buy: how much it may spend, on what, and for how long. The idea follows Visa's agentic commerce work, where an agent gets a limited payment token instead of your card.

**Payments run on Stripe Issuing, in Stripe's sandbox.** Stripe Issuing lets our backend *create* a virtual card (the opposite of the usual Stripe flow, where you charge a customer's card) and set spending controls on the card itself: a maximum amount and the merchant categories it may be used at. Each mandate gets its own card, so the agent holds a card that can't overspend, never the user's card. Everything runs with test keys; no real money moves, and we say so on screen and on Devpost. **Jasmine owns this.** Today the three routes in `backend/routes/checkout.py` and `backend/services/stripe_issuing.py` are outlines that return 501; the app's checkout works only on mocks.

1. You set the mandate: at most $200, apparel only, expires in 24 hours. The limit defaults to the budget maximum from Build. `POST /checkout/mandate` creates an Issuing virtual card with `spending_controls` (a `spending_limits` entry of the limit with interval `all_time`, and `allowed_categories` set to clothing stores) and stores the mandate (`supabase.create_mandate`).
2. The agent only ever holds a **card reference** (`Visa •••• <last 4>, agent card`), never the card number.
3. `POST /checkout/cart` checks the cart against the mandate in our code first, with the total from **catalog** prices: refused "expired", "not_apparel" or "over_limit" (naming the amount over, with the closest outfit that fits as a suggestion).
4. You confirm with Face ID or the passcode (`expo-local-authentication`).
5. `POST /checkout/confirm` runs the same check, then makes a simulated purchase on the card (Stripe's test helper for Issuing authorizations). Stripe approves or declines against the card's own limit, so the limit holds even if our check had a bug. Then it adds the total to `spent` and cancels the card.
6. The receipt shows what was bought, what's left of the mandate and the Stripe authorization ID, says "Demo: no order was placed and no money moved", and links each item to its real product page.

The "Pay with" picker in checkout (Apple Pay, Visa, PayPal) is a separate, simulated choice for the user's own payment method; it changes labels only.

**Fallback.** If Issuing isn't available on the sandbox account, the mandate is enforced in our code only, the card reference is a fixed test card (`Visa •••• 4242`), `Receipt.authorization_id` is null, and the app labels the payment as simulated (the receipt screen already does this). Build this path first: it makes the refusal demo work without Stripe, and Issuing adds to it.

**Production design.** No order reaches a store. In production the agent would order through each store's **Agentic Commerce Protocol (ACP)** checkout and pay with a Stripe **Shared Payment Token**, limited to one store, a maximum amount and an expiry. The mandate maps onto those limits almost one to one.

**Demo moment:** you say "make it nicer", the agent proposes an upgrade that pushes the cart past your $200 limit, and the backend refuses it and says why. "Make it nicer" is `POST /outfits` with `upgrade_of` set to the current outfit's item ids: one outfit priced in (F, F + $150], where F is the larger of that outfit's total and `budget_max`. It's the one request allowed past `budget_max`, and it always goes past it, so the mandate (which defaults to `budget_max`) refuses it.

**Merchant impact panel:** outfit-level selling raises basket size, and trying an outfit on should cut returns. Cite a real source for return rates. Don't invent numbers.

---

## 9. Scope: must-have, stretch, later

**Must-have**

- [x] Catalog of 1,040 real products, tagged
- [x] Reward with tests, retrieval, profiles and prompts (600 train / 200 eval)
- [x] `/profile`, `/catalog`, `/outfits` with the guard and fallbacks, `/rate`
- [x] Sign-in (username or guest), the scan with face matching, Your style, Build, Outfits, Trust with Delete my data
- [ ] SFT answers, v1-sft trained, deployed and evaluated; the eval table and journal (Charlie)
- [ ] Mandate checkout with a refusal: the fallback first, then Stripe Issuing (Jasmine)
- [ ] Pick photos (Jasmine)
- [ ] The A/B screen with real pairs (needs two models' eval answers)
- [ ] Try-on on one photo, with the flat-lay as a fallback (needs billing on the Gemini key's project)
- [ ] The whole demo path end to end with mocks off, on a real phone (Jasmine)
- [ ] Landing page on a GoDaddy Registry domain: pitch, demo video, QR code, privacy policy (Jasmine)

**Stretch, in this order**

1. v1-grpo (section 5)
2. **Closet items as candidates, not just the anchor:** "you already own shoes that work". `Outfit.owned` already carries them to the app
3. Sentry tracing, logs and AI monitoring, with a written "what it showed us"
4. Screenshots as inspiration: tag them "inspiration" instead of skipping them

**Later:** the backup training plan (section 5), makeup recommendations, sharing outfits, social media, live web product search.

---

## 10. Who does what, and when

**Charlie: model and backend.** `gen_sft.py`, the Veri runs, the eval and the journal, the Gemini latency fix, `/outfits`, `/profile`, `/catalog`, `/rate`, and the model half of Devpost.
**Jasmine: design, app and her backend routes.** Every screen, Pick photos, `/checkout` with Stripe Issuing (fallback first), `/tryon`, `DELETE /me`, `/scan`, `/faces/find-owner`, Sentry, the domain and landing page, the demo video, and the app half of Devpost and the README.

**Staying unblocked:** contract changes go in both `schemas.py` and `types.ts` with a note to the other person; one file per endpoint; pull before touching `main.py`, `schemas.py` or `supabase.py`; push small commits to `main` often.

Times are PDT, Sunday.

| When | Charlie | Jasmine |
| --- | --- | --- |
| **6:15–7:15** | Write `gen_sft.py` and check its answers score near the max. Rerun the Gemini eval on the current prompts (50 rows if the free-tier quota allows, else 20). Deploy base Llama and start the v0 eval on the same rows. | Pick photos. Checkout's fallback path (mandate, cart check, confirm, in our code). |
| **7:15–8:30** | SFT smoke run (5 steps), then v1-sft. Journal both. Try a lower Gemini thinking budget for latency. | Stripe Issuing on top of the fallback. Supabase dashboard: "Confirm email" off, "Allow manual linking" on, `feedback` and `mandates` tables exist. |
| **8:30–9:30** | Deploy v1-sft (`--min-replicas 0`), set `OUR_LLAMA_*`, run the eval. Build the A/B pairs from v0 and v1. Read 20 answers. | The whole demo path with mocks off on a real phone (`npx expo start --tunnel` if venue Wi-Fi blocks the laptop). Fix what breaks. |
| **9:30** | **Decision:** v1-sft passes the bars → `/outfits` uses it, Gemini stays the fallback; GRPO (50 steps) if there's time to finish by 11. Fails → Gemini live, report honest numbers. | |
| **9:30–11:00** | GRPO or reward fixes. Fill the eval table. Journal. Collect A/B ratings from friends. Start the Devpost model story. | Landing page, demo video recording, screenshots. Polish against Paper. |
| **11:00** | **Feature freeze.** | |
| **11:00–11:30** | Devpost: track, challenges, five-step story, eval table. README training section. Repo public, no secrets (`git log -p`). **Submit by 11:30.** | Devpost: app, trust and checkout sections. Publish the landing page with the video and QR code. |
| **12:00** | Hacking ends. | |
| **12:20** | `veri deployments wake <id>` before judging. | Phone charged, demo account loaded. |
| **12:30** | Judging. Afterwards: stop every Veri deployment (`veri deployments list`). | |

---

## 11. Demo script

**60–90 second pitch (judging round 1)**

1. *Problem (10 s):* "Stores sell items, people wear outfits, and you can't see it on you until it arrives."
2. *Profile (10 s):* share photos, show the style summary and closet.
3. *Outfits (15 s):* tap a jacket, set $200, outfits appear with reasons.
4. *Try-on (10 s):* the outfit on your photo.
5. *Checkout (10 s):* "make it nicer", the mandate refuses, approve the version that fits. "Stripe enforces the limit on the card. In production the agent orders through each store's ACP checkout; here the order is simulated and no money moves."
6. *The model (25 s):* the eval table and the A/B win rate. "This is a 3B Llama we post-trained on Veri. Base Llama breaks the rules X% of the time; ours, Y%. It answers in Z seconds; Gemini takes 25."

**Likely judge questions, with answers ready**

- *Why train a model instead of prompting a big one?* The eval numbers, latency, owning the model, and a path to running on the phone.
- *Isn't Gemini doing the real work?* Gemini reads photos, tags the catalog and makes try-on images. The outfits come from our model when it passes the bars, and a fallback is always labeled.
- *Is the reward gameable?* The gates (schema, no invented items) zero the score, and the journal shows what we found and fixed.
- *What's real and what's simulated?* The catalog and prices are real; payment runs on a real Stripe Issuing virtual card in the sandbox, so the card's limit is enforced by Stripe but no real money moves; no order reaches the store; try-on is a hosted image model.
- *Privacy?* You choose what to share, the picker needs no library access, photos aren't stored, face matching keeps nothing, and Delete my data removes everything.

---

## 12. Risks and fallbacks

| Risk | Fallback |
| --- | --- |
| No GPU free (`CAPACITY_UNAVAILABLE`, `QUOTA_EXCEEDED`) | Follow the alternatives the error lists. Change shape or provider instead of retrying the same one. |
| v1-sft misses the bars at 9:30 | Gemini stays live; report the honest numbers and what we learned. |
| Prompts longer than `max_seq_length` | The 5-step smoke run catches it; raise the limit or train on 25/50-candidate rows only (already the plan). |
| Veri deployment cold start during judging | `veri deployments wake <id>` 10 minutes before. The backend falls back to base Llama, then Gemini, with a visible label. |
| Gemini is slow (median 25 s, up to 60 s) when it's the fallback | A loading state on Build for up to 30 s; try a lower thinking budget; generate the demo outfits ahead of time. |
| Gemini free-tier quota runs out during judging | Save quota for the demo (no Gemini in training data); keep a cached demo answer as the last fallback. |
| Try-on fails on the free tier (image quota 0) | Turn on billing for the key's project, or show the flat-lay. |
| The full backend has never run end to end on Charlie's machine (no venv; `facenet-pytorch` installs separately with `--no-deps`) | Set up the venv from the README early, before the 8:30 end-to-end run. |
| Two phones scan at once and collide (the pose model isn't thread-safe) | Fix 4 in [backend/SCAN_FIXES.md](backend/SCAN_FIXES.md): one lock around model work. |
| The phone can't reach the laptop on venue Wi-Fi | `npx expo start --tunnel`. |
| Secrets in a public repo | Keys only in `backend/.env`. Check `git log -p` before making the repo public. |
| Credits run out | `veri billing balance` before each run; `--min-replicas 0` on every deployment. |

---

## 13. Open questions

| Question | Owner, by when |
| --- | --- |
| Can our Stripe sandbox account use Issuing by API (and is the card's `brand` Visa)? If not, ship the fallback. | Jasmine, before building Issuing (7:15) |
| Formal and semi-formal prompts top out around 5.2 of 7.5: the catalog has few formality-4 shoes and none at 5. Add dress shoes from a store, or accept it? | Charlie, after SFT |
| Should the live guard drop incomplete outfits? Completeness isn't a gate today. Deferred. | Charlie |
| Does a lower Gemini thinking budget fix the 25 s latency without hurting quality? | Charlie, 7:15–8:30 |
| New profiles start with an empty `avoid` list, while training profiles have one. Fine, since the user fills it on Your style? | Charlie |
| Commit `backend/data/rate_pairs.jsonl`, or copy it onto the server? | Charlie, when the pairs are built |
| Live candidate list size: 50 unless the eval says otherwise. | Charlie, 9:30 |

---

## 14. Submission checklist

- [ ] Devpost: what it does, the problem, **Model Learning** as the track, the five-step training story, the eval table, and one paragraph per challenge: Veri, Visa, Paper, Sentry, MLH Gemini, MLH GoDaddy Registry domain.
- [ ] Landing page live on the domain, with the demo video and the QR code.
- [ ] Mark anything built before the event (the Expo template, the Veri skill file) as pre-existing.
- [ ] Public GitHub repo with a README: setup, architecture, how to rebuild the data and rerun training and eval. `training/JOURNAL.md` included.
- [ ] Demo video, 2–3 minutes, showing the eval table, the A/B result and the mandate refusal.
- [ ] Paper file link, model link on Hugging Face.
- [ ] Whole team at the table for judging at 12:30 PM Sunday.
- [ ] After judging: stop every Veri deployment (`veri deployments list`).
