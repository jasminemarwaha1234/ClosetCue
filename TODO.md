# TODO: model and backend

Status as of Sun Oct 18, 10:00 AM PDT. Feature freeze 11:00, submit by 11:30, judging around 12:20. The full run history, with Veri job ids and costs, is in [training/JOURNAL.md](training/JOURNAL.md). Eval outputs are in [training/results/](training/results/).

## Decided

- **Ship v2-sft as the trained model, with Gemini as the fallback.** `/outfits` tries our Llama first, retries once, then falls back to Gemini. The trained model is in the demo and answers in about 5 s, against Gemini's 27 s.
- **GRPO is a "next time" item.** v2-grpo was worse than v2-sft on every metric (table below).

## Action items

### Before the 11:00 freeze

- [ ] **Decide on "make it nicer".** Charlie wants to remove it for simplicity. Catch: the PLAN.md section 8 demo uses it to push the cart past the $200 limit so checkout refuses it. Options:
  - Remove it: backend `upgrade_of` in `backend/schemas.py` and `backend/routes/outfits.py`; app `upgrade_of` in `src/api/types.ts`, `makeItNicer` in `src/api/client.ts` and its button in `src/app/outfits.tsx`. Then show the over-limit refusal another way.
  - Or keep it and fix its bug: an upgrade can come back identical to the original outfit ($141.00 → $141.00), because upgrades skip the budget check and nothing requires a higher total. Fix: drop upgrade outfits that don't cost more than the current one.
- [ ] **Decide on a "try again with Gemini" button** for when the user doesn't like a Llama outfit.
  - Backend: an optional `prefer: "gemini"` field in `OutfitsRequest` (`schemas.py` and `types.ts` together) that skips Llama. About 15 min.
  - App (Jasmine): the button, plus a loading state for the ~27 s wait.
  - Bonus: every press is a "Llama lost" preference pair for future DPO training.
- [ ] **Jasmine: set `OUR_LLAMA_*` in her `backend/.env`** if the demo backend runs on her laptop. Charlie sends the values privately. `OUR_LLAMA_API_KEY` is Charlie's whole Veri account key: anyone holding it can spend the credits. Rotate it after the event, or use a limited key if Veri offers one.
  - `OUR_LLAMA_URL=https://api.veri.studio/v1/deployments/1d83a13cc7ec`, with no `/chat/completions` at the end.
  - `OUR_LLAMA_NAME=CharlieBrown364/outfit-llama-v2-sft`
  - Leave `BASE_LLAMA_*` empty. Untrained Llama is a poor fallback (25% valid JSON).
- [ ] **App: the loading state must cover up to ~60 s.** The Gemini fallback takes ~27 s, and occasionally times out at 60 s.
- [ ] **Push.** At 10:00, `main` was 1 commit ahead of GitHub (plus this file, uncommitted).
- [ ] **Merge or delete `feature/test-v2-app`.** It's a test worktree at `../LaHacksAI-app-test`, with no unique commits; it was fast-forwarded to `main`. Remove it with `git worktree remove ../LaHacksAI-app-test`, then `git branch -d feature/test-v2-app`.

### Before submitting (11:30)

- [ ] Devpost write-up with the eval table below and the "next time" list.
- [ ] Repo public with no secrets: check `git log -p` for keys. `.env` files are git-ignored.
- [ ] Model links: https://huggingface.co/CharlieBrown364/outfit-llama-v2-sft (shipped) and https://huggingface.co/CharlieBrown364/outfit-llama-v2-grpo (the GRPO attempt).
- [ ] README: how to rerun training and eval (commands below).

### Judging (~12:20)

- [ ] **Wake the v2-sft deployment about 15 min before the demo:** `veri deployments wake 1d83a13cc7ec`. A cold start takes ~12 min, and until it's serving `/outfits` falls back to Gemini.
- [ ] Check Gemini's free-tier quota still has calls left for the fallback and `/profile`.
- [ ] After judging: `veri deployments list` and stop everything (`veri deployments stop <id>`). Veri balance was ~$15.

## Results

The same 20 held-out eval prompts were used for v2-sft and v2-grpo. Gemini and v1 ran on slightly different prompt sets and scoring, so treat those columns as approximate.

| Metric | Gemini | Base Llama | v1-sft | **v2-sft (shipped)** | v2-grpo | Bar |
| --- | --- | --- | --- | --- | --- | --- |
| Valid JSON, nothing invented | 100% | 25% | 90% | **100%** | 100% | 90% |
| Within budget | 100% | 53% | 57% | **72%** | 60% | |
| Answers with 2+ outfits kept by the live check | 100% | 10% | 50% | **65%** | 45% | 80% |
| Reward as % of best possible | 94.6% | 17.8% | 72.8% | **64.7%** | 53.4% | 85% |
| Median latency | 27 s | 5.2 s | 4.9 s | **4.6 s** | 4.9 s | |

