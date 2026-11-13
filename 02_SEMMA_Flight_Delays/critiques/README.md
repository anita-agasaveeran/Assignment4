# Critic Review Log

Each SEMMA stage is drafted in the notebook and in `reports/`, then reviewed by a **separate Claude critic** (an independent subagent with read-only access, able to re-run the numbers) using the persona in [`critic_prompt.md`](critic_prompt.md). The critic scores the stage out of 10 and tags issues **major** or **minor**; I revise and record what changed. Every stage gets **at least 2 rounds** and passes only when a round reports **no major issues**. Rounds are saved as `<stage>_round<R>.md` using [`_template.md`](_template.md).

| Stage | Rounds | Final score | Status |
|---|---|---|---|
| Front pass (framing, data checks, partition) | 2 | 8/10, no major issues | ✅ passed |
| Sample · Explore · Modify | 3 (`sample_explore_modify_round1.md`, `..._model_round2.md`, `..._model_round3.md`) | 8.5/10, no major issues | ✅ passed |
| Model | 2 (rounds 2–3 above) | 8.5/10, no major issues | ✅ passed |
| Assess · Score | – (single sealed run, reported as is) | – | done |
