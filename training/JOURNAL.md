# Training journal

One entry for every decision and every run, written when it happens, failed runs included (PLAN.md section 7). Every run records its Veri job ID, the git commit of `reward.py` and the data, the cost, and the result.

Entry template:

```markdown
### 2026-10-17 21:40, v1-grpo run 2
- Changed: color-harmony weight 0.5 → 1.0; added the 60–100% budget bonus
- Why: run 1's top answers all spent ~30% of budget (cheapest-item hack)
- Data: prompts v2 (300 train / 100 eval), reward.py @ <git commit>
- Veri job: <job id>, L4 x1, 41 min, $0.72
- Result: mean reward 2.9 → 4.1; within-budget 97%; read 20 samples, cheap-item hack gone
```

### 2026-10-18 00:30, smoke runs 1 and 2 (pipeline check, not a model)
- Changed: nothing yet; first runs on Veri.
- Why: confirm Veri trains `unsloth/Llama-3.2-3B-Instruct` (ungated mirror) and can push merged LoRA weights to Hugging Face before real data exists.
- Data: 20 synthetic outfit-format chat rows (Veri dataset 232689ace2c0), not real training data.
- Veri jobs: 34ba5d1ea926 and 633352df677e, `sft_text`, LoRA rank 16, 5 steps, L4 x1, ~6 min each; $0.35 for both.
- Result: the model loads and trains (5 steps in 44 s). Run 1 pushed nothing: the TOML table is `[huggingface]`, not `[hf_push]`, and the CLI ignores unknown tables silently. Run 2 with `[huggingface]`, `artifact = "merged"`, `private = false` pushed full merged weights to https://huggingface.co/CharlieBrown364/llama-smoke-test. `veri jobs estimate` validates nothing (same price for a nonexistent model), so only a real run proves a config. Decision: stay on Llama 3.2 3B; no Qwen fallback needed.

### 2026-10-18 06:25, v1-sft smoke (5 steps)
- Changed: first run on real data. Correction to the entry above: `veri jobs list` reports the two earlier smoke runs at $0.38 and $0.35 ($0.73 total, not $0.35).
- Why: prove the SFT data loads and a 2,612-token row fits on one L4 before the full v1-sft run.
- Data: `training/data/sft_train.jsonl` from `gen_sft.py` @ 8f70014 (251 rows: 25- and 50-candidate train prompts only; solver answers + templated reasons, every row at 100% of its best possible reward). Veri dataset e6447f2e5a33.
- Veri job: 23ac2f782f62, `training/configs/v1-sft-smoke.toml` (sft_text, LoRA 16/32, lr 1e-4, max_seq_length 3072, 5 steps), L4 x1. ~6 min wall clock (about 5 min setup and model download), cost not yet reported by Veri (estimate $0.09).
- Result: completed. 5 steps in 47 s: the first step took 35 s (warm-up), then about 3 s per step at batch size 1. Loss 2.29 → 2.17 (train_loss 2.06). ~2,000 tokens per step, so the loss appears to cover the whole sequence (prompt included), not just the answer. Projection for v1-sft.toml (2 epochs = 502 steps): ~25–30 min of training plus ~5 min setup and the merge and Hugging Face push, so ~40 min, about $0.70.

### 2026-10-18 07:01, v1-sft (full run)
- Changed: nothing from the smoke config except 2 epochs (502 steps) and the [huggingface] push.
- Data: Veri dataset e6447f2e5a33 (251 rows, see the smoke entry).
- Veri job: 93db1eb64b94, `training/configs/v1-sft.toml`, L4 x1. Training 17 min (about 2 s per step), ~23 min wall clock, $0.65.
- Result: completed and pushed to https://huggingface.co/CharlieBrown364/outfit-llama-v1-sft. Loss 2.2 → about 0.2 by the end (train_loss 0.48), mean token accuracy about 95%.

