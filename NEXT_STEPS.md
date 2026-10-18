# Next steps: model and backend (Charlie's side)

Handoff written Sun Oct 18, 01:30 PDT, so a fresh session can continue. Read this, then [PLAN.md](PLAN.md) sections 4–7 and [CHANGES_FOR_CHARLIE.md](CHANGES_FOR_CHARLIE.md). Hacking ends **Sun 12:00 PM PDT**; feature freeze **8:30 AM**; submit by 11:30.

Rules for whoever picks this up:

- Commit as needed. **Never push without Charlie's approval.** Another agent may be editing the repo at the same time: re-read files before editing, and stage only your own files.
- Price every Veri run with `veri jobs estimate` and get Charlie's OK before anything that spends credits. Never leave a deployment warm (`--min-replicas 0`, short `scale_to_zero_window`).
- Log every Veri run in [training/JOURNAL.md](training/JOURNAL.md), failed ones too.

## Where things stand

### Done and committed (local only: not pushed yet; `git log origin/main..HEAD` lists them)

| What | Where | Notes |
| --- | --- | --- |
| Shared vocabularies | `training/vocab.py` | 23 colors (the app's swatch names plus `gold`, `silver`), neutrals, 8 clashing pairs, 17 style tags, occasion formality ranges |
| Outfit contract | `backend/schemas.py`, `src/api/types.ts` | Typed catalog/closet anchors, `closet_<n>` ids, budget checks, 1–3 outfits, `upgrade_of` for "make it nicer" |
| Retrieval | `training/retrieval.py`, `test_retrieval.py` (16 pass) | `retrieve(...)` and `format_candidates(items)` for the prompt. Deterministic |
| Reward | `training/reward.py`, `test_reward.py` (19 pass) | `reward()` for Veri, plus `parse_output`, `score_outfit`, `score_completion`, `prepare_context` for the backend guard. Stdlib only. Max score 6.5 |
| Catalog scraper | `training/scrape_catalog.py`, `training/stores.json` | One request at a time, ≥3.5 s apart (parallel requests got the IP blocked across all of Shopify). `--cache DIR` reuses fetched feeds |
| Raw catalog | `training/catalog_raw.json` | **930 items, 21 US-dollar stores**, pulled 2026-10-18. Untagged: no department/colors/formality/style_tags/season yet |
| Veri pipeline check | JOURNAL entry | Llama trains, merged weights push to HF. See "Veri facts" |

Run the tests: `python3 -m pytest -q training/`.

### Catalog details

- Stores: Stüssy, Brain Dead, Kith, Taylor Stitch, Todd Snyder, Big Bud Press, Faherty, Rowing Blazers, Outerknown, Alo Yoga, Set Active, Outdoor Voices, Christy Dawn, Edikted, Allbirds (cap 30), Thursday Boot Co. (30), Birdies (30), Steve Madden (40), Koio (30), Gorjana (20), Princess Polly. Others: 50 each.
- Bonobos is in `stores.json` but skipped: its feed returns HTTP 500 partway through. Retry once later or delete the line.
- Decisions already made: US-dollar stores only, English names only (no Rouje), **no Brixton** (its terms ban AI training by name). Scraping stores whose terms technically forbid it is accepted.
- Slots: top 191, bottom 172, accessory 178, shoes 146, outerwear 135, dress 108. Department hints: women 411, men 263, unisex 97, unknown 159. Median price $110.
- Add a store: append one line to `stores.json` (`max_items` caps it), rerun `python -m training.scrape_catalog --cache <dir>`. Ids follow store order, so appending never renumbers earlier items.

### Veri facts (learned the hard way)

- Account: charlieweinberger05@gmail.com, balance **$19.65**. L4 is $1.05/GPU-hour. HF account connected: **CharlieBrown364**.
- Base model: **`unsloth/Llama-3.2-3B-Instruct`** (ungated mirror). Confirmed it trains. No Qwen fallback needed.
- In a training TOML the Hugging Face table is **`[huggingface]`** (`repo`, `artifact = "merged"`, `private = false`). `.claude/skills/veri/SKILL.md` wrongly says `[hf_push]`; the CLI silently ignores it and pushes nothing.
- `veri jobs estimate` validates nothing (same price for a nonexistent model). Only a real run proves a config.
- This config ran and pushed (job 633352df677e). Chat data rows are `{"messages": [...]}`; run `veri datasets check` before uploading.

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
  max_seq_length = 1024
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
- Throwaway repo `CharlieBrown364/llama-smoke-test` can be deleted.

## Decide now (blocks work)

1. **Gemini is available again** (Charlie has a key). Put it in `backend/.env` as `GEMINI_API_KEY=` (copy `backend/.env.example`; the file doesn't exist yet; never paste keys into chat). Then decide what Gemini does:
   - Recommended: Gemini tags the catalog (it can read the product photo) and writes profile summaries and SFT reasons; code generates profiles and the SFT outfits (see step 5).
   - Check the key's rate limits first: 930 tagging calls plus ~300 SFT calls on a free tier may be throttled. Batch several items per call.
   - The OpenAI switch is off unless Charlie says otherwise.
2. **Track:** stay on Model Learning or switch to Applied Intelligence. The plan's 10 PM deadline passed with only smoke runs done.
3. **Push** the local commits so Jasmine gets the catalog, reward, retrieval and contract.

## Review (defaults are already in code; change if you disagree)

4. **Reward rules** (`training/reward.py`):
   1. The 3 outfit scores are averaged; missing or duplicate outfits score 0.
   2. An invented item zeroes only that outfit.
   3. No anchor: the anchor point is free.
   4. Bad outfits still earn about 2 of 6.5.
   5. JSON in code fences scores 0 (training must store answers without fences; the live guard may strip them).
   6. Complete = top + bottom or a dress, exactly one pair of shoes, at most one outerwear.
   7. Budget is pass or fail; stated total within $0.01 of the real one.
   8. Color: a clash or 3+ accents = 0; 2 accents = 0.5; 0–1 = 1.
   9. Formality is pass or fail across all items, anchor included.
   10. Anything on the avoid list = 0; else the share of items sharing a style tag with the profile.
   11. The reason must name an item (id, or a 4+ letter word from its name that isn't a color or tag).
   12. The reason is one sentence, at most 40 words.
   13. The live guard also drops outfits with `anchor == 0` or `budget == 0`, except `upgrade_of` requests.
   - Known gap: nothing stops "always pick the cheapest items". Add a budget-use bonus only if GRPO finds that trick.
5. **Retrieval rules** (`training/retrieval.py`):
   1. A dress anchor removes tops and bottoms, and vice versa.
   2. Empty `departments` means shop everything.
   3. No `budget_min` filter.
   4. The diversity cap is never relaxed.
   5. Slot split: top 25%, bottom 25%, shoes 20%, outerwear 12%, dress 10%, accessory 8%.
   6. The formality filter applies to accessories too.
6. **Vocabulary** (`training/vocab.py`): the 17 style tags and 8 clash pairs. Changing them later means re-tagging.

## Ask Jasmine

7. Add `gold` and `silver` to `swatches` in `src/theme/index.ts`.
8. Try-on: with Gemini back, `/tryon` can use Gemini image editing as planned.
9. `GeneratedBy` keeps `"gemini"` now that Gemini is back. The kebab-case spelling (`our-llama`) stays unless she wants it changed.

## The pipeline, in order

Owner in brackets. Critical path: 1 → 2 → 4 → 5 → 7 → 8.

1. **[agent] Tag the catalog: `training/tag_catalog.py`** → `training/catalog.json`.
   - Gemini (fast model) fills `department`, `colors`, `formality` (1–5), `style_tags`, `season` from name, product_type, tags, description and image, choosing **only** from `training/vocab.py`. Validate every answer against the vocab and retry or drop bad ones.
   - Use `department_hint` when set. Drop scraper-only fields (`product_type`, `tags`, `description`, `department_hint`) from `catalog.json` so it matches `CatalogItem`.
   - Start with 20 items, read them, then all 930.
   - Fallback if Gemini fails: rules from Shopify data (color option names and tags, product type → formality).
2. **[Charlie] Spot-check about 30 random tagged items.** Record the pull date.
3. **[agent] Tell Jasmine the final color and tag lists** (they're `vocab.py`).
4. **[agent] Profiles and prompts: `gen_profiles.py`, `build_prompts.py`** → `training/data/`.
   - Profiles from code with a fixed seed: style tags, colors, avoid list, departments, budgets (min $0–$150, max $60–$400), occasions, about 25 closet items each. **No `formality` field** (removed from `StyleProfile`). Gemini may write the one-line `summary`.
   - Prompts: anchor mix 45% catalog / 35% closet / 20% none; candidate sizes 25/50/75/100; candidates from `retrieval.retrieve`, rendered with `retrieval.format_candidates`; output instructions per PLAN section 5 "Task" (ask for exactly 3 outfits, strict JSON, no fences).
   - Every row carries the reward's columns: `occasion`, `budget_min`, `budget_max`, `anchor`, `candidates` (with `name`; closet items price 0), `profile_style_tags`, `profile_avoid`. See `reward.CONTEXT_COLUMNS`.
   - 20 profiles / 40 prompts first; `veri datasets check`; read 10 rows. Then 400 profiles, split 300 train / 100 eval **by profile**, and check no eval profile is in training.
5. **[agent] SFT answers: `gen_sft.py`.**
   - Option A (recommended): a solver searches each prompt's candidates for the 3 highest-reward distinct outfits; Gemini (or base Llama) writes each one-sentence reason; keep only answers that score near the max with `reward.score_completion`.
   - Option B (the original plan): Gemini answers the prompts; keep only high scorers.
   - Store answers as plain JSON, no fences. One prompt format per JSONL file.
6. **[agent + Charlie's OK] v0 baseline.** Deploy base Llama on Veri (L4, `--min-replicas 0`), write `training/eval.py`, run the 100 eval prompts: valid JSON, invented items, complete outfit, within budget, mean reward, latency. Also the candidate-size check (20 prompts each at 25/50/75/100/150/200). Stop the deployment after.
7. **[agent + Charlie's OK] v1-sft** on Veri: LoRA, merged push to `CharlieBrown364/<name>` via `[huggingface]`. About $1–2. 5-step smoke first if the config changed.
8. **[agent + Charlie's OK] v1-grpo** from the SFT checkpoint with `reward.py`. `max_steps` about 100, 4–8 rollouts. About $2–4. Watch the mean reward climb with `veri jobs logs <id> -f`.
9. **[Charlie + agent] Read outputs after each run:** 20 random and the 10 highest-reward answers. Look for reward hacking; fix the reward, journal it, rerun.
10. **[agent] Eval table** (PLAN section 6): v0, v1-sft, v1-grpo, Gemini reference. Plus accuracy by candidate size for the winner. Pick the live candidate size (start at 50). If GRPO doesn't beat SFT, ship SFT and say so.
11. **[agent] Backend endpoints**, written while training runs (one file each in `backend/routes/`, plus `services/veri.py`, `services/gemini.py`, `services/supabase.py`):
    - `GET /catalog` from `catalog.json`.
    - `POST /outfits`: load profile, resolve anchor (422 if unknown), `retrieve`, prompt, call Veri, guard with `reward.score_outfit` (drop gate failures and `anchor`/`budget` zeros, recompute totals from catalog prices), retry once if fewer than 2 survive, then fall back to base Llama, then Gemini, setting `generated_by`; 503 if all fail. Compute `swaps` (up to 3 same-slot items keeping the total in range). `upgrade_of`: budget range becomes (outfit total, total + $150], return one outfit, no `budget_max` cap.
    - `POST /profile`, `GET`/`PUT /profile`: Gemini tags photos into a `StyleProfile` and closet; Supabase storage.
    - `GET /rate/next`, `POST /rate`: blind A/B pairs (v0 vs ours on held-out prompts); store choices as DPO pairs.
    - Supabase: anonymous sign-in, `profiles` and `feedback` tables.
    - Checkpoint: `/outfits` against v0 first, then against the trained model.
12. **[agent + Charlie's OK] Deploy the winner** (`veri deploy CharlieBrown364/<name> --gpu-type L4-24GB --no-cache --min-replicas 0`) and point `/outfits` at it. By about 6 AM.
13. **[stretch] v2-dpo** from A/B answers collected at the event.
14. **[Charlie] Sunday morning:** condense the journal into the five-step story (PLAN section 7), Devpost write-up with the eval table, README (setup, how to rerun training and eval).
15. **[Charlie] Before submitting:** repo public with no secrets (`git log -p` check), model link on HF, Paper link.
16. **[Charlie] 12:20 PM:** `veri deployments wake <id>` before judging. After judging: `veri deployments list` and stop everything.

## Optional cleanup

- Delete the HF repo `CharlieBrown364/llama-smoke-test`.
- Fix `.claude/skills/veri/SKILL.md` (`[hf_push]` → `[huggingface]` in the TOML example) if the skill is ours to edit.
