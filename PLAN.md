# PLAN: an AI stylist that builds whole outfits and checks out safely

Working name: **As If** (from *Clueless*, whose digital closet inspired this). Swap it freely.

LA Hacks AI Hackathon 2026, team of 2. Hacking ends **Sunday Oct 18, 12:00 PM PDT**. See [LA_HACKS.md](LA_HACKS.md) for rules, judging and schedule.

## Contents

1. [Pitch](#1-pitch)
2. [Track and challenge strategy](#2-track-and-challenge-strategy)
3. [Product](#3-product)
4. [The model: what we train and how we prove it learned](#4-the-model-what-we-train-and-how-we-prove-it-learned)
5. [Architecture](#5-architecture)
6. [Trust, privacy and checkout](#6-trust-privacy-and-checkout)
7. [Scope: must-have, stretch, cut](#7-scope-must-have-stretch-cut)
8. [Who does what, and when](#8-who-does-what-and-when)
9. [Demo script](#9-demo-script)
10. [Risks and fallbacks](#10-risks-and-fallbacks)
11. [Submission checklist](#11-submission-checklist)

---

## 1. Pitch

**One line:** Pick a piece you love, and a small stylist model that we trained ourselves builds the rest of the outfit around it from your own style and within your budget, shows it on you, and checks out with a Visa spending limit the agent can't go over.

**The problem.** Online clothes shopping fails in three places:

1. **People think in outfits; stores sell single items.** You find a jacket and then have to work out the shoes, the trousers and what you already own that goes with it.
2. **You can't see it on you until it arrives.** So you guess, and you return it.
3. **Letting an AI buy for you feels unsafe.** A shopping agent that can spend money needs limits you set and can see.

**The user.** Someone who shops online, has a recognizable personal style, and is tired of returns. In the demo it's one of us, with our real photos.

**Why this wins over "another LLM wrapper":** the stylist isn't a prompt on a frontier model. It's a 3B open model post-trained on Veri with a reward that checks real constraints (budget, catalog, outfit completeness, color and formality rules, the user's style). We show measured before-and-after numbers. A small model that follows these rules reliably is cheap, fast and could one day run on the phone, so photos never need to leave it.

---

## 2. Track and challenge strategy

### Main track: Model Learning (recommended), Applied Intelligence as the fallback

Model Learning's description is "Build systems that learn, adapt, and improve from data. Create innovative models that uncover patterns, make predictions, or solve complex problems." The project qualifies **if the trained model is the core of the system and we can show it improved**, not if a fine-tune sits off to the side. That shapes the plan:

| Model Learning asks for | What we show |
| --- | --- |
| Learns from data | SFT (supervised fine-tuning: training on example answers) on outfits a strong model wrote, kept only if they pass our reward, then GRPO (reinforcement learning against a scoring function) on a reward that checks real constraints. |
| Improves | A held-out eval: base Llama, then SFT, then GRPO, against a frontier model as a reference. One chart in the pitch. |
| Adapts | The style profile updates from "How did it fit?" feedback and outfit thumbs up or down. Stretch: a DPO round (training on preferred-versus-rejected pairs) on the feedback we gather from real people during the event. |

Decide by **Saturday 10 PM**: if the first training run hasn't started by then, or the eval shows no gain, switch the Devpost entry to Applied Intelligence. The app and the pitch stay the same apart from the emphasis. We pick exactly one main track.

The judge's likely question is "Why not just prompt GPT or Gemini?" The answer has to be numbers: how often the base model breaks budget, invents items or leaves out shoes, against how often ours does, plus latency and cost per outfit.

### Company challenges

| Challenge | Fit | What it takes from us | Priority |
| --- | --- | --- | --- |
| **veri.studio**, best use of an open model ($800) | Strong. Requirement: "Use our platform to train an open-source model." | The training pipeline in section 4, which we need anyway. | Core |
| **Visa**, Future of Shopping ($2,000) | Strong. It's an AI shopping product end to end. Weights: innovation 25%, UX 25%, technical execution 20%, commerce impact 15%, trust and responsibility 15%. | The spending-limit checkout and trust screen (section 6), plus a commerce-impact claim about fewer returns, with a cited source. | Core |
| **Paper**, Best Designed Hack ($1,500 / $1,000 / $500) | Strong. Fashion is visual, and the judging rewards "personal craft and character" over AI-looking design. | Design the key screens in Paper first, with a real style guide (type, color, spacing), and build to match. Paper's MCP server lets an agent read the canvas while coding. Redeem `LAHACKS26`. | Core |
| **Sentry**, Best Use of Sentry (guaranteed interviews) | Good. Needs Sentry plus at least two products beyond error monitoring, and "show how observability shaped what you built". | Tracing across app, backend, Veri and Gemini; Logs; AI agent monitoring on the model calls. About 1–2 hours if we set it up in the first hour so data piles up. Mobile Session Replay needs a development build (see section 10), so we don't count on it. | Medium |
| **MLH Best Use of Gemini API** | Free if we use Gemini for photo reading and try-on, which the plan does. | Mention it on Devpost. | Low effort |
| **MLH Best Domain Name (GoDaddy Registry)** | From the original idea. | Register a domain and put the landing and privacy page on it. Check MLH's offer for which domain endings are free. | Low effort |
| **MLH Commit Fellowship category** | Needs a working prototype and a real problem, which we'll have. | Opt in on Devpost and fill in the extra form. | Low effort |

**Skipped, and why:**

- **Fetch.ai:** the whole workflow has to run inside ASI:One with no custom app, which throws away our app and design.
- **Browser Use:** live product search on the web is slow and flaky in a demo. A curated catalog of real products is safer.
- **Workday, Intuit, QNX, Espressif, Even Realities, Base44, Creao, Photon, StepFun:** the problem or the required platform doesn't match.
- **Cognition (Devin):** judged on what you build with Devin. Only worth it if we use Devin's free credits for real work anyway.

---

## 3. Product

### Core loop

1. **Style profile from your photos.** Pick 10–20 photos of outfits you wear or like. A vision model tags each one (garments, colors, fit, formality) and the backend turns the tags into a style profile you can read and edit: "Mostly neutrals with one accent color, relaxed fits, smart-casual, avoids logos."
2. **Pick an anchor and a budget.** Choose one item from the catalog (or "I need an outfit for…"), set a budget and an occasion.
3. **Outfit cards.** The trained stylist returns 2–3 complete outfits built around the anchor, each with a total price and a one-line reason ("the cream knit picks up the off-white sneaker sole"). Swap any single piece.
4. **Try it on.** See the outfit on your own full-body photo.
5. **Checkout under a limit.** The agent proposes a cart. You approve it against a spending limit you set, and the backend refuses anything over it.
6. **"How did it fit?"** After delivery (simulated in the demo), rate fit and style. The profile updates, and the next outfits change.

### Screens

Design these in Paper before building. The first six are the demo path.

1. **Welcome and consent:** what we read, what we keep, the choice between picking photos and scanning.
2. **Pick your photos:** the system photo picker, 10–20 shots.
3. **Your style:** the profile as a short, editable summary with the photos grouped into looks.
4. **Build:** anchor item, budget slider, occasion.
5. **Outfits:** 2–3 cards, total price, reasons, swap a piece.
6. **Try-on:** your photo wearing the outfit, plus a flat-lay view.
7. **Checkout:** the cart, the spending limit, the tokenized card, confirm.
8. **Trust:** what data is used, delete my data, AI use policy, merchant impact.
9. **How did it fit?:** feedback that updates the profile.

### Catalog

Use 50–80 **real products** (real brand, price, image and retailer link) across tops, bottoms, outerwear, shoes and accessories, kept in `catalog.json`. Real products make the demo believable and give the reward function something concrete to check. Each item has:

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

---

## 4. The model: what we train and how we prove it learned

### Task

Input: the style profile, budget, occasion, anchor item and about 25 candidate items the backend has pre-filtered from the catalog (right slots, roughly in budget). Output: strict JSON.

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

`Llama-3.2-3B-Instruct` from an **ungated community mirror** on Hugging Face. Veri's guide warns that gated `meta-llama/*` repos fail after the GPU has booted and started billing. 3B trains on one L4 GPU and serves on one L4. Run `veri jobs estimate` on it first. If Veri rejects the Llama architecture, fall back to `Qwen/Qwen3-4B` and say so on Devpost.

### Data, generated Saturday afternoon

1. Write about 400 synthetic style profiles across a spread of styles, body-neutral sizes, budgets ($60–$400) and occasions. Use a strong model to write them, with a fixed seed list so they vary.
2. For each profile, choose an anchor item and a candidate set from the catalog. That gives the **prompts**.
3. Split them: about 300 for training, about 100 held out for evaluation. Never train on the eval set.
4. For SFT, have the strong model answer the training prompts, score every answer with the reward function, and keep only answers that score high.

Veri needs one prompt format per JSONL file. Mixing plain-string prompts with message-list prompts crashes the trainer after the GPU boots.

### Reward function

Deterministic, fast, no network: Veri runs it inside the trainer. The catalog is embedded in `reward.py`. The profile, budget, anchor and candidates ride along as extra dataset columns and arrive in `**kwargs`.

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

Before any GPU time: unit-test the reward on hand-written good and bad outfits. A reward that scores everything the same teaches GRPO nothing.

### Training runs

1. **SFT** on the filtered answers. `sft_text`, LoRA, one L4. Short.
2. **GRPO** from the SFT checkpoint with the reward above. One L4, `max_steps` about 100, 4–8 rollouts per prompt. Price it first with `veri jobs estimate`.
3. LoRA runs must push **merged** weights to a **public** Hugging Face repo (`[hf_push] artifact = "merged"`, `private = false`). Veri can't serve a bare LoRA adapter.
4. Serve on one L4 with `--min-replicas 0`. Wake it 10 minutes before judging. Stop every deployment when done.
5. Stretch: **DPO** on preference pairs from real people at the event (outfit thumbs up or down, "How did it fit?"). This is the honest form of "learns from users", and becomes v2 if it's ready Sunday morning.

### Eval: the chart that carries the pitch

Run the 100 held-out prompts through each model and report:

| Metric | Base Llama 3B | + SFT | + GRPO | Frontier model (reference) |
| --- | --- | --- | --- | --- |
| Valid JSON | | | | |
| No invented items | | | | |
| Complete outfit | | | | |
| Within budget | | | | |
| Mean reward | | | | |
| Profile match (LLM-judged, blind, 50 samples) | | | | |
| Median latency and cost per outfit | | | | |

Fill it in from real runs only. If GRPO doesn't beat SFT, report that and ship SFT: an honest negative result plus a clear explanation still scores on technical depth.

---

## 5. Architecture

```
Expo app (Expo Router)                 FastAPI backend                      Models
─────────────────────                  ───────────────                      ──────
photo picker ───── photos ───────────▶ POST /profile ──────────────────────▶ Gemini (vision): tag each photo
                                         builds profile from tags
build screen ───── anchor, budget ───▶ POST /outfits ── candidates ────────▶ Veri deployment: tuned Llama 3B
                                         retrieve, call, validate, retry once     (fallback: base model or Gemini)
try-on screen ──── photo + items ────▶ POST /tryon ────────────────────────▶ Gemini image editing
checkout ───────── cart ─────────────▶ POST /checkout/mandate, /confirm      enforces the spending limit
feedback ───────── ratings ──────────▶ POST /feedback → profile update, DPO pairs
trust screen ──────────────────────────▶ DELETE /me
                 Sentry: traces, logs and AI-call monitoring on both sides
```

- **App:** this repo. Expo SDK per `package.json`, TypeScript, Expo Router with routes in `src/app/` (see [AGENTS.md](AGENTS.md)). Photos come from `expo-image-picker`, which works in Expo Go. Images are shrunk on the phone with `expo-image-manipulator` before upload.
- **Backend:** FastAPI in `server/`. State lives in memory or SQLite, per session. No Supabase: it adds setup and nothing the demo needs. For the demo it runs on a laptop behind a tunnel, or on a small cloud VM if time allows.
- **Secrets:** the Gemini and Veri keys live only on the backend, in `.env.local`. The repo goes public for submission, and anything the phone app ships can be read.
- **Validation:** the backend runs the same checks as the reward on every model answer, so a bad answer gets one retry and never reaches the screen. The training reward and the runtime guard are one piece of code.
- **Training code:** `training/` holds data generation, `reward.py`, the eval script and the Veri configs, so judges can rerun it.

---

## 6. Trust, privacy and checkout

Trust is 15% of Visa's score and the main worry people have with agents that spend money, so it gets real screens, not a footnote.

**Photos**

- You choose the photos with the normal picker. We don't ask for the whole camera roll.
- Photos are processed for the session and not stored. Only the text tags and the profile are kept, and you can read and edit both.
- One tap deletes everything: profile, feedback and the session's photos.

**Checkout: a spending mandate the agent can't exceed**

The flow follows the idea behind Visa's agentic commerce work, where the agent gets a payment token with limits instead of the card itself. Ask the Visa team at the event whether a sandbox exists. If not, simulate it and label it as simulated.

1. You set a **mandate**: a maximum amount, a category (apparel), an expiry (24 hours).
2. The agent only ever holds a **token reference** (`Visa •••• 4242, agent token`). It never sees the card number.
3. The backend checks every cart against the mandate. Over the limit means refused, with the reason shown.
4. You confirm the final cart with a biometric prompt (`expo-local-authentication`; Face ID needs a development build, and Expo Go falls back to the device passcode).
5. The receipt shows what was bought, what it cost and what's left of the mandate.

**Demo moment:** ask the agent to "make it nicer". It suggests a $90 upgrade, the mandate refuses it, and the app offers the closest outfit that fits. That shows the guardrail working, not just promised.

**Merchant impact panel:** outfit-level selling raises basket size, and fit feedback should cut returns. Cite a real source for return rates on the panel and on Devpost. Don't invent numbers.

---

## 7. Scope: must-have, stretch, cut

Two people, about 22 hours. Each feature has to earn its place in the 3-minute demo.

**Must-have (the demo path)**

- Photo picker, then a style profile
- Anchor + budget, then 2–3 outfit cards from the **tuned** model
- Try-on on one photo, with the flat-lay as a fallback
- Mandate checkout with a refusal, and the trust screen with delete my data
- The eval chart with real numbers
- Paper designs for the demo-path screens, and the app built to match them

**Stretch, in this order**

1. "How did it fit?" feedback updating the profile
2. Sentry tracing, logs and AI monitoring with a written "what it showed us"
3. DPO v2 from feedback gathered at the event
4. Domain and landing page
5. Automatic camera-roll scan as an alternative to the picker. This needs `expo-media-library`, filtering thousands of photos down to outfit shots, and many vision calls, so the picker comes first.

**Cut:** makeup recommendations, sharing with friends, social media integration, live web product search, Supabase.

---

## 8. Who does what, and when

**Person A: model and backend.** Catalog, data generation, reward, Veri runs, eval, `/outfits`, `/profile`.
**Person B: design and app.** Paper style guide and screens, Expo Router setup, every screen, try-on, checkout, Sentry.

Times are PDT.

| When | Person A | Person B |
| --- | --- | --- |
| **Sat 2–4 PM** | Get Veri credits from @daniung on Discord and redeem them **before** any run. `veri whoami`. Build `catalog.json` (real products). Freeze the output schema. | Paper style guide: type, color, spacing, one hero screen. Move the app to Expo Router. Add Sentry to app and backend. |
| **Sat 4–7 PM** | Generate profiles and prompts. Write `reward.py` and its unit tests. Run the base model eval. | Paper: the six demo-path screens. Build picker → profile → build screens against mocked responses. |
| **Sat 7–10 PM** | Start SFT (about 8 PM), then GRPO from it. `/profile` with Gemini. `/outfits` against the base model. **10 PM: decide the main track.** | Outfit cards, swap a piece, checkout, trust screen. Mandate endpoints. |
| **Overnight** | Watch runs (`veri jobs logs <id> -f`). Eval each checkpoint. Push merged weights, deploy the winner. | Try-on endpoint and screen, flat-lay fallback. Polish against Paper. |
| **Sun 6–8:30 AM** | Point `/outfits` at the tuned model. Final eval table and chart. Stretch: DPO v2. | End-to-end on a real phone over the venue Wi-Fi (`npx expo start --tunnel` if needed). Bug fixes. **8:30 AM: feature freeze.** |
| **Sun 8:30–10:30 AM** | Devpost write-up: track, every challenge and how it's met, the eval table. README. | Record the 2–3 minute demo video. Screenshots. Sentry "what it showed us". |
| **Sun 10:30 AM–12 PM** | Buffer. Repo public, no secrets in it. Submit by 11:30. | Buffer. Rehearse the 60–90 second pitch. |
| **Sun 12:20 PM** | Wake the Veri deployment before judging. | Phone charged, demo account loaded. |

---

## 9. Demo script

**60–90 second pitch (judging round 1)**

1. *Problem (10 s):* "Stores sell items, people wear outfits, and you can't see it on you until it arrives."
2. *Profile (15 s):* pick photos, show the style summary.
3. *Outfits (20 s):* tap a jacket, set $200, three outfits appear with reasons.
4. *Try-on (10 s):* the outfit on your photo.
5. *Checkout (15 s):* "make it nicer", the mandate refuses, approve the version that fits.
6. *The model (15 s):* the eval chart. "This is a 3B Llama we post-trained on Veri. Base Llama breaks budget or invents items X% of the time; ours, Y%."

**The 3-minute stage version** adds the reward design and the trust screen, and leaves time for questions.

**Likely judge questions, with answers ready**

- *Why train a model instead of prompting a big one?* The eval numbers, plus latency, cost, and a path to running on the phone.
- *Is the reward gameable?* The gates (schema, no invented items) zero out the score, and we checked samples by hand.
- *What's real and what's simulated?* Say it plainly: the catalog and prices are real, payment is a simulated tokenized flow, try-on is a hosted image model.
- *Privacy?* The picker, session-only photos, delete my data.

---

## 10. Risks and fallbacks

| Risk | Fallback |
| --- | --- |
| No GPU free (`CAPACITY_UNAVAILABLE` or `QUOTA_EXCEEDED`) | Follow the alternatives listed in the error. Change shape or provider, don't retry the same one in a loop. Start the first run by 8 PM so there's time. |
| The tuned model isn't better | Ship the best checkpoint, report the honest numbers, and switch the main track to Applied Intelligence if the learning story is weak. |
| Veri deployment cold start during judging | `veri deployments wake <id>` 10 minutes before. The backend falls back to the base model or Gemini, with a visible label. |
| Try-on is slow (10–20 s) or looks bad | Generate the demo outfits' try-ons ahead of time. Show progress. The flat-lay always works. |
| A library needs native code that Expo Go lacks (Face ID, Session Replay) | Stay in Expo Go for the demo path. Build a development build only if one of us has Xcode set up and the time. |
| The phone can't reach the laptop on venue Wi-Fi | `npx expo start --tunnel`, tested Saturday, not Sunday morning. |
| Secrets in a public repo | Keys only in `.env.local` on the backend. Check `git log -p` for keys before making the repo public. |
| Credits run out | `veri billing balance` before each run. `--min-replicas 0` on every deployment. Stop deployments overnight if we aren't using them. |

---

## 11. Submission checklist

- [ ] Devpost: what it does, the problem, **Model Learning** (or Applied Intelligence) as the track, and one paragraph per challenge on how it's met: Veri, Visa, Paper, Sentry, MLH Gemini, MLH domain, Commit Fellowship.
- [ ] Mark anything built before the event (the Expo template, the Veri skill file) as pre-existing.
- [ ] Public GitHub repo with a README: setup, architecture, how to rerun training and eval.
- [ ] Demo video, 2–3 minutes, showing the eval chart and the mandate refusal.
- [ ] Paper file link, eval table, model link on Hugging Face.
- [ ] Opt in to the Commit Fellowship category and fill in its form.
- [ ] Whole team at the table for judging at 12:30 PM Sunday.
- [ ] After judging: stop every Veri deployment (`veri deployments list`).
