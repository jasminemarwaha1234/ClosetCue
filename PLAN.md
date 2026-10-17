# PLAN: an AI stylist that builds whole outfits and checks out safely

Working names, to choose between later: **As If** (from *Clueless*, whose digital closet inspired this) or **Fitly** (used in the current photo-permission text in [app.json](app.json)). Once we pick, update that text to match.

LA Hacks AI Hackathon 2026, team of 2. Hacking ends **Sunday Oct 18, 12:00 PM PDT**. See [LA_HACKS.md](LA_HACKS.md) for rules, judging and schedule.

## Contents

1. [Pitch](#1-pitch)
2. [Track and challenge strategy](#2-track-and-challenge-strategy)
3. [Product](#3-product)
4. [Architecture and which model does what](#4-architecture-and-which-model-does-what)
5. [The model: what we train](#5-the-model-what-we-train)
6. [How we validate the model](#6-how-we-validate-the-model)
7. [The training journal: how we explain it to judges](#7-the-training-journal-how-we-explain-it-to-judges)
8. [Trust, privacy and checkout](#8-trust-privacy-and-checkout)
9. [Scope: must-have, stretch, later](#9-scope-must-have-stretch-later)
10. [Who does what, and when](#10-who-does-what-and-when)
11. [Demo script](#11-demo-script)
12. [Risks and fallbacks](#12-risks-and-fallbacks)
13. [Open questions to look into](#13-open-questions-to-look-into)
14. [Submission checklist](#14-submission-checklist)

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
| Adapts | Each user's style profile updates from their feedback. Every "which outfit is better?" answer becomes a preference pair, and a DPO round (training on preferred versus rejected answers) on those pairs gives model v2. |

The judges' likely question is "Why not just prompt GPT or Gemini?" The answer has to be numbers: how often the base model breaks budget, invents items or leaves out shoes, against how often ours does, plus latency and cost per outfit.

**Fallback.** If by **Saturday 10 PM** the first training run hasn't started, or the eval shows no gain, switch the Devpost entry to Applied Intelligence. The app and pitch stay the same apart from the emphasis. We pick exactly one main track.

### Company challenges

| Challenge | Fit | What it takes from us | Priority |
| --- | --- | --- | --- |
| **veri.studio**, best use of an open model ($800) | Strong. Requirement: "Use our platform to train an open-source model." | Sections 5–7, which we're doing anyway. The training journal doubles as our Veri write-up. | Core |
| **Visa**, Future of Shopping ($2,000) | Strong. It's an AI shopping product end to end. Weights: innovation 25%, UX 25%, technical execution 20%, commerce impact 15%, trust and responsibility 15%. | The spending-limit checkout and trust screen (section 8), plus a commerce-impact claim about fewer returns, with a cited source. | Core |
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
2. **Style profile from your photos.** You give the app photos of outfits you wear (see "Getting your photos" below). Gemini tags each one (garments, colors, fit, formality) and the backend turns the tags into a style profile you can read and edit: "Mostly neutrals with one accent color, relaxed fits, smart-casual, avoids logos." The profile is saved to your account.
3. **Pick an anchor and a budget.** Choose one item from the catalog (or "I need an outfit for…"), set a budget and an occasion.
4. **Outfit cards.** The trained stylist returns 2–3 complete outfits built around the anchor, each with a total price and a one-line reason ("the cream knit picks up the off-white sneaker sole"). Swap any single piece.
5. **Try it on.** See the outfit on your own full-body photo. The flat-lay view is the fallback.
6. **Checkout under a limit.** The agent proposes a cart. You approve it against a spending limit you set, and the backend refuses anything over it. Confirm with Face ID or the passcode, then see a receipt (section 8).
7. **Feedback.** "How did it fit?" updates your profile right away and becomes training data for the next model.

**Available at any time, outside the loop:**

- **Trust:** what data is used, and delete my data.
- **Which is better?:** the blind A/B screen (section 6). It shows pairs prepared ahead of time (base Llama against our model on held-out prompts), not the user's own request, so it's a separate destination that friends at the venue can use without making a profile. Each answer is a preference pair for v2-dpo.

### Getting your photos

The user chooses one of two ways to share photos. Both ship as equal options.

| Option | How | Expo package | Status |
| --- | --- | --- | --- |
| **Pick photos** | The system picker, multi-select up to 20. On iOS the picker runs outside our app, so it needs no photo-library permission. | `expo-image-picker` (in Expo Go) | To build |
| **Scan the camera roll** | Read the 300 newest photos and keep only the ones that show you in an outfit, using outfit detection and face matching (below). | `expo-media-library` (its `legacy` API), plus pose and face models on the server | Built as a prototype in [App.tsx](App.tsx) and `backend/main.py` |

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

**Plan:** keep it on the server for the demo, keep the embedding only for the session (done), put it behind a consent screen that says what it computes (section 8; not done yet), and tell judges that on-device matching is the production design. That honesty helps the Visa trust score.

### Screens

Design these in Paper before building. The first six are the demo path.

1. **Welcome and consent:** what we read, what we keep, and the choice of how to share photos.
2. **Share your photos:** pick photos or scan the camera roll. The scan asks "Is this you?" before it filters.
3. **Your style:** the profile as a short, editable summary with the photos grouped into looks.
4. **Build:** anchor item (chosen in a catalog picker), budget slider, occasion.
5. **Outfits:** 2–3 cards, total price, reasons, swap a piece.
6. **Try-on:** your photo wearing the outfit, plus a flat-lay view.
7. **Checkout:** the cart, the spending limit, the tokenized card, confirm.
8. **Which is better?:** the blind A/B screen (section 6).
9. **Trust:** what data is used, delete my data, AI use policy, merchant impact.
10. **How did it fit?:** feedback that updates the profile.

### Routes

Every file in `src/app/` is a screen in Expo Router. Folders in parentheses, like `(tabs)`, group screens under one layout without adding to the URL. The demo path (Welcome → Photos → Style → Build → Outfits → Try-on → Checkout) is one straight push through the stack. After onboarding, a tab bar holds the four places a user returns to.

```
src/app/
├── _layout.tsx              root Stack; starts the anonymous Supabase session
├── index.tsx                redirects to onboarding (no profile yet) or to the tabs
├── onboarding/
│   ├── welcome.tsx          1. Welcome and consent
│   ├── photos.tsx           2. Share your photos (pick / scan)
│   └── is-this-you.tsx      2. "Is this you?" during the scan (an inline card in App.tsx today)
├── (tabs)/
│   ├── _layout.tsx          tab bar: Build · Style · Rate · Trust
│   ├── index.tsx            4. Build
│   ├── style.tsx            3. Your style (also the last onboarding step)
│   ├── rate.tsx             8. Which is better?
│   └── trust.tsx            9. Trust
├── pick-item.tsx            modal: browse the catalog to choose the anchor
├── outfits.tsx              5. Outfits
├── tryon/[outfitId].tsx     6. Try-on
├── checkout/
│   ├── index.tsx            7. Checkout, including the refusal
│   └── receipt.tsx          receipt and what's left of the mandate
└── fit/[orderId].tsx        10. How did it fit?
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
                                          builds profile ────────────────▶ Supabase: profiles
anchor, budget ────────────────────────▶ POST /outfits ── candidates ────▶ Veri: our Llama 3B
                                          retrieve, call, guard, retry once
photo + items ─────────────────────────▶ POST /tryon ────────────────────▶ Gemini image editing
cart ──────────────────────────────────▶ POST /checkout/mandate, /confirm   enforces the spending limit
A/B choice, fit rating ────────────────▶ POST /feedback ─────────────────▶ Supabase: feedback (→ DPO data)
trust screen ──────────────────────────▶ DELETE /me ─────────────────────▶ Supabase: delete user's rows
                 Sentry: traces, logs and AI-call monitoring on both sides
```

- **App:** this repo. Expo SDK 57, TypeScript, Expo Router with routes in `src/app/` (see [AGENTS.md](AGENTS.md)). Photos are shrunk on the phone with `expo-image-manipulator` before upload.
- **Backend:** FastAPI in `server/`. It's in `backend/` today and gets renamed when we move to the repo layout below. For the demo it runs on a laptop behind a tunnel, or on a small cloud VM if time allows. The pose and face models run inside the server process, on CPU.
- **Supabase** stores accounts, style profiles and feedback:
  - **Anonymous sign-in** gives every user an account with no sign-up screen, so judges and friends can start in one tap. Email sign-in can come later.
  - Tables: `profiles` (one per user, the style profile as JSON), `feedback` (A/B choices and fit ratings, with the outfits shown). The `feedback` table exports straight to the DPO dataset.
  - Photos are never stored. "Delete my data" deletes the user's rows.
  - The phone only talks to Supabase for sign-in. Reads and writes go through the backend, which holds the service key.
- **Secrets:** the Gemini, Veri and Supabase service keys live only on the backend, in `.env.local`. The repo goes public for submission, and anything the phone app ships can be read.
- **The guard:** the backend runs the reward's checks on every model answer. A failing answer gets one retry and never reaches the screen.

### Repo layout

Everything lives in this one repo. The Expo app stays at the root, which is what [AGENTS.md](AGENTS.md) and the Expo commands expect. Today the app is one file ([App.tsx](App.tsx)) and the server is one file in `backend/`. When we move to this layout, `backend/` becomes `server/`, and the code in `backend/main.py` splits into the files below.

```
LaHacksAI/
├── package.json, app.json, tsconfig.json   the Expo app
├── src/
│   ├── app/          routes only (section 3)
│   ├── components/   OutfitCard, ItemTile, BudgetSlider, PhotoGrid…
│   ├── api/          client.ts (fetch + EXPO_PUBLIC_API_BASE_URL), types.ts, mocks.ts
│   ├── lib/          supabase.ts, sentry.ts, photos.ts (the shrink and scan helpers now in App.tsx)
│   └── theme/        colors, type and spacing from the Paper style guide
├── assets/
├── server/           FastAPI
│   ├── main.py       creates the app, includes the routers
│   ├── routes/       profile.py, outfits.py, tryon.py, checkout.py, feedback.py, me.py, scan.py, faces.py
│   ├── services/     gemini.py, veri.py, supabase.py, retrieval.py, pose.py, faces.py
│   ├── schemas.py    Pydantic request and response models
│   ├── test_framing.py   prints the framing for local photos
│   └── requirements.txt
├── training/
│   ├── catalog.json  the catalog; the server reads it too
│   ├── reward.py, test_reward.py   the server imports reward.py as the guard
│   ├── gen_profiles.py, build_prompts.py, gen_sft.py, eval.py
│   ├── configs/      one Veri config per run
│   ├── data/         JSONL files (gitignore the large ones)
│   └── JOURNAL.md
├── landing/          static page for the GoDaddy Registry domain
└── README.md, PLAN.md, LA_HACKS.md
```

Rules that matter more than the exact folders:

- **One copy of `catalog.json` and of `reward.py`.** The same reward trains the model and guards live answers, so a second copy that drifts means the guard rejects answers the model was trained to give. Run the server from the repo root (`uvicorn server.main:app`) so it can `import training.reward`. If `reward.py` embeds the catalog for Veri (section 5), generate that copy from `catalog.json` instead of editing it by hand.
- **API shapes in two places:** `server/schemas.py` and `src/api/types.ts`. Freeze both in the first hour. `src/api/mocks.ts` returns fake data in those shapes, so the app can be built before the server is ready.
- **One file per endpoint in `server/routes/`**, so both of us can work on the server without merge conflicts (section 10).

---

## 5. The model: what we train

### Task

Input: the style profile, budget, occasion, anchor item, and about 25 candidate items that the backend pre-filtered from the catalog (right slots, roughly in budget). Output: strict JSON.

```json
{
  "outfits": [
    {
      "items": ["top_012", "bottom_004", "shoes_009", "outerwear_002"],
      "total": 186.0,
      "reason": "One short sentence a person would say."
    }
  ]
}
```

The backend retrieves; the model chooses and explains. That keeps prompts short enough for a 3B model and makes every rule checkable.

### Base model

`Llama-3.2-3B-Instruct` from an **ungated community mirror** on Hugging Face. Veri's guide warns that gated `meta-llama/*` repos fail after the GPU has booted and started billing. 3B trains on one L4 GPU and serves on one L4. Whether Veri's trainer accepts the Llama mirror is an open question (section 13). If it doesn't, fall back to `Qwen/Qwen3-4B` and say so on Devpost.

### Catalog

50–80 **real products** (real brand, price, image and retailer link) across tops, bottoms, outerwear, shoes and accessories, in `catalog.json`. Real products make the demo believable and give the reward something concrete to check.

```json
{
  "id": "top_012",
  "name": "Relaxed cotton crewneck",
  "brand": "…",
  "slot": "top",
  "price": 38.0,
  "colors": ["cream"],
  "formality": 2,
  "style_tags": ["minimal", "relaxed"],
  "season": ["fall", "winter", "spring"],
  "image": "https://…",
  "url": "https://…"
}
```

Formality runs from 1 (athleisure) to 5 (formal). Slots are `top`, `bottom`, `dress`, `outerwear`, `shoes`, `accessory`.

### Data

1. Have Gemini write about 400 synthetic style profiles across a spread of styles, budgets ($60–$400) and occasions, from a fixed seed list so they vary.
2. For each profile, pick an anchor item and a candidate set from the catalog. That gives the **prompts**.
3. Split by profile: about 300 for training, about 100 held out for evaluation. A profile never appears in both.
4. For SFT, have Gemini answer the training prompts, score every answer with the reward, and keep only high scorers.

Veri needs one prompt format per JSONL file. Mixing plain-string prompts with message-list prompts crashes the trainer after the GPU boots. Run `veri datasets check` on every file before upload.

### Reward function: our definition of a good outfit

Deterministic, fast, no network, because Veri runs it inside the trainer. The catalog is embedded in `reward.py`. The profile, budget, anchor and candidates go in as extra dataset columns and arrive in `**kwargs`.

| Check | Score |
| --- | --- |
| Output parses as the JSON schema | Gate: 0 overall if it fails |
| Every item ID is in that prompt's candidate set (no invented items) | Gate |
| Includes the anchor | +1 |
| Complete outfit: top + bottom (or a dress) + shoes, at most one per slot except accessories | +1 |
| Total ≤ budget, and the stated total equals the real sum | +1, with a small bonus for using 60–100% of the budget |
| Color harmony from a small rule table (neutrals pair with anything, at most one accent color, a list of clashes) | 0 to +1 |
| Formality coherent: all items within 1 level of each other and of the occasion | +1 |
| Matches the profile: overlap of style tags, nothing from the profile's "avoid" list | 0 to +1 |
| Reason is one sentence and names at least one item | +0.5 |

The same code runs in the backend as a guard on every live answer (section 4), so the definition of "good" that trained the model also protects the demo.

### Training runs

1. **v0, the baseline.** Base Llama with our prompt, no training. Evaluated, not trained.
2. **v1-sft.** `sft_text` with LoRA on the filtered Gemini answers. One L4. Short.
3. **v1-grpo.** GRPO from the SFT checkpoint with the reward. One L4, `max_steps` about 100, 4–8 rollouts per prompt.
4. **v2-dpo** (stretch). DPO on preference pairs from the in-app A/B screen and outfit feedback, collected from real people at the event.

For every run, price it first with `veri jobs estimate`. LoRA runs must push **merged** weights to a **public** Hugging Face repo (`[hf_push] artifact = "merged"`, `private = false`), because Veri can't serve a bare LoRA adapter. Serve the winner on one L4 with `--min-replicas 0`.

---

## 6. How we validate the model

We don't trust a number until we've checked it ourselves. Five layers, cheapest first:

1. **Reward unit tests, before any GPU time.** About 20 hand-written outfits: clearly good, clearly bad, and edge cases (exactly at budget, a dress with no bottom, an invented ID). The reward must rank them the way we would. A reward that scores everything the same teaches GRPO nothing.
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

- You choose what to share: specific photos, or a scan of your 300 newest photos. Only small thumbnails leave the phone.
- **Face matching, during the scan.** Finding your face computes face embeddings for everyone in your 80 newest photos, not just you. None of them are stored. Your own face's embedding stays in the app's memory for the session, and "Not you? Reset my face" clears it. The consent screen says all of this plainly before the scan runs.
- Photos are processed for the session and not stored. Only the text tags and the profile are kept, and you can read and edit both.
- One tap deletes everything: profile, feedback and anything from the session.

**Checkout: a spending mandate the agent can't exceed**

A **mandate** is a set of rules you give the agent before it can buy: how much it may spend, on what, and for how long. The idea follows Visa's agentic commerce work, where an agent gets a limited payment token instead of your card. Ask the Visa team at the event whether a sandbox exists. If not, simulate it and label it as simulated.

1. You set the mandate: at most $200, apparel only, expires in 24 hours.
2. The agent only ever holds a **token reference** (`Visa •••• 4242, agent token`). It never sees the card number.
3. The backend checks every cart against the mandate. Over the limit means refused, with the reason shown.
4. You confirm the final cart with a biometric prompt (`expo-local-authentication`; Face ID needs a development build, and Expo Go falls back to the device passcode).
5. The receipt shows what was bought, what it cost and what's left of the mandate.

**Demo moment:** you say "make it nicer", the agent proposes a $90 upgrade that would push the cart past your $200 limit, and the backend refuses the cart and says why. The app then offers the closest outfit that fits. Judges see the limit enforced in code, not just promised in a policy.

**Merchant impact panel:** outfit-level selling raises basket size, and fit feedback should cut returns. Cite a real source for return rates on the panel and on Devpost. Don't invent numbers.

---

## 9. Scope: must-have, stretch, later

Two people, about 22 hours. The model work comes first: an app with no trained model behind it loses the track.

**Must-have**

- The training pipeline: catalog, data, reward with tests, SFT, GRPO, deployed model
- The eval table with real numbers, and the training journal
- Share photos in either of two ways (pick photos, or scan the camera roll with face matching), then a style profile saved in Supabase
- Anchor + budget, then 2–3 outfit cards from **our** model
- The blind A/B screen, writing to Supabase
- Try-on on one photo, with the flat-lay as a fallback
- Mandate checkout with a refusal, and the trust screen with delete my data
- Paper designs for the demo-path screens, and the app built to match them
- Landing page on a GoDaddy Registry domain: pitch, demo video, QR code to the app, privacy policy

**Stretch, in this order**

1. v2-dpo from A/B answers gathered at the event
2. "How did it fit?" feedback updating the profile
3. Sentry tracing, logs and AI monitoring, with a written "what it showed us"
4. Screenshots as inspiration: the scan currently skips screenshots. Instead, include them, tag them "inspiration" (outfits the user likes) as opposed to "worn" (camera photos of the user), and weigh the two differently in the style profile

**Later (after the hackathon, unless we're far ahead)**

- Makeup recommendations from skin type and tone
- Sharing outfits with friends
- Social media integration
- Live web product search instead of a fixed catalog

---

## 10. Who does what, and when

**Person A: model and backend.** Catalog, data, reward, Veri runs, eval, journal, `/outfits`, `/profile`, `/feedback`, Supabase.
**Person B: design and app.** Paper style guide and screens, Expo Router setup, every screen including the A/B screen, `/tryon`, `/checkout`, `DELETE /me`, `/scan`, `/faces/find-owner`, Sentry, domain and landing page, demo video.

The split works because training runs take 30–60 minutes of waiting. Person A writes server endpoints while a run trains.

### Staying unblocked

1. **Contract first (Sat 2–4 PM, together).** Agree on the outfit JSON schema, the request and response of every endpoint, and the `catalog.json` fields. Write them into `server/schemas.py` and `src/api/types.ts`, and have B write `src/api/mocks.ts` from them. After that, neither of us waits on the other.
2. **Split the server by file.** A owns `profile.py`, `outfits.py`, `feedback.py` and the `services/` files for Gemini, Veri and Supabase. B owns `tryon.py`, `checkout.py`, `me.py`, `scan.py`, `faces.py`, and the pose and face `services/`. `main.py` and `schemas.py` are shared: keep edits there small and pull before touching them.
3. **Integration checkpoints**, where the app swaps a mock for the real endpoint:
   - **Sat 10 PM:** `/profile` live, and `/outfits` against v0.
   - **Sun 6 AM:** `/outfits` against our trained model.
4. **Git:** short-lived branches, or push to `main` inside your own folders, and pull often.
5. **Watch A's load.** A is on the critical path, since no trained model means no Model Learning track. If A falls behind, B takes the Supabase setup or `/feedback`, both plain create, read, update and delete code.

Times are PDT. Shift them if we start late, but keep the 10 PM track decision and the 8:30 AM feature freeze.

| When | Person A | Person B |
| --- | --- | --- |
| **Sat 2–4 PM** | Get Veri credits from @daniung on Discord and redeem them **before** any run. `veri whoami`. Check the Llama mirror with `veri jobs estimate`. Build `catalog.json`. Freeze the output schema and, with B, the API shapes. Start `training/JOURNAL.md`. | Register the domain. Paper style guide: type, color, spacing, one hero screen. Move the app to Expo Router. Agree on the API shapes with A and write the mocks. |
| **Sat 4–7 PM** | Generate profiles and prompts. Write `reward.py` and its tests. Run the v0 eval. Set up Supabase (anonymous sign-in, two tables). | Paper: the demo-path screens. Build photos → profile → build screens against mocked responses. Add Sentry. |
| **Sat 7–10 PM** | Start v1-sft (by 8 PM), then v1-grpo from it. `/profile` with Gemini. `/outfits` against v0. **10 PM: confirm the track.** | Outfit cards, swap a piece, the A/B screen, checkout, trust screen. Mandate endpoints. |
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
5. *Checkout (10 s):* "make it nicer", the mandate refuses, approve the version that fits.
6. *The model (25 s):* the eval chart and the A/B win rate. "This is a 3B Llama we post-trained on Veri. Base Llama breaks budget or invents items X% of the time; ours, Y%. People preferred ours Z% of the time. And when it gamed our reward, here's how we caught it."

**The 3-minute stage version** walks through the five-step training story from the journal and the trust screen, and leaves time for questions.

**Likely judge questions, with answers ready**

- *Why train a model instead of prompting a big one?* The eval numbers, plus latency, cost, and a path to running on the phone.
- *Isn't Gemini doing the real work?* Gemini handles vision, images and writing training data. Every outfit on screen comes from our model, and the fallback is labeled.
- *Is the reward gameable?* It was, and the journal shows how we found and fixed it. The gates (schema, no invented items) zero out the score.
- *What's real and what's simulated?* Say it plainly: the catalog and prices are real, payment is a simulated tokenized flow, try-on is a hosted image model.
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
| Secrets in a public repo | Keys only in `.env.local` on the backend. Check `git log -p` for keys before making the repo public. |
| Credits run out | `veri billing balance` before each run. `--min-replicas 0` on every deployment. Stop deployments overnight if we aren't using them. |

---

## 13. Open questions to look into

Not urgent right now. Each has an owner and a time it must be answered by.

| Question | How to answer it | By |
| --- | --- | --- |
| Does Veri's trainer accept an ungated Llama 3.2 3B community mirror? If not, we use Qwen3-4B. | `veri jobs estimate` on a config with the mirror; ask at the Veri table if unclear. | Person A, before the first run |
| Does Visa have a sandbox or API for agent payment tokens at this event? | Ask the Visa team at their table. | Either, Saturday |

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
