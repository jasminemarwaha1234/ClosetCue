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
