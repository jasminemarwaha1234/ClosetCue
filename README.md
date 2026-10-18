# As If

An AI stylist that builds whole outfits around a piece you love, within your budget, and checks out under a spending limit the agent can't go over. Built at LA Hacks 2026. See [PLAN.md](PLAN.md) for the full plan.

## Run it locally

The app has two parts that run at the same time: the Expo app (`src/`) and the FastAPI backend (`backend/`). The pose and face models run inside the backend, and the trained stylist model runs on Veri, so there's nothing else to start.

### Prerequisites

- Node.js and npm.
- Python 3.12 or 3.13. If the backend fails with `No module named '_lzma'`, that Python was built without xz support: use one from python.org, Homebrew or `uv` instead.
- On a phone: the Expo Go app for SDK 57. On a Mac: Xcode's iOS Simulator also works.

### 1. Install

From the repo root:

```sh
npm install

# A Python environment outside the repo, so the bundler doesn't scan it
python3 -m venv ~/.venvs/as-if
source ~/.venvs/as-if/bin/activate
pip install -r backend/requirements.txt
pip install facenet-pytorch --no-deps   # its pinned versions conflict with ours, so it installs separately
```

### 2. Set the environment variables

There are two env files, each copied from its `.env.example`:

| File | Holds | Safe to share? |
| --- | --- | --- |
| `.env` (repo root) | The app's settings. Expo builds every `EXPO_PUBLIC_` value into the app. | Yes, anyone with the app can read them |
| `backend/.env` | The backend's secret keys (Gemini, Veri, Supabase, Sentry, Stripe test key) | No, never commit it |

```sh
cp .env.example .env
cp backend/.env.example backend/.env
```

Then set `EXPO_PUBLIC_API_BASE_URL` in `.env`:

- **Simulator:** `http://localhost:8000` (the default).
- **Real phone on the same Wi-Fi:** your laptop's local IP, such as `http://192.168.1.23:8000`. On a Mac, `ipconfig getifaddr en0` prints it.

### 3. Run

Use two terminals, both started from the repo root.

**Terminal 1, backend:**

```sh
source ~/.venvs/as-if/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

The backend must start from the repo root, because its modules import each other as `backend.…`. `--host 0.0.0.0` lets a phone on the same network reach it. The first start downloads the pose and face model weights. `curl localhost:8000/health` returns `{"ok":true}` once it's up.

**Terminal 2, app:**

```sh
npx expo start
```

Scan the QR code with Expo Go, or press `i` to open the iOS Simulator. After pulling changes to `package.json`, run `npm install` and start with `npx expo start --clear`.

**When the phone can't reach the laptop** (venue Wi-Fi often blocks devices from talking to each other): `npx expo start --tunnel` makes the app's bundler reachable, but not the backend. Give the backend its own tunnel too, and put that URL in `EXPO_PUBLIC_API_BASE_URL`.

### Checks

```sh
npm run lint                                 # ESLint
npx tsc --noEmit                             # TypeScript
python -m backend.test_framing <photo> …     # prints the outfit framing the backend sees in each photo
python -m training.test_retrieval            # retrieval tests
python -m training.test_reward               # reward tests
```

## Training

Everything for the stylist model lives in `training/`; [PLAN.md](PLAN.md) section 5 explains it, and [training/JOURNAL.md](training/JOURNAL.md) records every run. Run these from the repo root:

```sh
python -m training.scrape_catalog            # re-pulls training/catalog_raw.json from training/stores.json (slow on purpose: one request every 3.5 s)
```

Add packages with `npx expo install <package>`, not `npm install`, so they match Expo SDK 57.
