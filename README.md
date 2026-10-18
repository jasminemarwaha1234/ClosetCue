# ClosetCue

**Pick one piece you love. ClosetCue builds the whole outfit around it, in your style and within your budget, shows it on you, and checks out under a spending limit the AI agent can't go over.**

<table>
  <tr>
    <td><img src="docs/screenshots/style.png" alt="Your style: the profile and closet read from your photos" width="250"></td>
    <td><img src="docs/screenshots/outfits.png" alt="Outfits: three complete looks around one anchor piece, with prices and reasons" width="250"></td>
    <td><img src="docs/screenshots/checkout.png" alt="Checkout: a cart refused for going over the spending limit" width="250"></td>
  </tr>
  <tr>
    <td align="center">Your style, from your photos</td>
    <td align="center">Outfits built around one piece</td>
    <td align="center">A cart refused over the limit</td>
  </tr>
</table>

Built in 24 hours at the [LA Hacks AI Hackathon 2026](https://la-ai-hackathon-2026.devpost.com/) (UCLA, Oct 17–18) by **Charlie Weinberger** ([@charlieweinberger](https://github.com/charlieweinberger)) and **Jasmine** ([@jasminemarwaha1234](https://github.com/jasminemarwaha1234)).

**Links:** [Landing page](landing/index.html) · [Model on Hugging Face](https://huggingface.co/CharlieBrown364/outfit-llama-v2-sft) · [Training journal](training/JOURNAL.md)

## Inspiration

People have closets full of clothes and still feel like they have nothing to wear. Shopping apps show one item at a time and know nothing about what you own, your style, or what you can afford. Styling advice online is either too generic ("build a capsule wardrobe") or built around influencers with budgets nothing like a student's. We wanted a tool that starts from one piece you love, learns your style from your own photos, and builds complete outfits around it within a budget you set. An AI agent that spends your money can feel scary, so we also made it trustworthy by design: it can never spend more than you allow.

## What it does

- **Learns your style from your photos:** style tags, colors, fits, things to avoid, and the clothes already in your closet.
- **Builds 2–3 complete outfits** around one anchor piece, from a catalog of real products or from your own closet, within your budget range and occasion.
- **Explains each outfit,** lets you swap or remove any piece, and links each item to its real store.
- **Shows the outfit on you** with an AI try-on on your own photo.
- **Checks out under a spending limit you set.** If a cart goes over, the app refuses it, explains why, and offers the closest outfit that fits.
- **A trust screen** shows what data we use and keep, and deletes everything in one tap.

## How we built it

- **App (Expo, React Native):** every screen designed in [Paper](https://paper.design) first, then built with Expo Router: sign in or guest mode, a two-handle budget slider, swappable outfit cards, a payment sheet, and the trust screen.
- **Catalog:** 1,011 real products scraped from 24 US stores, each with a real price, photo and product page, tagged by Gemini with colors, style tags, fit and formality.
- **Stylist model:** Llama 3.2 3B, post-trained on [Veri](https://www.veri.studio) against a reward function we wrote. It checks every outfit for a valid format, no made-up items, a complete look, staying in budget, and matching your style. The same checks guard every live answer, so a bad outfit never reaches the screen.
- **Backend (FastAPI):** finds photos of you in outfits with pose detection and face matching, makes try-on images with Gemini, and enforces the spending limit in our code and on a Stripe Issuing virtual card (test mode). Supabase stores profiles, ratings and spending limits.

**Results** on 20 held-out prompts:

| | Base Llama 3B | **Our model (shipped)** | Gemini |
| --- | --- | --- | --- |
| Valid answers, no invented items | 25% | **100%** | 100% |
| Outfits within budget | 53% | **72%** | 100% |
| Median response time | 5.2 s | **4.6 s** | 27 s |

Gemini still scores higher on overall outfit quality (94.6% of the best possible reward, against our 64.7%), so our model doesn't beat it on quality yet. In the app, the live guard closes much of that gap: in a live test of 14 requests, our model answered all 14 itself in 2–7.5 seconds, with every outfit complete and in budget. Raw outputs: [training/results/live/](training/results/live/).

## Challenges we ran into

- **Scraping:** our first scraper sent requests too fast and got us blocked by every store at once. It now sends one request every 3.5 seconds.
- **Messy data:** every store describes colors, sizes and categories differently, so we made a fixed vocabulary of colors, style tags and occasions that the catalog, the model and the app all share.
- **Teaching a small model strict rules:** it liked to go over budget, invent items, or forget shoes. Our first version got the outfit total wrong in 55 of 57 outfits, so we stopped asking it to add: code computes totals now, and constrained decoding means it can only name real items.
- **Reinforcement learning made it worse:** a GRPO run lost to plain fine-tuning on every metric, so we shipped the fine-tuned model and wrote down why in the [training journal](training/JOURNAL.md).
- **Privacy:** finding you in your camera roll means looking at everyone's faces in those photos, so nothing is ever stored.
- **What's possible in a weekend:** Face ID and Apple Pay don't work in Expo Go, and no store accepts a test card, so we built fallbacks and made the app honest about what is simulated.

## Accomplishments that we're proud of

- We trained our own model instead of just prompting a big one, and it answers about 6x faster than Gemini. The same rules that trained it also protect the live app.
- The spending limit truly can't be bypassed: Stripe enforces it on the card itself, so it holds even if our code had a bug.
- Every outfit is made of real products with real prices, photos and store links.
- A clean, friendly interface, with every screen designed in Paper first.
- Privacy from the start: photos and face data are never stored, and one tap deletes your data.

## What we learned

- A small model can be very good at one job if you define exactly what "good" means. Most of our time went into the reward function and the data, not the model itself.
- Give the model only the part of the job that needs judgment. Let code do the math.
- Trust is a feature. An agent that spends money needs hard limits, clear explanations when it says no, and an honest line between what's real and what's simulated.
- A shared API contract let two people build at once: Jasmine designed and built the app against sample data matching the real backend exactly, while Charlie trained the model and built the outfit backend.

## What's next for ClosetCue

- **Real checkout** through stores that support the Agentic Commerce Protocol, paying with a token limited to one store, one amount and one expiry, the same limits as our spending limit.
- **On-device face matching,** so photos with other people in them never leave your phone.
- **Outfits mostly from clothes you own,** so you only buy the one missing piece.
- **Fit feedback after delivery,** and continued training on real user ratings (already saved from the app's A/B screen) so the stylist keeps learning what people like.

## Run it locally

The app has two parts that run at the same time: the Expo app (`src/`) and the FastAPI backend (`backend/`). The pose and face models run inside the backend, and the trained stylist model runs on Veri, so there's nothing else to start.

**Prerequisites:** Node.js and npm; Python 3.12 or 3.13 (if the backend fails with `No module named '_lzma'`, use a Python from python.org, Homebrew or `uv`); Expo Go for SDK 57 on a phone, or Xcode's iOS Simulator on a Mac.

### 1. Install

```sh
npm install

# A Python environment outside the repo, so the bundler doesn't scan it
python3 -m venv ~/.venvs/as-if
source ~/.venvs/as-if/bin/activate
pip install -r backend/requirements.txt
pip install facenet-pytorch --no-deps   # its pinned versions conflict with ours, so it installs separately
```

### 2. Set the environment variables

```sh
cp .env.example .env                  # the app's settings; Expo builds every EXPO_PUBLIC_ value into the app
cp backend/.env.example backend/.env  # the backend's secret keys (Gemini, Veri, Supabase, Stripe test key); never commit it
```

- Set `EXPO_PUBLIC_API_BASE_URL` in `.env` to `http://localhost:8000` for the simulator, or your laptop's local IP (`ipconfig getifaddr en0` on a Mac) for a phone on the same Wi-Fi.
- Set `EXPO_PUBLIC_USE_MOCKS=false` to use the real backend; otherwise the app answers from built-in sample data.
- Leave `STRIPE_*` empty and checkout runs in its simulated mode; with them set, run `python -m backend.stripe_setup` once.

### 3. Run

From the repo root, in two terminals:

```sh
# Terminal 1: backend (the first start downloads the pose and face model weights)
source ~/.venvs/as-if/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000   # curl localhost:8000/health returns {"ok":true}

# Terminal 2: app (scan the QR code with Expo Go, or press i for the iOS Simulator)
npx expo start
```

- If the phone can't reach the laptop (venue Wi-Fi often blocks this), `npx expo start --tunnel` exposes the app's bundler; give the backend its own tunnel and put that URL in `EXPO_PUBLIC_API_BASE_URL`.
- Veri deployments scale to zero when idle. `veri deployments wake <id>` starts one; a cold start takes about 12 minutes, and until then `/outfits` falls back to Gemini.

### Checks

```sh
npm run lint
npx tsc --noEmit
python3 -m pytest -q training/ backend/test_profile.py backend/test_outfits.py backend/test_rate.py
```

## Retrain and re-evaluate the model

Everything for the stylist model lives in `training/`. [PLAN.md](PLAN.md) section 5 explains the design. Run these from the repo root:

```sh
# Rebuild the training data (no AI, about 1 s)
python -m training.gen_profiles --n 400 && python -m training.build_prompts && python -m training.gen_sft

# Train on Veri (configs for every run are in training/configs/)
veri datasets upload training/data/sft_train.jsonl --name outfit-sft   # then put the dataset id in the config's [dataset] table
veri jobs create training/configs/v2-sft.toml --follow

# Evaluate on 20 held-out prompts: gemini, our-llama or base-llama
python -m training.eval --model our-llama --data training/data/prompts_eval.jsonl --limit 20 --out training/results/<name>

# Re-pull the catalog (one request every 3.5 s), then re-tag it with Gemini
python -m training.scrape_catalog && python -m training.tag_catalog
```

## License

MIT. See [LICENSE](LICENSE).