### 2026-10-18 07:45, eval: Gemini vs base Llama (v0) vs v1-sft, same 20 eval rows
- Changed: Gemini rerun on the regenerated prompts (comfy = formality 1–2); v0 and v1-sft deployed on Veri (L4, vLLM, max-model-len 8192, scale to zero).
- Data: first 20 rows of `training/data/prompts_eval.jsonl` (20 different held-out profiles, candidate sizes 25–100).
- Veri deployments: base-llama 19cbd2e67a0f, our-llama 8cf7ae4c5843, both stopped after the evals. My eval wrapper waited for the wrong status name ("running"; Veri says "serving") and both sat idle through one scale-to-zero window, then the first eval attempt sent every request to `<endpoint_url>/chat/completions` twice over (Veri's endpoint_url already ends in /chat/completions; OUR_LLAMA_URL / BASE_LLAMA_URL must be the deployment URL without it). About $0.70 of deployment time was wasted on these two mistakes. Balance after everything: $16.56.
- Result:

  | Metric | Gemini | v0 base Llama | v1-sft |
  | --- | --- | --- | --- |
  | Valid JSON, nothing invented | 100% | 25% | 90% |
  | Answers with 2+ outfits kept by the live guard | 100% | 10% | 50% |
  | Mean reward, % of each row's best | 94.6% | 17.8% | 72.8% |
  | Within budget (real prices) | 100% | 53.3% | 56.7% |
  | Complete outfits | 94.4% | 40% | 86.7% |
  | Median latency | 27 s (2 timeouts at 60 s) | 5.2 s | 4.9 s |

- Reading: SFT took the 3B model from mostly unusable (25% valid JSON) to valid structured outfits 90% of the time, at 5x Gemini's speed. Its two failures: it can't add (the stated total is wrong in 55 of its 57 non-invented outfits, which zeroes the reward's budget point; the live route recomputes totals, so users never see this), and it really does overspend (20 of 57 outfits over budget_max). It also invented an item in 2 answers. Gemini passes every bar except speed; v1-sft fails the 80% and 85% bars.

### 2026-10-18 08:14, v2 model changes and the v2-sft run (submitted)
- Changed (one commit each, eb51e5b..a64ac3b): (1) the model no longer states `total`; the prompt says "each outfit's items must cost between $X and $Y combined", the reward prices outfits from the candidates, and a stray `total` key still parses and is ignored. (2) The budget is a reward gate: an outfit outside [budget_min, budget_max] scores 0 (the budget point stays in the breakdown, so the max is still 7.5); upgrades still skip the budget in the live guard. (3) `best_outfits` treats scores within TIE = 0.05 as equal and takes fewer pieces, then the lower total (every check moves the score by 0.1 or more, except the profile average, where 0.05 is the gap between 3 of 4 and 4 of 5 matching pieces). (4) Athletic rule, `vocab.OCCASION_RULES` mirrored in reward.py: every top, bottom, dress and shoes must carry `sporty` or `athleisure` and its name must contain none of jeans, denim, chino, trouser, skirt, dress shirt, oxford, blazer, loafer, boot, slipper, clog, flip flop, slide, sandal, heel (whole words); outerwear and accessories are exempt. `reward.occasion_allows` applies it in retrieval, the prompt builder's anchors (catalog and closet), and the reward, where a violation zeroes the formality point. (5) /outfits swaps an over-budget outfit's priciest item (never the anchor or an owned item) for the best same-slot alternative that fits, before dropping it.
- Data: regenerated with `gen_profiles --n 400`, `build_prompts`, `gen_sft` (600 train prompts; 261 SFT rows, all at 100% of their best possible; skipped: 289 over 50 candidates, 44 with a top-3 outfit breaking a stated rule, 6 with fewer than 3 outfits). Budget position of the 783 answer outfits, (total - min) / (max - min): p10 0.35, p50 0.75, p90 0.96 (v1: median 0.84). 26 athletic rows, all obeying the rule. Longest row 2,579 Llama 3.2 tokens. Veri dataset ff38c670ba1d (outfit-sft-v2).
- Veri job: e90a9127cc02, `training/configs/v2-sft.toml` (v1-sft's hyperparameters), L4 x1, estimate $1.75 (an upper bound; v1-sft cost $0.65). Pushes to https://huggingface.co/CharlieBrown364/outfit-llama-v2-sft.
- Result: pending.

### 2026-10-18 08:20, grpo-smoke (5 GRPO steps on v1-sft; pipeline check, not a model)
- Changed: first GRPO run. New `training/build_grpo.py` turns build_prompts rows into Veri GRPO rows: `messages` becomes `prompt` (the system + user chat list; Veri's GRPO needs a `prompt` column and accepts a message list), every other column is kept and passed by TRL to `reward()` as a keyword argument, with lists and objects written as JSON strings (reward.py decodes them) so the trainer's Arrow table doesn't have to infer a schema for the candidate dicts.
- Why: prove the GRPO pipeline (dataset format, inline reward, context columns reaching the reward, an HF repo as the base model) and time a step before v2-grpo.
- Data: 30 rows (25- and 50-candidate prompts, first 30 of them) from `prompts_train.jsonl` as of 91ec523, Veri dataset fc2f15a9f4f1. Reward: reward.py as of 91ec523 (still scores `total`, which v1-sft emits), uploaded from a frozen copy.
- Veri job: fbce31cfde27, `training/configs/grpo-smoke.toml` (grpo, base CharlieBrown364/outfit-llama-v1-sft, LoRA 16/32, lr 1e-5, 4 rollouts, max_response_length 384, 5 steps), L4 x1. Wall clock 8.7 min from submit to completed (about 6 min boot, setup and model download); training 138 s. $0.39 (estimate said $0.09; earlier small jobs also billed $0.35 to $0.38, so expect about $0.30 of fixed overhead per job).
- Result: completed, no errors. Step times 51 s (warm-up), then 20, 14, 18, 19 s (plus ~2 s of checkpoint upload per step). The reward got the context columns: rewards vary inside every group (reward_std 0.87 to 2.31, frac_reward_zero_std 0 on all 5 steps; a missing candidates column would have raised and failed the job). Mean reward per step 3.44, 2.86, 5.30, 4.25, 3.73 (out of 7.5), noise at this length. Completions 131 to 184 tokens, none clipped at 384. Projection for `training/configs/v2-grpo.toml` (50 steps, 8 rollouts): at most ~40 s per step if step time doubles with rollouts, so ≤ ~33 min of training, ~45 min wall clock with setup and the merged push, about $1.00 billed.

### 2026-10-18 08:35, constrained decoding test on the v1-sft endpoint
- Changed: nothing in the repo. Tested whether Veri's vLLM endpoint can force item ids from the prompt's candidate list.
- Data: first 3 rows of `prompts_eval.jsonl` (101, 26 and 25 candidates; two with closet anchors). Schema per row: `{"outfits": exactly 3 of {"items": 2-6 strings, enum = that row's candidate ids (the anchor included), "total": number, "reason": string}}`, all keys required, additionalProperties false.
- Veri deployment: 2ccdaf3f4a0f (CharlieBrown364/outfit-llama-v1-sft, L4, max-model-len 8192), ~12.5 min cold start, 32 requests, stopped after. $0.28.
- Result: `response_format: {"type": "json_schema", "json_schema": {"name": "outfits", "schema": ..., "strict": true}}` works and is enforced: with an enum of three fake ids the model output only those ids, and with "total" removed from the schema the output dropped "total" (v1-sft always emits it). `structured_outputs: {"json": schema}` also works (dropped "total" too). Top-level `guided_json` returns 200 but is silently ignored (it invented the same `accessory_134` as the unconstrained call). `response_format: {"type": "json_object"}` gives JSON but doesn't constrain ids (invented `accessory_134` twice).
- Latency (9 calls each, same rows): unconstrained 4.39–5.17 s (mean 4.62), constrained 4.27–5.73 s (mean 4.89), constrained without "total" 3.78–4.38 s (mean 4.11, fewer tokens). The first constrained calls were the slowest by ~0.5 s (grammar compile); no meaningful cost after that.
- Quality (reward.py as of 91ec523, 27 outfits each): unconstrained 1 of 9 answers invented an id (26/27 outfits passed the gate), constrained 27/27. Every other reward part is unchanged (complete 1.0, formality 0.96–1.0, color ~0.95, profile 0.85), so forcing ids costs nothing measurable. Stated totals are still wrong in every outfit and ~19% of outfits are over budget on real prices; the schema can't fix arithmetic. The schema allows a repeated id inside one outfit (seen only in the fake-id test); add a server-side dedupe or `uniqueItems` if it shows up.

### 2026-10-18 08:41, v2-sft (full run)
- Veri job: e90a9127cc02, `training/configs/v2-sft.toml`, 522 steps (2 epochs of 261 rows), training 17.5 min, $0.66. train_loss 0.46. Pushed to https://huggingface.co/CharlieBrown364/outfit-llama-v2-sft.

### 2026-10-18 08:53, v2-sft eval and live /outfits test
- Deployment 1d83a13cc7ec (scaled to zero after use). Eval with constrained decoding (`64b976a`) on the first 20 rows of the regenerated `prompts_eval.jsonl`; results in `training/results/v2-sft/`. Not directly comparable with the 07:45 table: different eval rows, and over-budget outfits now score 0 (budget gate), so mean reward drops for the same behaviour.
- Result: valid JSON with nothing invented 100% (v1 90%); within budget 71.7% (v1 56.7%); complete 95%; live guard (with the over-budget repair) keeps 66.7% of outfits, 65% of answers keep 2+ (v1 50%); mean reward 64.7% of each row's best; median latency 4.6 s.
- Live test (`training/results/live/live_outfits.py`, output in `live/v2-sft.txt`): backend from the `feature/test-v2-app` worktree pointed at v2-sft; 3 held-out profiles, 14 requests (no anchor, catalog anchor, closet anchor, athletic, make it nicer). All 14 answered by our-llama, 2–7.5 s, all in budget and complete; athletic outfits were real workout clothes. Problems found: reasons named items not in the outfit; non-clothing catalog items (Koio Shoe Tree as shoes, cloths); work outfits at formality 2; low variety across the 3 outfits; modest "make it nicer" step. Fixed without retraining in b8231fb (reasons written from the returned items with the SFT templates), b0dce05 (29 non-clothing items removed, denylist in the scraper) and 52f4ed2 (exact formality 3–4 for work only; semi-formal/formal keep the slack because the catalog has almost no formality 4–5 tops or women's bottoms).

### 2026-10-18 09:12, v2-grpo
- Veri job: 6b526a12fd19, `training/configs/v2-grpo.toml`: from v2-sft, 50 GRPO steps, 8 rollouts, LoRA 16/32, lr 1e-5, max_response_length 384, reward = `training/reward.py` with the budget gate, 100-row dataset 68bb74db11b5 (311 rows failed to upload: multipart parse error at 5.5 MB). Training 24 min, $0.78. Pushed to https://huggingface.co/CharlieBrown364/outfit-llama-v2-grpo.
- Result: mean reward per 10 steps 1.75 → 2.70 → 2.61 → 2.26 → 3.15 (noisy, up overall). Training rollouts are unconstrained (no JSON schema), so these are lower than the constrained eval scores. Eval pending.
