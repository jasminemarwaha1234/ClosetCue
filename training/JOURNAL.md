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
