# PLAN: an AI stylist that builds whole outfits and checks out safely

Working name: **As If** (from *Clueless*, whose digital closet inspired this). The final name is still open. When it changes, update the photo-permission text in [app.json](app.json) and the title in `src/app/onboarding/photos.tsx`.

LA Hacks AI Hackathon 2026, team of 2. Hacking ends **Sunday Oct 18, 12:00 PM PDT**. See [LA_HACKS.md](LA_HACKS.md) for rules, judging and schedule.

## Contents

- [PLAN: an AI stylist that builds whole outfits and checks out safely](#plan-an-ai-stylist-that-builds-whole-outfits-and-checks-out-safely)
  - [Contents](#contents)
  - [1. Pitch](#1-pitch)
  - [2. Track and challenge strategy](#2-track-and-challenge-strategy)
    - [Main track: Model Learning](#main-track-model-learning)
    - [Company challenges](#company-challenges)
  - [3. Product](#3-product)
    - [Core loop](#core-loop)
    - [Getting your photos](#getting-your-photos)
    - [Outfit detection](#outfit-detection)
    - [Face matching ("only look at photos of me")](#face-matching-only-look-at-photos-of-me)
    - [Screens](#screens)
    - [Routes](#routes)
  - [4. Architecture and which model does what](#4-architecture-and-which-model-does-what)
    - [Which model does what](#which-model-does-what)
    - [System](#system)
    - [Repo layout](#repo-layout)
  - [5. The model: what we train](#5-the-model-what-we-train)
    - [Task](#task)
    - [Retrieval](#retrieval)
    - [Occasions](#occasions)
    - [Base model](#base-model)
    - [Catalog](#catalog)
    - [Data](#data)
    - [Reward function: our definition of a good outfit](#reward-function-our-definition-of-a-good-outfit)
    - [Training runs](#training-runs)
    - [Small first, then scale up](#small-first-then-scale-up)
  - [6. How we validate the model](#6-how-we-validate-the-model)
    - [The eval table that carries the pitch](#the-eval-table-that-carries-the-pitch)
  - [7. The training journal: how we explain it to judges](#7-the-training-journal-how-we-explain-it-to-judges)
  - [8. Trust, privacy and checkout](#8-trust-privacy-and-checkout)
  - [9. Scope: must-have, stretch, later](#9-scope-must-have-stretch-later)
  - [10. Who does what, and when](#10-who-does-what-and-when)
    - [Staying unblocked](#staying-unblocked)
  - [11. Demo script](#11-demo-script)
  - [12. Risks and fallbacks](#12-risks-and-fallbacks)
  - [13. Open questions to look into](#13-open-questions-to-look-into)
  - [14. Submission checklist](#14-submission-checklist)

---

## 1. Pitch

**One line:** Pick a piece you love, and a small stylist model that we post-trained ourselves builds the rest of the outfit around it from your own style and within your budget, shows it on you, and checks out with a Visa spending limit the agent can't go over.

**The problem.** Online clothes shopping fails in three places:

1. **People think in outfits; stores sell single items.** You find a jacket and then have to work out the shoes, the trousers and what you already own that goes with it.
2. **You can't see it on you until it arrives.** So you guess, and you return it.
3. **Letting an AI buy for you feels unsafe.** A shopping agent that can spend money needs limits you set and can see.

**The user.** Someone who shops online, has a recognizable personal style, and is tired of returns. In the demo it's one of us, with our real photos.

**Why this is a Model Learning project.** The stylist is a 3B open Llama model that we post-trained on Veri. Our reward function encodes what a good outfit is: within budget, only real catalog items, complete, colors and formality that go together, and true to the user's style. We measured the base model and each training stage on held-out data and with blind human ratings, and the app keeps collecting preference data that trains the next version. A small model that follows these rules reliably is cheap, fast, and small enough that it could one day run on the phone, so photos would never need to leave it.

**Gemini versus our Llama.** Our Llama, post-trained and served on Veri, does one job: pick the outfit and explain why. That's the job we train, measure and pitch. Gemini does everything our model can't do or isn't trained for: reading photos into style tags, generating try-on images, writing the training data, and serving as the reference row in the eval. Every outfit on screen comes from our Llama. Section 4 has the full table and the reasons.

---

## 2. Track and challenge strategy

### Main track: Model Learning

The track asks us to "Build systems that learn, adapt, and improve from data. Create innovative models that uncover patterns, make predictions, or solve complex problems." We qualify because the trained model is the core of the product and we can show it improved. Sections 5–7 are the heart of the project, and the app exists to put that model in front of people.

| Model Learning asks for | What we show |
| --- | --- |
| Learns from data | Supervised fine-tuning (SFT: training on example answers) on outfits a strong model wrote, kept only when they pass our reward. Then GRPO, a reinforcement learning method that trains against a scoring function. |
| Improves | A held-out eval of base Llama, then SFT, then GRPO, with a frontier model as a reference, plus a blind human A/B test. |
| Adapts | Every "which outfit is better?" answer becomes a preference pair, and a DPO round (training on preferred versus rejected answers) on those pairs gives model v2. |

The judges' likely question is "Why not just prompt GPT or Gemini?" The answer has to be numbers: how often the base model breaks budget, invents items or leaves out shoes, against how often ours does, plus latency and cost per outfit.

**Fallback.** If by **Saturday 10 PM** the first training run hasn't started, or the eval shows no gain, switch the Devpost entry to Applied Intelligence. The app and pitch stay the same apart from the emphasis. We pick exactly one main track.

### Company challenges

| Challenge | Fit | What it takes from us | Priority |
| --- | --- | --- | --- |
| **veri.studio**, best use of an open model ($800) | Strong. Requirement: "Use our platform to train an open-source model." | Sections 5–7, which we're doing anyway. The training journal doubles as our Veri write-up. | Core |
| **Visa**, Future of Shopping ($2,000) | Strong. It's an AI shopping product end to end. Weights: innovation 25%, UX 25%, technical execution 20%, commerce impact 15%, trust and responsibility 15%. | The spending-limit checkout on a Stripe Issuing virtual card and the trust screen (section 8), plus a commerce-impact claim about fewer returns, with a cited source. | Core |
| **Paper**, Best Designed Hack ($1,500 / $1,000 / $500) | Strong. Fashion is visual, and the judging rewards "personal craft and character" over AI-looking design. | Design the key screens in Paper first, with a real style guide (type, color, spacing), and build to match. Paper's MCP server lets an agent read the canvas while coding. Redeem `LAHACKS26`. | Core |
| **Sentry**, Best Use of Sentry (guaranteed interviews) | Good. Needs Sentry plus at least two products beyond error monitoring, and "show how observability shaped what you built". | Tracing across app, backend, Veri and Gemini; Logs; AI agent monitoring on the model calls. About 1–2 hours if set up in the first hour so data builds up. Mobile Session Replay needs a development build (section 12), so we don't count on it. | Medium |
| **MLH Best Use of Gemini API** (Google swag) | Free. We use Gemini for photo reading, try-on and data generation (section 4). | Mention it on Devpost. | Low effort |
| **MLH Best Domain Name, GoDaddy Registry** (digital gift card) | Good. The product is a mobile app, so the site is a landing page that sends people to it. | Register the domain. One static page with the pitch, the demo video, a QR code that opens the app, and the privacy policy (the same text as the in-app trust screen). About an hour. | Must-have (small) |

**Skipped, and why:**

- **Fetch.ai:** the whole workflow has to run inside ASI:One with no custom app, which throws away our app and design.
- **Browser Use:** live product search on the web is slow and flaky in a demo. A curated catalog of real products is safer.
- **Workday, Intuit, QNX, Espressif, Even Realities, Base44, Creao, Photon, StepFun:** the problem or the required platform doesn't match.
- **Cognition (Devin):** judged on what you build with Devin. Only worth it if we use Devin's free credits for real work anyway.

---

## 3. Product

### Core loop

1. **Open the app.** Anonymous sign-in gives you an account with no sign-up screen. The welcome screen says what we read and what we keep.
2. **Style profile and closet from your photos.** You give the app photos of outfits you wear (see "Getting your photos" below). Gemini tags each one (garments, colors, fit, formality) and the backend turns the tags into a style profile you can read and edit: "Mostly neutrals with one accent color, relaxed fits, minimal and preppy, avoids y2k." Each garment Gemini finds also becomes a **closet item**, a piece you already own. The profile and closet are saved to your account.
3. **Pick an anchor, a budget range and an occasion.** Everything is prefilled, so one tap builds outfits:
   - **Anchor (optional), one of three kinds:** a catalog item you'd buy, a closet item you already own ("find pants for this shirt"), or none ("I need an outfit for…"). The app suggests one: the catalog item that best matches your style tags, with some randomness.
   - **Budget range:** a slider with two handles, a minimum and a maximum. Default $50–$200. The checkout spending limit defaults to the maximum.
   - **Max price per item (optional):** "no single piece over $80". The backend enforces it by never showing the model pricier items.
   - **Occasion:** default `everyday` (full list in section 5).
4. **Outfit cards.** The trained stylist returns 2–3 complete outfits built around the anchor, each with a total price and a one-line reason ("the cream knit picks up the off-white sneaker sole"). An owned anchor shows as "from your closet" and costs nothing. Swap any single piece you'd buy, or open it with **View at retailer**.
5. **Try it on.** See the outfit on your own full-body photo. The flat-lay view is the fallback.
6. **Checkout under a limit.** The agent proposes a cart. You approve it against a spending limit you set, and the backend refuses anything over it. Confirm with Face ID or the passcode, then see a receipt (section 8).

**Available at any time, outside the loop:**

- **Trust:** what data is used, and delete my data.
- **Which is better?:** the blind A/B screen (section 6). It shows pairs prepared ahead of time (base Llama against our model on held-out prompts), not the user's own request, so it's a separate destination that friends at the venue can use without making a profile. Each answer is a preference pair for v2-dpo.

### Getting your photos

The user chooses one of two ways to share photos. Both ship as equal options.

| Option | How | Expo package | Status |
| --- | --- | --- | --- |
| **Pick photos** | The system picker, multi-select up to 20. On iOS the picker runs outside our app, so it needs no photo-library permission. | `expo-image-picker` (in Expo Go) | To build |
| **Scan the camera roll** | Read the 500 newest photos and keep only the ones that show you in an outfit, using outfit detection and face matching (below). | `expo-media-library` (its `legacy` API), plus pose and face models on the server | Built as a prototype in [src/app/onboarding/photos.tsx](src/app/onboarding/photos.tsx) and `backend/services/` |

How the scan works today:

1. The app skips screenshots and iCloud-only photos, then shrinks each photo on the phone to a 512 px wide JPEG thumbnail. Full-size photos never leave the phone. 512 px keeps faces readable, at about 4× the upload size of the earlier 256 px.
2. The first time, the app finds the user's face (face matching, below).
3. The app sends the thumbnails to `POST /scan` in batches of 10, with the user's face embedding if there is one. The server returns which photos show the user in an outfit, and how they're framed.
4. The results screen shows the outfit photos and counts: full-body, waist-up, photos checked, screenshots skipped, and photos it couldn't read.

### Outfit detection

The server runs a pose model (`yolov8n-pose`) on each thumbnail. For every person it finds, the model scores 17 body points (shoulders, hips, knees, ankles and so on), and the server labels the photo's framing:

- **`full`:** a shoulder, a hip, a knee and an ankle are visible.
- **`upper`:** a shoulder and a hip are visible.
- **`none`:** anything else, including face-only close-ups.

A photo counts as an outfit photo when its best person is `full` or `upper` and fills at least 25% of the photo's height, so small people in the background don't count. With no face chosen, photos with more than 3 people are skipped. With a face chosen, only people whose face matches the user count. [backend/SCAN_FIXES.md](backend/SCAN_FIXES.md) has the full rules and test cases. `backend/test_framing.py` prints the framing for local photos.

### Face matching ("only look at photos of me")

This is matching your face against your photos, not identity verification.

No selfie is needed. In someone's own camera roll, the face that shows up most often is usually theirs, so the app finds it and asks.

1. The app sends its 80 newest thumbnails to `POST /faces/find-owner`.
2. The server finds every face (MTCNN) and turns each into a face embedding, a list of 512 numbers that summarizes a face (FaceNet, `InceptionResnetV1` with VGGFace2 weights).
3. It groups similar faces and returns up to 3 groups that appear in at least 2 photos, most frequent first, each with a cropped face to show.
4. The app asks **"Is this you?"** for each face in turn. "Yes" makes that face the user's. "None of these" turns face matching off for this scan.
5. Every `/scan` request then carries the user's embedding. The server keeps only people whose face is close enough to it (similarity of at least 0.6).
6. The embedding lives only in the app's memory for the session. "Not you? Reset my face" clears it. The server stores nothing.

It drops photos of other people and keeps photos of you that someone else took. Only the scan needs it: when you pick photos yourself, you've already chosen photos of you.

**Where it runs.** On the phone is the private version, but it needs native code, so a development build. Today it runs on the server, which means uploading photos that contain other people's faces. Finding the user's face also computes embeddings for **everyone** in the 80 photos, not just the user. Face embeddings count as biometric data under laws like Illinois' BIPA, so they need explicit consent and shouldn't be stored. Gemini isn't an option: face identification is the kind of request it's likely to refuse.

**Plan:** keep it on the server for the demo, keep the embedding only for the session (done), put it behind a consent screen that says what it computes (section 8; Person B; not done yet), and tell judges that on-device matching is the production design. That honesty helps the Visa trust score.

### Screens

Design these in Paper before building. The first six are the demo path.

1. **Welcome and consent:** what we read, what we keep, and the choice of how to share photos.
2. **Share your photos:** pick photos or scan the camera roll. The scan asks "Is this you?" before it filters.
3. **Your style:** the profile as a short, editable summary with the photos grouped into looks, and the closet (pieces you own).
4. **Build:** anchor (catalog item, closet item or none; suggested by default), two-handle budget range slider, optional max price per item, occasion.
5. **Outfits:** 2–3 cards, total price, reasons, owned pieces marked "from your closet", swap a piece.
6. **Try-on:** your photo wearing the outfit, plus a flat-lay view.
7. **Checkout:** the cart, the spending limit, the tokenized card, confirm.
8. **Which is better?:** the blind A/B screen (section 6).
9. **Trust:** what data is used, delete my data, AI use policy, merchant impact.

There is no "How did it fit?" screen: the app can't know when an order arrives, and no real order is placed.

### Routes

Every file in `src/app/` is a screen in Expo Router. Folders in parentheses, like `(tabs)`, group screens under one layout without adding to the URL, which is why Build is `build.tsx` and not `(tabs)/index.tsx`: that would claim `/`, which the redirect already uses. Every route below exists. Screens that aren't built yet show a placeholder with links along the demo path. The demo path (Welcome → Photos → Style → Build → Outfits → Try-on → Checkout) is one straight push through the stack. After onboarding, a tab bar holds the four places a user returns to.

```
src/app/
├── _layout.tsx              root Stack; will start the anonymous Supabase session
├── index.tsx                redirects to onboarding (later: to /build when a profile exists)
├── onboarding/
│   ├── welcome.tsx          1. Welcome and consent
│   └── photos.tsx           2. Share your photos (pick / scan), with the "Is this you?" card inline
├── (tabs)/
│   ├── _layout.tsx          tab bar: Build · Style · Rate · Trust
│   ├── build.tsx            4. Build
│   ├── style.tsx            3. Your style (also the last onboarding step)
│   ├── rate.tsx             8. Which is better?
│   └── trust.tsx            9. Trust
├── pick-item.tsx            modal: choose the anchor from the catalog or your closet, or none
├── outfits.tsx              5. Outfits
├── tryon/[outfitId].tsx     6. Try-on
└── checkout/
    ├── index.tsx            7. Checkout, including the refusal
    └── receipt.tsx          receipt and what's left of the mandate
```

---

## 4. Architecture and which model does what

### Which model does what

Rule of thumb: **our Llama does the job we trained it for; Gemini does what our model can't do or wasn't trained for.**

| Job | Model | Why |
| --- | --- | --- |
| Pick and explain the outfit | **Our Llama, on Veri** | The trained task. It's what the eval measures and what the judges score. |
| Read photos into tags | Gemini | Needs vision. Veri's trainer is text-only, and serving an 11B vision Llama would take scarce GPUs and one of our two deployment slots for a job we aren't training. |
| Try-on image | Gemini image editing | Needs image generation, which Llama can't do. |
| Write training profiles and SFT answers | Gemini | A strong teacher model writes the data our small model learns from. That's standard distillation, and the reward filter keeps only good answers. |
| Reference row in the eval | Gemini | Shows how close our 3B model gets to a frontier model. |
| Fallback when Veri is down | Base Llama, then Gemini | Labeled in the app so we never pass Gemini off as our model. |

Using our Llama for everything would be a weaker story, not a stronger one: an untrained model doing jobs we didn't measure. One wrinkle: Gemini writes the training data, so it shouldn't also judge the outputs. Keep the human A/B test as the judge of style quality.

### System

```
Expo app (Expo Router)                 FastAPI backend                      Models and data
─────────────────────                  ───────────────                      ───────────────
sign-in (anonymous) ─────────────────────────────────────────────────────▶ Supabase Auth
newest photos ─────────────────────────▶ POST /faces/find-owner ─────────▶ face models: most common faces
thumbnails + your face ────────────────▶ POST /scan ─────────────────────▶ pose + face models: photos of you in outfits
photos ────────────────────────────────▶ POST /profile ──────────────────▶ Gemini: tag each photo
                                          builds profile + closet ───────▶ Supabase: profiles
edit profile ──────────────────────────▶ GET, PUT /profile ──────────────▶ Supabase: profiles
browse, anchor ────────────────────────▶ GET /catalog ───────────────────▶ training/catalog.json
anchor, budget range, make it nicer ───▶ POST /outfits ── candidates ────▶ Veri: our Llama 3B
                                          retrieve, call, guard, retry once
photo + items ─────────────────────────▶ POST /tryon ────────────────────▶ Gemini image editing
cart ──────────────────────────────────▶ POST /checkout/mandate, /cart, /confirm ▶ Stripe Issuing (sandbox): card with a spending limit
A/B choice ────────────────────────────▶ GET /rate/next, POST /rate ─────▶ Supabase: feedback (→ DPO data)
trust screen ──────────────────────────▶ DELETE /me ─────────────────────▶ Supabase: delete user's rows
                 Sentry: traces, logs and AI-call monitoring on both sides
```

- **App:** this repo. Expo SDK 57, TypeScript, Expo Router with routes in `src/app/` (see [AGENTS.md](AGENTS.md)). Photos are shrunk on the phone with `expo-image-manipulator` before upload.
- **Backend:** FastAPI in `backend/`. For the demo it runs on a laptop behind a tunnel, or on a small cloud VM if time allows. The pose and face models run inside the server process, on CPU.
- **Supabase** stores accounts, style profiles and feedback:
  - **Anonymous sign-in** gives every user an account with no sign-up screen, so judges and friends can start in one tap. Email sign-in can come later.
  - Tables: `profiles` (one per user, the style profile and closet as JSON), `feedback` (A/B choices, with the outfits shown). The `feedback` table exports straight to the DPO dataset.
  - Photos are never stored. "Delete my data" deletes the user's rows.
  - The phone only talks to Supabase for sign-in. Reads and writes go through the backend, which holds the service key.
- **Secrets:** the Gemini, Veri, Supabase service and Stripe secret keys live only on the backend, in `backend/.env`. The app's settings go in the root `.env`, and everything in it ships inside the app. [README.md](README.md) lists both. The repo goes public for submission, and anything the phone app ships can be read.
- **The guard:** the backend runs the reward's checks on every model answer. A failing answer gets one retry and never reaches the screen.

### Repo layout

Everything lives in this one repo. The Expo app stays at the root, which is what [AGENTS.md](AGENTS.md) and the Expo commands expect. Built so far: the photo scan (`src/app/onboarding/photos.tsx`, `src/api/`, `src/lib/photos.ts`, and the scan and face files in `backend/routes/` and `backend/services/`), a placeholder screen for every route, `src/theme/` (tokens seeded from the current screens; real values come from the Paper style guide), and the first half of `training/`: `stores.json`, `scrape_catalog.py` with its first pull in `catalog_raw.json`, `vocab.py`, `retrieval.py` and `reward.py` with their tests (`python -m training.test_retrieval`, `python -m training.test_reward`). Everything else in the tree is planned. Run the backend from the repo root with `uvicorn backend.main:app --host 0.0.0.0 --port 8000`.

```
LaHacksAI/
├── package.json, app.json, tsconfig.json   the Expo app
├── src/
│   ├── app/          routes only (section 3)
│   ├── components/   Placeholder (until every screen is real), OutfitCard, ItemTile, BudgetSlider, PhotoGrid…
│   ├── api/          client.ts (fetch + EXPO_PUBLIC_API_BASE_URL), types.ts, mocks.ts
│   ├── lib/          photos.ts (shrinks photos for the scan), supabase.ts, sentry.ts
│   └── theme/        colors, type, spacing and radii; values from the Paper style guide once it's done
├── assets/
├── backend/          FastAPI
│   ├── main.py       creates the app, includes the routers
│   ├── routes/       profile.py, outfits.py, catalog.py, tryon.py, checkout.py, feedback.py, me.py, scan.py, faces.py
│   ├── services/     gemini.py, veri.py, supabase.py, stripe_issuing.py, pose.py, faces.py, images.py
│   ├── schemas.py    Pydantic request and response models
│   ├── test_framing.py   prints the framing for local photos (python -m backend.test_framing <photos>)
│   └── requirements.txt
├── training/
│   ├── stores.json   the 25 stores the catalog is pulled from
│   ├── scrape_catalog.py   stores → catalog_raw.json (untagged)
│   ├── tag_catalog.py      catalog_raw.json → catalog.json, tagged by Gemini (section 5)
│   ├── catalog.json  the catalog; the server reads it too
│   ├── vocab.py      the fixed slots, colors, style tags and occasion formality ranges
│   ├── retrieval.py, test_retrieval.py   picks each prompt's candidates; the server imports it for /outfits
│   ├── reward.py, test_reward.py   the server imports reward.py as the guard
│   ├── gen_profiles.py, build_prompts.py, gen_sft.py, eval.py
│   ├── configs/      one Veri config per run
│   ├── data/         JSONL files (gitignore the large ones)
│   └── JOURNAL.md
├── landing/          static page for the GoDaddy Registry domain
└── README.md, PLAN.md, LA_HACKS.md
```

Rules that matter more than the exact folders:

- **One copy of `catalog.json`, `retrieval.py` and `reward.py`.** The same reward trains the model and guards live answers, so a second copy that drifts means the guard rejects answers the model was trained to give. Likewise, the same retrieval builds training prompts and live prompts, or the model meets inputs in the app it never saw in training. Run the server from the repo root (`uvicorn backend.main:app`) so it can `import training.reward` and `training.retrieval`. Veri runs `reward.py` as a single file, so it carries its own copy of the vocabularies from `vocab.py`; `test_reward.py` fails if the two copies drift.
- **API shapes in two places:** `backend/schemas.py` and `src/api/types.ts`. Freeze both in the first hour. `src/api/mocks.ts` returns fake data in those shapes, so the app can be built before the server is ready.
- **One file per endpoint in `backend/routes/`**, so both of us can work on the server without merge conflicts (section 10).

---

## 5. The model: what we train

### Task

Input: the style profile, budget range, occasion, the anchor (if any), and a list of candidate items that `training/retrieval.py` picked from the catalog for this request (see Retrieval below). Output: strict JSON.

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

`items` lists every piece, the anchor included. A closet anchor appears by its `closet_<n>` id and adds nothing to `total`, which is the sum of the catalog items only.

The backend retrieves; the model chooses and explains. That keeps prompts short enough for a 3B model and makes every rule checkable.

**Three kinds of prompt, one pipeline.** Each prompt has a catalog anchor, a closet anchor, or no anchor. The prompt template, retrieval and reward are the same code for all three; only the anchor line and a couple of checks change. Training data mixes them, about 45% catalog anchor, 35% closet anchor and 20% no anchor, so the model learns all three.

**Two numbers to keep apart.**

- **The catalog** is every product we have, about 1,000 (below). It sets how much variety exists across all users.
- **The candidate list** is the slice of the catalog that one prompt shows the model, picked for that user and that request. It sets how many choices the model weighs at once.

A bigger catalog gives retrieval more to choose from, so every user's candidates fit them better, at no cost to the prompt. A longer candidate list gives the model more options but a longer prompt, which costs accuracy for a small model, training time, and some latency.

**Candidate list size: train on several, measure the rest.** Each item takes about 30 tokens in the prompt, so 25 items is about 1,000 tokens and 200 is about 6,500. Llama 3.2 3B accepts 128,000, so all of them fit; the questions are accuracy and training cost.

- **Train** on a mix of 25, 50, 75 and 100 candidates, so the model handles any size in that range.
- **Evaluate** at 25, 50, 75, 100, 150 and 200. 150 and 200 are deliberately sizes the model never trained on: the eval shows where accuracy starts to fall.
- **Live default:** 50 until the eval says otherwise. Pick the largest size where invented items and broken rules stay near the 25-item rate.
- Training on 150–200 too would make GRPO runs 2–3× slower (cost grows with prompt length × rollouts). Add them only if the eval shows the model holds up there.

### Retrieval

`training/retrieval.py`, used by both `build_prompts.py` and `/outfits`. Deterministic, so the same request always gets the same candidates.

1. **Filter out** items that can't work: the anchor's slot (accessories excepted; a dress anchor also drops tops and bottoms, and a top or bottom anchor drops dresses), items priced above `budget_max` minus the anchor's price (a closet anchor costs $0), items above `max_item_price`, departments the profile doesn't shop (unisex always passes), dresses for a men-only profile, anything with a style tag or color on the profile's `avoid` list, and items more than one formality level outside the occasion's range.
2. **Score** the rest by the number of style tags shared with the profile, plus 0.5 if any of the item's colors is one the user wears, plus 0.5 if its fit is one of the profile's `fits`. Ties break by id.
3. **Keep the top N, split across slots** by fixed weights (tops 25%, bottoms 25%, shoes 20%, outerwear 12%, dresses 10%, accessories 8%), renormalized over the slots that still have items, with a diversity cap: at most two items in a slot that share both a color and a style tag. If a slot runs short, the remaining places go to the best items left in any slot.
4. **Leave some imperfect options in.** About 15% of each slot's places go to items spread across the lower-scoring half. If the candidates all go together, the model does no real choosing and the "we trained it" claim weakens. The eval keeps this honest: base Llama gets the same candidates and still breaks rules.

The result is sorted by slot, then id, so an item's position in the prompt doesn't reveal its score.

Swaps on the outfit cards come from the whole catalog, computed by the backend after the model answers, so the user sees more variety than the candidate list.

### Occasions

Each occasion has a target formality range that the reward checks against (`OCCASION_FORMALITY` in `training/vocab.py`). Fixed list; free text can't be scored.

| Occasion | Formality |
| --- | --- |
| `formal` | 4–5 |
| `semi-formal` | 4–5 |
| `work` | 3–4 |
| `everyday` | 2–4 |
| `party` | 2–4 |
| `casual` | 1–3 |
| `athletic` | 1–2 |
| `comfy` | 1 |

`formal` shares `semi-formal`'s range because every outfit needs shoes and no shoe is tagged 5 (heels and dress shoes are 4).

### Base model

`unsloth/Llama-3.2-3B-Instruct`, an **ungated community mirror** on Hugging Face. Veri's guide warns that gated `meta-llama/*` repos fail after the GPU has booted and started billing. 3B trains on one L4 GPU and serves on one L4. The two smoke runs on Oct 18 confirmed that Veri trains the mirror and pushes its merged weights (`training/JOURNAL.md`), so the `Qwen/Qwen3-4B` fallback isn't needed.

### Catalog

About 1,000 **real products** (real brand, price, image and retailer link) from 25 online stores, across tops, bottoms, dresses, outerwear, shoes and accessories, menswear and womenswear, in `catalog.json`. Real products make the demo believable and give the reward something concrete to check. A large catalog also matters for training: the 400 training prompts rarely share the same candidates, so the model can't memorize a few safe outfits.

Built by scripts, not by hand:

1. **Pick stores** (`training/stores.json`, Charlie decides). Prefer stores on Shopify: many publish their whole product list at `<store>/products.json` (up to 250 products per page) with title, product type, price, images and URL. Big chains like Zara, H&M, Uniqlo and Nike have no such feed and block scraping, so skip them. Cover a real spread of styles, prices and both departments. Check each store's terms of service. The list is 22 stores that price in US dollars, from streetwear (Stüssy, Kith) to menswear basics (Taylor Stitch, Todd Snyder), activewear (Alo Yoga, Set Active), womenswear (Christy Dawn, Edikted, Princess Polly), shoes (Allbirds, Thursday Boot Co., Koio) and jewelry (Gorjana).
2. **`scrape_catalog.py`** (done) pulls each store's feed, maps its product types to our six slots, keeps one price and image per product, sets `url` to the product's own page (`<store>/products/<handle>`, never the store's home page), drops color variants of the same item, and caps each store at 50 products spread across slots. One-slot stores get a lower cap in `stores.json` (`max_items`, 20–40) so they don't swamp a slot. Requests go strictly one at a time, at least 3.5 s apart: a parallel run once got our IP blocked across all of Shopify. The first pull (Oct 18) gave 930 untagged items in `catalog_raw.json` from 21 stores (Bonobos returned none): 191 tops, 172 bottoms, 108 dresses, 135 outerwear, 146 shoes and 178 accessories, priced $4–$998.
3. **`tag_catalog.py`** (next) has Gemini (the fast model) tag each item's `department`, `colors`, `formality`, `style_tags`, `season`, `pattern` and `fit` from its title and image, choosing only from the fixed vocabularies in `training/vocab.py` so "navy" and "dark blue" don't become two colors. The scraper's `department_hint` (from the product's type and tags, else the store's `department`) is a hint, not the answer.
4. **Check:** slot and department balance, every image and product URL loads, and a person spot-checks about 30 random items. Record the date the catalog was pulled; prices and stock drift.

```json
{
  "id": "top_012",
  "name": "Relaxed cotton crewneck",
  "brand": "…",
  "slot": "top",
  "department": "unisex",
  "price": 38.0,
  "colors": ["cream"],
  "formality": 2,
  "style_tags": ["minimal"],
  "season": ["fall", "winter", "spring"],
  "pattern": "solid",
  "fit": "relaxed",
  "image": "https://…",
  "url": "https://…"
}
```

Formality runs from 1 (athleisure) to 5 (formal). Slots are `top`, `bottom`, `dress`, `outerwear`, `shoes`, `accessory`. Departments are `men`, `women`, `unisex`. The vocabularies, in `training/vocab.py`:

- **Colors,** in three groups. Neutrals: white, cream, beige, tan, khaki, brown, gray, charcoal, black. Versatiles: navy, denim, olive, blue, forest-green, muted-green, burgundy, light-blue, lilac, gold, silver. Accents: yellow, orange, red, pink, purple.
- **Style tags,** 1 to 3 per item: minimal, old-money, western, preppy, streetwear, techwear, workwear, outdoors, athleisure, bohemian, y2k, goth, coastal, sporty, clean-girl, soft-girl, grunge.
- **Patterns:** solid, stripe, check, small-print, large-print, graphic. Check, large-print and graphic are loud.
- **Fits:** slim, regular, relaxed, oversized, for tops, bottoms, dresses and outerwear. Shoes and accessories have none.

Changing a list means re-tagging the catalog and regenerating the training data.

### Data

1. Have Gemini write about 400 synthetic style profiles across a spread of styles, departments, budget ranges (minimums $0–$150, maximums $60–$400) and occasions, from a fixed seed list so they vary. Each profile also gets a synthetic closet of 5 garments per slot it wears, about 25 in all (30 when the profile wears dresses), so closet-anchor prompts have something to anchor on, each profile can yield several closet-anchor prompts, and the closet-as-candidates stretch goal won't need the data regenerated. Some prompts get a `max_item_price`.
2. For each profile, pick an anchor kind (catalog, closet or none, in the mix above), a candidate list size (25, 50, 75 or 100), and run `retrieval.py`. That gives the **prompts**.
3. Split by profile: about 300 for training, about 100 held out for evaluation. A profile never appears in both.
4. For SFT, have Gemini answer the training prompts, score every answer with the reward, and keep only high scorers.

Veri needs one prompt format per JSONL file. Mixing plain-string prompts with message-list prompts crashes the trainer after the GPU boots. Run `veri datasets check` on every file before upload.

### Reward function: our definition of a good outfit

`training/reward.py`. Deterministic, fast, no network and standard library only, because Veri runs it inside the trainer as a single file. Nothing from the catalog is embedded: each row's occasion, budget range, anchor, candidates (with their slot, price, colors, formality, style tags, pattern, fit and season), and the profile's style tags, fits and `avoid` list go in as extra dataset columns and arrive in `**kwargs`.

Charlie owns the rules in this table (which checks are gates, the weights, the color table, the formality tolerance); the agent drafts the code and tests from it.

| Check | Score |
| --- | --- |
| Output is exactly the JSON schema: one `outfits` key holding 1–3 outfits, each with exactly `items`, `total` and `reason` | Gate: 0 overall if it fails |
| Every item ID is in that prompt's candidate set or is the anchor (no invented items) | Gate: 0 for that outfit |
| Includes the anchor (full score when there is none) | +1 |
| Complete outfit: top + bottom, or a dress with neither, plus shoes; at most one per slot except accessories; no repeated IDs | +1 |
| Total of catalog items is within `budget_min`–`budget_max`, and the stated total equals the real sum to the cent. Closet items count as $0 | +1 |
| Color harmony: the lowest score of any two different colors in the outfit, by group (neutral with neutral or versatile 1, neutral with accent 0.9, versatile with versatile 0.9, versatile with accent 0.75, accent with accent 0.6); one color or none scores 1 | 0.6 to +1 |
| Pattern: at most one loud pattern (check, large-print, graphic) | +0.5 |
| Season: the items share at least one season (items without seasons are skipped) | +0.5 |
| Formality coherent: all items within 1 level of each other and inside the occasion's range | +1 |
| Matches the profile: the mean over non-anchor items of each item's checks (shares a style tag with the profile; has one of the profile's fits, when both have one); 0 if any item has a tag or color from the profile's `avoid` list | 0 to +1 |
| Reason is one sentence of at most 40 words and names at least one item, by ID or by a word from its name | +0.5 |

One outfit scores at most 7.5. A completion's reward is the sum of its outfits' scores divided by 3, so a missing outfit, a failed gate or a repeated outfit each count as 0.

The per-item price cap, departments and the `avoid` list need no reward check: retrieval never shows the model items that break them, so it can't pick one without failing the "no invented items" gate.

The same code runs in the backend as a guard on every live answer (section 4), so the definition of "good" that trained the model also protects the demo. The backend scores each outfit separately, drops any that fail a gate, recomputes every total from catalog prices instead of trusting the model's number, and retries once if fewer than two outfits survive. If the retry also fails, it falls back to base Llama, then Gemini, and sets `generated_by` so the app shows a label. If every generator fails, `/outfits` returns a 503, never an empty list. An anchor ID that isn't in the catalog or the user's closet is a 422.

**How we know the reward works:** unit tests on hand-written outfits (`training/test_reward.py`, section 6), then score base Llama's answers and check the scores spread out (if nearly every answer gets the same score, GRPO has nothing to learn from), then watch the mean reward climb during GRPO with `veri jobs logs <id> -f`, then read the top-scoring answers after each run. One score takes about a millisecond.

### Training runs

1. **v0, the baseline.** Base Llama with our prompt, no training. Evaluated, not trained.
2. **v1-sft.** `sft_text` with LoRA on the filtered Gemini answers. One L4. Short.
3. **v1-grpo.** GRPO from the SFT checkpoint with the reward. One L4, `max_steps` about 100, 4–8 rollouts per prompt.
4. **v2-dpo** (stretch). DPO on preference pairs from the in-app A/B screen, collected from real people at the event.

### Small first, then scale up

Every stage gets a tiny version first, because the expensive failures (a bad dataset format, a wrong config, a reward that scores everything the same) show up just as well at small size, and on Veri they show up after the GPU has booted and started billing.

| Stage | Small version | Proves | Then |
| --- | --- | --- | --- |
| Catalog | Scrape and tag 2 stores (~100 items) | The feed works, slot mapping is right, Gemini tags look sensible | All 25 stores |
| Reward | The hand-written test outfits (21 tests, passing) | It ranks outfits the way we would | Score real model answers |
| Data | 20 profiles, 40 prompts | Prompts read well; `veri datasets check` passes; Gemini's SFT answers pass the reward often enough | 400 profiles |
| Candidate list size | Base Llama on 20 prompts at each size, no training | Whether accuracy already drops at 100–200 before we pay to train on them | The full eval |
| SFT and GRPO | `max_steps` 5–10 on 40 prompts | The config is accepted, the reward runs inside the trainer, logs show a reward, merged weights push to Hugging Face. SFT's model load and weight push are proven by the Oct 18 smoke runs (`training/JOURNAL.md`); the reward inside GRPO isn't yet | Full runs |
| Eval | 10 held-out prompts | The script runs end to end and fills the table | All 100 |

For every run, price it first with `veri jobs estimate`, but don't treat that as a check: it gives a price even for a model that doesn't exist, so only a real run proves a config. LoRA runs must push **merged** weights to a **public** Hugging Face repo, in a `[huggingface]` table with `artifact = "merged"` and `private = false`, because Veri can't serve a bare LoRA adapter. The table is `[huggingface]`, not `[hf_push]`: the CLI silently ignores tables it doesn't know, which is why smoke run 1 pushed nothing. Serve the winner on one L4 with `--min-replicas 0`.

---

## 6. How we validate the model

We don't trust a number until we've checked it ourselves. Five layers, cheapest first:

1. **Reward unit tests, before any GPU time** (`training/test_reward.py`). Hand-written outfits: clearly good, clearly bad, and edge cases (exactly at the budget minimum and maximum, a dress with no bottom, an invented ID, a closet anchor that must not count toward the total, no anchor at all). The reward must rank them the way we would. A reward that scores everything the same teaches GRPO nothing.
2. **Data checks.** `veri datasets check` on every file; a script confirms no eval profile appears in training data; read 10 random rows by hand.
3. **Automatic eval on the 100 held-out prompts.** Same prompts, same sampling settings, every model. This is the table below.
4. **Read the outputs.** After each run, both of us read 20 random answers and the 10 highest-reward answers. The top answers are where reward hacking shows up, such as always picking the cheapest items or reusing one safe outfit. If we find a hack, fix the reward, log it, and rerun.
5. **Blind human A/B test.** The app's "Which outfit is better?" screen shows two outfits for the same request, one from base Llama and one from our model, in random order with no labels. We rate, and so do friends at the venue. Report the win rate. The same answers are the preference pairs for v2-dpo.

### The eval table that carries the pitch

Fill it in from real runs only.

| Metric | v0 base Llama | v1-sft | v1-grpo | Gemini (reference) |
| --- | --- | --- | --- | --- |
| Valid JSON | | | | |
| No invented items | | | | |
| Complete outfit | | | | |
| Within budget | | | | |
| Mean reward | | | | |
| Human A/B win rate against v0 | n/a | | | |
| Median latency per outfit | | | | |
| Cost per 1,000 outfits | | | | |

A second table, for the winning model only, shows accuracy by candidate list size (section 5). 150 and 200 were never trained on.

| Candidates | 25 | 50 | 75 | 100 | 150 | 200 |
| --- | --- | --- | --- | --- | --- | --- |
| No invented items | | | | | | |
| Mean reward | | | | | | |
| Median latency | | | | | | |

If GRPO doesn't beat SFT, report that and ship SFT. An honest negative result with a clear explanation still scores on technical depth, and judges trust the other numbers more.

---

## 7. The training journal: how we explain it to judges

Judges will ask how we customized the model. The answer should come from a record we kept, not memory at 3 AM.

**`training/JOURNAL.md`** gets an entry for every decision and every run, written when it happens:

```markdown
### 2026-10-17 21:40, v1-grpo run 2
- Changed: color-harmony weight 0.5 → 1.0; added the 60–100% budget bonus
- Why: run 1's top answers all spent ~30% of budget (cheapest-item hack)
- Data: prompts v2 (300 train / 100 eval), reward.py @ <git commit>
- Veri job: <job id>, L4 x1, 41 min, $0.72
- Result: mean reward 2.9 → 4.1; within-budget 97%; read 20 samples, cheap-item hack gone
```

Rules that keep it useful:

- Every run records its Veri job ID, the git commit of `reward.py` and the data, the cost, and the result. That lets anyone rerun it.
- Failed runs and dead ends get logged too. "We found the model gaming the reward and fixed it" is one of the strongest things we can tell a Model Learning judge.
- `training/` holds the data generation script, `reward.py` with its tests, the eval script, the Veri configs and the journal, so the whole pipeline is in the public repo.

**Turning it into the pitch.** On Sunday morning, condense the journal into a five-step story for Devpost, the README and one slide:

1. We defined the task and an output schema.
2. We wrote down what a good outfit is, as a reward function, and tested it.
3. We generated and filtered training data.
4. We trained in stages (SFT, then GRPO) and fixed what the outputs showed us.
5. We measured it two ways (automatic eval, blind human test) and kept learning from users (DPO).

---

## 8. Trust, privacy and checkout

Trust is 15% of Visa's score and the main worry people have about agents that spend money, so it gets real screens, not a footnote.

**Photos**

- You choose what to share: specific photos, or a scan of your 500 newest photos. Only small thumbnails leave the phone.
- **Face matching, during the scan.** Finding your face computes face embeddings for everyone in your 80 newest photos, not just you. None of them are stored. Your own face's embedding stays in the app's memory for the session, and "Not you? Reset my face" clears it. The consent screen says all of this plainly before the scan runs.
- Photos are processed for the session and not stored. Only the text tags and the profile are kept, and you can read and edit both.
- One tap deletes everything: profile, feedback and anything from the session.

**Checkout: a spending mandate the agent can't exceed**

A **mandate** is a set of rules you give the agent before it can buy: how much it may spend, on what, and for how long. The idea follows Visa's agentic commerce work, where an agent gets a limited payment token instead of your card.

**Payments run on Stripe Issuing, in Stripe's sandbox.** Visa has no open sandbox for agent payment tokens; it expects builders to use a payment platform. Stripe Issuing lets our backend *create* a virtual card (the opposite of the usual Stripe flow, where you charge a customer's card) and set spending controls on the card itself: a maximum amount and the merchant categories it may be used at. Each mandate gets its own card, so the agent holds a card that can't overspend, never the user's card. Everything runs with test keys, so no real money moves, and we say so on screen and on Devpost.

1. You set the mandate: at most $200, apparel only, expires in 24 hours. The limit defaults to the budget maximum you chose on the Build screen. `POST /checkout/mandate` creates a Stripe Issuing virtual card with `spending_controls`: `spending_limits` of the limit with interval `all_time`, and `allowed_categories` set to clothing stores.
2. The agent only ever holds a **card reference** (`Visa •••• <last 4 of the Issuing card>, agent card`). It never sees the card number.
3. `POST /checkout/cart` checks every cart against the mandate in our code first, so the refusal comes back fast with a clear reason.
4. You confirm the final cart with a biometric prompt (`expo-local-authentication`; Face ID needs a development build, and Expo Go falls back to the device passcode).
5. `POST /checkout/confirm` makes a simulated purchase on the card for the cart total (Stripe's test helper for Issuing authorizations). Stripe approves it or declines it against the card's own limit, so the limit holds even if our check had a bug.
6. The receipt shows what was bought, what it cost, what's left of the mandate and the Stripe authorization ID. It says "Demo: no order was placed and no money moved," and each item has a **View at retailer** link to its real product page (the catalog's `url`).
7. Stripe's spending intervals don't go below a day, so the 24-hour expiry is ours: the backend cancels the card after a purchase or when the mandate expires.

The app needs no Stripe SDK: the user never enters a card, and every Stripe call happens on the backend. The Stripe secret key lives in `backend/.env` with the other keys.

**What's simulated, and the production design.** No order reaches a store. Stripe only handles the payment: it creates the card, enforces its limit and approves or declines. Placing the order (cart, size, shipping, the store's checkout) is a separate problem Stripe doesn't solve, and test-mode Issuing cards can't be charged by real stores anyway. In production the agent would order through each store's **Agentic Commerce Protocol (ACP)** checkout, the open standard from Stripe and OpenAI, and pay with a Stripe **Shared Payment Token**, which is limited to one store, a maximum amount and an expiry. The mandate maps onto those limits almost one-to-one, so the trust model stays the same and only the payment mechanism changes. ACP only works with stores that have joined, so it can't be built this weekend. Browser automation of each store's checkout was ruled out as too fragile for a live demo.

**Fallback.** If Issuing isn't available on our Stripe account, the mandate stays enforced in our code only, the card reference is a fixed test card (`Visa •••• 4242`), and the payment is labeled as simulated.

**Demo moment:** you say "make it nicer", the agent proposes a $90 upgrade that would push the cart past your $200 limit, and the backend refuses the cart and says why. "Make it nicer" is `POST /outfits` with `upgrade_of` set to the current outfit's item ids: the backend runs the normal pipeline with the budget range moved up to (that outfit's total, total + $150] and returns one outfit. That's the one request allowed past `budget_max`, because the mandate is what's supposed to refuse it. The app then offers the closest outfit that fits. Judges see the limit enforced twice, in our code and on the card, not just promised in a policy.

**Merchant impact panel:** outfit-level selling raises basket size, and trying an outfit on before buying should cut returns. Cite a real source for return rates on the panel and on Devpost. Don't invent numbers.

---

## 9. Scope: must-have, stretch, later

Two people, about 22 hours. The model work comes first: an app with no trained model behind it loses the track.

**Must-have**

- The training pipeline: catalog, data, reward with tests, SFT, GRPO, deployed model
- The eval table with real numbers, and the training journal
- A catalog of about 1,000 real products, built by script from 25 stores
- Share photos in either of two ways (pick photos, or scan the camera roll with face matching), then a style profile and closet saved in Supabase
- Optional anchor (catalog item, closet item or none), budget range and occasion, all prefilled, then 2–3 outfit cards from **our** model
- Max price per item in the API and retrieval (a one-line filter); its Build-screen control is Person B's call
- The blind A/B screen, writing to Supabase
- Try-on on one photo, with the flat-lay as a fallback
- Mandate checkout with a refusal, and the trust screen with delete my data
- Paper designs for the demo-path screens, and the app built to match them
- Landing page on a GoDaddy Registry domain: pitch, demo video, QR code to the app, privacy policy

**Stretch, in this order**

1. v2-dpo from A/B answers gathered at the event
2. **Closet items as candidates, not just the anchor:** "you already own shoes that work". Retrieval adds the user's closet items to the candidate list at $0, the reward counts them as free, and `Outfit.owned` already carries them to the app
3. Sentry tracing, logs and AI monitoring, with a written "what it showed us"
4. Screenshots as inspiration: the scan currently skips screenshots. Instead, include them, tag them "inspiration" (outfits the user likes) as opposed to "worn" (camera photos of the user), and weigh the two differently in the style profile

**Later (after the hackathon, unless we're far ahead)**

- Makeup recommendations from skin type and tone
- Sharing outfits with friends
- Social media integration
- Live web product search instead of a fixed catalog

---

## 10. Who does what, and when

**Person A (Charlie): model and backend.** Catalog (scraper and tagging), data, retrieval, reward, Veri runs, eval, journal, `/profile` (including the closet), `/outfits` (including make it nicer), `/catalog`, `/rate`, Supabase.
**Person B (Jasmine): design and app.** Paper style guide and screens, Expo Router setup, every screen including the A/B screen, `/tryon`, `/checkout`, `DELETE /me`, `/scan`, `/faces/find-owner` (including fix 4 in [backend/SCAN_FIXES.md](backend/SCAN_FIXES.md)), the face-matching consent screen, the Stripe Issuing setup behind `/checkout`, Sentry, domain and landing page, demo video.

The split works because training runs take 30–60 minutes of waiting. Person A writes server endpoints while a run trains.

### Staying unblocked

1. **Contract first (Sat 2–4 PM, together).** Agree on the outfit JSON schema, the request and response of every endpoint, and the `catalog.json` fields. Write them into `backend/schemas.py` and `src/api/types.ts`, and have B write `src/api/mocks.ts` from them. After that, neither of us waits on the other.
2. **Split the server by file.** A owns `profile.py`, `outfits.py`, `catalog.py`, `feedback.py` (`/rate`) and the `services/` files for Gemini, Veri and Supabase. B owns `tryon.py`, `checkout.py`, `me.py`, `scan.py`, `faces.py`, and the pose and face `services/`. `main.py` and `schemas.py` are shared: keep edits there small and pull before touching them.
3. **Integration checkpoints**, where the app swaps a mock for the real endpoint:
   - **Sat 10 PM:** `/profile` live, and `/outfits` against v0.
   - **Sun 6 AM:** `/outfits` against our trained model.
4. **Git:** short-lived branches, or push to `main` inside your own folders, and pull often.
5. **Watch A's load.** A is on the critical path, since no trained model means no Model Learning track. If A falls behind, B takes the Supabase setup or `/rate`, all plain create, read, update and delete code.

Times are PDT. Shift them if we start late, but keep the 10 PM track decision and the 8:30 AM feature freeze.

| When | Person A | Person B |
| --- | --- | --- |
| **Sat 2–4 PM** | Get Veri credits from @daniung on Discord and redeem them **before** any run. `veri whoami`. Check the Llama mirror with `veri jobs estimate`. Pick the stores, scrape and tag 2 of them, then all of them into `catalog.json`. Freeze the output schema and, with B, the API shapes (see [JANGES_FOR_JASMINE.md](JANGES_FOR_JASMINE.md)). Start `training/JOURNAL.md`. | Register the domain. Paper style guide: type, color, spacing, one hero screen. Move the app to Expo Router. Agree on the API shapes with A and write the mocks. |
| **Sat 4–7 PM** | Write `retrieval.py`. Generate profiles and prompts (20 first, then 400). Write `reward.py` and its tests. Run the candidate-size check on base Llama, then the v0 eval. Set up Supabase (anonymous sign-in, two tables). | Paper: the demo-path screens. Build photos → profile → build screens against mocked responses. Add Sentry. |
| **Sat 7–10 PM** | A 5–10 step smoke run, then v1-sft (by 8 PM), then v1-grpo from it. `/profile` with Gemini. `/outfits` against v0. **10 PM: confirm the track.** | Outfit cards, swap a piece, the A/B screen, checkout, trust screen. Mandate endpoints. |
| **Overnight** | Watch runs (`veri jobs logs <id> -f`). Eval and read samples from each checkpoint. Journal every run. Push merged weights, deploy the winner. | Try-on endpoint and screen, flat-lay fallback. Polish against Paper. Load the A/B screen with v0 and v1 answers on held-out prompts. |
| **Sun 6–8:30 AM** | Point `/outfits` at our model. Final eval table and chart. Stretch: v2-dpo from the A/B data. | End-to-end on a real phone over venue Wi-Fi (`npx expo start --tunnel` if needed). Collect A/B ratings from friends. **8:30 AM: feature freeze.** |
| **Sun 8:30–10:30 AM** | Condense the journal into the five-step story. Devpost write-up: track, each challenge, the eval table. README. | Record the 2–3 minute demo video. Screenshots. Publish the landing page with the video and QR code. |
| **Sun 10:30 AM–12 PM** | Buffer. Repo public, no secrets in it. Submit by 11:30. | Buffer. Rehearse the 60–90 second pitch. |
| **Sun 12:20 PM** | Wake the Veri deployment before judging. | Phone charged, demo account loaded. |

---

## 11. Demo script

**60–90 second pitch (judging round 1)**

1. *Problem (10 s):* "Stores sell items, people wear outfits, and you can't see it on you until it arrives."
2. *Profile (10 s):* share photos, show the style summary.
3. *Outfits (15 s):* tap a jacket, set $200, three outfits appear with reasons.
4. *Try-on (10 s):* the outfit on your photo.
5. *Checkout (10 s):* "make it nicer", the mandate refuses, approve the version that fits. One line on the boundary: "Stripe enforces the limit on the card. In production the agent orders through each store's ACP checkout; here the order is simulated and no money moves."
6. *The model (25 s):* the eval chart and the A/B win rate. "This is a 3B Llama we post-trained on Veri. Base Llama breaks budget or invents items X% of the time; ours, Y%. People preferred ours Z% of the time. And when it gamed our reward, here's how we caught it."

**The 3-minute stage version** walks through the five-step training story from the journal and the trust screen, and leaves time for questions.

**Likely judge questions, with answers ready**

- *Why train a model instead of prompting a big one?* The eval numbers, plus latency, cost, and a path to running on the phone.
- *Isn't Gemini doing the real work?* Gemini handles vision, images and writing training data. Every outfit on screen comes from our model, and the fallback is labeled.
- *Is the reward gameable?* It was, and the journal shows how we found and fixed it. The gates (schema, no invented items) zero out the score.
- *What's real and what's simulated?* Say it plainly: the catalog and prices are real, payment runs on a real Stripe Issuing virtual card in Stripe's sandbox, so the card's limit is enforced by Stripe but no real money moves, no order reaches the store (the receipt links to each item's real product page), try-on is a hosted image model.
- *Could it really buy things?* In production, through ACP: the agent places the order at stores that support it and pays with a Stripe Shared Payment Token limited to that store, amount and expiry, the same limits as our mandate (section 8).
- *Privacy?* You choose what to share, photos aren't stored, delete my data, and face matching asks you to confirm your face, says what it computes, and keeps nothing.

---

## 12. Risks and fallbacks

| Risk | Fallback |
| --- | --- |
| No GPU free (`CAPACITY_UNAVAILABLE` or `QUOTA_EXCEEDED`) | Follow the alternatives listed in the error. Change shape or provider instead of retrying the same one. Start the first run by 8 PM so there's time. |
| Our model isn't better | Ship the best checkpoint, report the honest numbers, and switch to Applied Intelligence if the learning story is weak. |
| Veri deployment cold start during judging | `veri deployments wake <id>` 10 minutes before. The backend falls back to base Llama, then Gemini, with a visible label. |
| Try-on is slow (10–20 s) or looks bad | Generate the demo outfits' try-ons ahead of time. Show progress. The flat-lay always works. |
| A library needs native code that Expo Go lacks (Face ID, Session Replay, on-device face matching) | Stay in Expo Go for the demo path. Build a development build only if one of us has Xcode set up and the time. |
| Two phones scan at once and collide. All three models (pose and two face models) are shared by every request, and the pose model's `predict` isn't thread-safe. | Fix 4 in [backend/SCAN_FIXES.md](backend/SCAN_FIXES.md): one lock around all model work, and one pose `predict` call per batch. |
| A fresh server install crashes on import, because `facenet-pytorch` isn't in `requirements.txt` (it's installed separately with `pip install facenet-pytorch --no-deps`). | Put the step in the README's setup section, and tell each other when a dependency changes. |
| The phone can't reach the laptop on venue Wi-Fi | `npx expo start --tunnel`, tested Saturday, not Sunday morning. |
| Secrets in a public repo | Keys only in `backend/.env`. Check `git log -p` for keys before making the repo public. |
| Credits run out | `veri billing balance` before each run. `--min-replicas 0` on every deployment. Stop deployments overnight if we aren't using them. |

---

## 13. Open questions to look into

Not urgent right now. Each has an owner and a time it must be answered by. Answered so far: Veri trains the ungated Llama mirror (section 5, Base model), and the store list is settled (section 5, Catalog).

| Question | How to answer it | By |
| --- | --- | --- |
| Can our Stripe sandbox account use Issuing by API? Stripe's developer docs say yes with test keys; a Stripe support article says to talk to sales first. Also check that the card's `brand` is Visa. | Turn on Issuing in the sandbox dashboard and create one card with `sk_test`. If it's blocked, use the fallback in section 8. | Person B, Saturday, before building `/checkout` |
| Is a sandbox payment with a simulated order fine for the Visa track? | Ask the Visa mentors at the event, showing the mandate refusal and the Stripe decline. | Person B, Saturday, before building `/checkout` |
| What candidate list size should the live app use? | The candidate-size table in section 6. Start at 50. | Person A, Sunday morning |

---

## 14. Submission checklist

- [ ] Devpost: what it does, the problem, **Model Learning** as the track, the five-step training story, the eval table, and one paragraph per challenge on how it's met: Veri, Visa, Paper, Sentry, MLH Gemini, MLH GoDaddy Registry domain.
- [ ] Landing page live on the domain, with the demo video and the QR code.
- [ ] Mark anything built before the event (the Expo template, the Veri skill file) as pre-existing.
- [ ] Public GitHub repo with a README: setup, architecture, how to rerun training and eval. `training/JOURNAL.md` included.
- [ ] Demo video, 2–3 minutes, showing the eval chart, the A/B result and the mandate refusal.
- [ ] Paper file link, model link on Hugging Face.
- [ ] Whole team at the table for judging at 12:30 PM Sunday.
- [ ] After judging: stop every Veri deployment (`veri deployments list`).