**Live `/outfits` test.** The test ran 3 held-out profiles and 14 requests, with no anchor, a catalog anchor, a closet anchor, athletic and "make it nicer". v2-sft answered all 14 itself in 2–7.5 s, with every outfit in budget and complete. The retry and the over-budget repair cover the cases the 65% misses. Output: [training/results/live/](training/results/live/).

## What changed today (all committed)

- **Training data:** 400 synthetic profiles. 600 train and 200 eval prompts, split by profile. SFT answers come from a best-outfit search plus templated reasons; there are no Gemini answers. `training/data/` is git-ignored and rebuilds byte-for-byte in about 1 s with `python -m training.gen_profiles --n 400 && python -m training.build_prompts && python -m training.gen_sft`.
- **The model no longer writes `total`:** a 3B model can't add, so the code computes it.
- **Budget is pass/fail in the reward.** Near-ties break toward fewer pieces and a lower price.
- **Athletic rule:** tops, bottoms, dresses and shoes must be tagged `sporty` or `athleisure`. Their names can't contain jeans, denim, loafer, boot, slipper, sandal and similar. The rule is applied in retrieval, in anchor choice and in the reward.
- **Constrained decoding:** Veri's vLLM `response_format` JSON schema means the model can only use the offered item ids. Invented items went to 0, with no speed cost.
- **Over-budget repair:** `/outfits` swaps the priciest non-anchor piece for a cheaper same-slot item before dropping an outfit.
- **Reasons are written by code** from the returned outfit, using the training templates, so they always name the outfit's own items. Gemini's reasons are kept unless the repair changed its outfit.
- **Catalog:** 29 non-clothing items were removed (shoe care, books, pencils, yoga gear, a toy wand, loose charms); 1,011 items are left. The scraper's denylist keeps them out on a re-tag.
- **Work uses exactly formality 3–4.** Semi-formal and formal keep one level of slack, because the catalog has almost no formality 4–5 tops or women's bottoms.
- `/catalog`, `/outfits`, `/profile`, `training/eval.py`, `training/build_grpo.py` and the Veri configs in `training/configs/` are all built.

## Known gaps

- **Catalog tags are loose:** athleisure covers loafers and boots. Workout outfits can still get the "Faherty x REEF Original Convertible" sandal or a maxi dress. Adding "maxi", "slip on" and "convertible" to the athletic exclusions was considered and set aside.
- **Little variety:** the 3 outfits often share 2 of their pieces.
- **Synthetic closet items get the profile's style tags whatever the garment.** For example, black jeans were tagged "techwear".
- **Formal and semi-formal:** few catalog items at formality 4–5. About 38 of 170 men's profiles can't get a complete work outfit under budgets below $280.
- `/outfits` doesn't drop outfits outside an occasion's formality range. That's only possible through the slack or a user-chosen anchor.
- New `/profile` users start with an empty avoid list, while training profiles have one.
- `POST /profile` has no call in `src/api/client.ts` yet.

## Next time (for the write-up)

1. **Better GRPO.** Trim rows so all 311 prompts upload (each row stores the candidate list twice; the 5.5 MB file hit Veri's upload limit). Run ~200 steps at lr 5e-6, with 4–8 rollouts. This run had only 50 prompts, a noisy reward trend, and unconstrained rollouts while the eval was constrained.
2. **Better reasons:** have Gemini rewrite the template reasons in the SFT data so the model learns a natural voice.
3. **Sharper reward checks:** "season" and "reason" score 0.5 for almost everything, so they don't separate good outfits from bad ones.
4. **DPO from real users:** `/rate` choices and "try again with Gemini" presses become preference pairs.
5. **Retag the catalog** with an explicit "workout-ready" field instead of relying on the name exclusions.
6. **Choose the candidate count from data:** run the eval at 25, 50 and 100 candidates.

## Commands

```sh
# Rebuild the training data (no AI, ~1 s)
python -m training.gen_profiles --n 400 && python -m training.build_prompts && python -m training.gen_sft

# Eval a model on 20 held-out prompts (gemini, or our-llama / base-llama with *_URL set)
python -m training.eval --model our-llama --data training/data/prompts_eval.jsonl --limit 20 --out training/results/<name>

# Backend (repo root, venv from the README)
source ~/.venvs/as-if/bin/activate && uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
