# Critic Review Log

The assignment asks for each section to be critiqued and revised over several rounds. Here's how that works for this project:

1. A phase gets drafted in the notebook and in `reports/final_report.md`.
2. A **separate Claude critic** (independent reviewer session with read-only access to the project, able to re-run the numbers) receives the persona prompt in [`critic_prompt.md`](critic_prompt.md).
3. The critic returns a score out of 10 and a list of issues tagged **major** or **minor**.
4. I revise and record what changed.
5. Steps 2–4 repeat. Every phase gets **at least 2 rounds**, and it's only finished once a round reports **no major issues**.

Each round is saved as `phase<N>_<name>_round<R>.md`, using [`_template.md`](_template.md).

**Lessons carried over** from the abandoned bakery dataset (`../../_archive/01_CRISP-DM_Bakery_Waste/critiques/`):
- size the problem against an *achievable* baseline;
- define prediction timing and excluded inputs up front;
- freeze the test design in Phase 1;
- make every criterion measurable.

| Phase | Rounds | Final score | Status |
|---|---|---|---|
| 1 · Business Understanding | 3 (+ DM5 loop-back from Phase 2, 2026-11-04) | 9/10, no major issues | ✅ passed |
| 2 · Data Understanding | 3 | 8.5/10, no major issues | ✅ passed |
| 3 · Data Preparation | 2 (+ revision 3 for round-2 minors) | 8/10, no major issues | ✅ passed |
| 4 · Modeling | 3 (+ revision 4 for round-3 minors) | 8/10, no major issues | ✅ passed |
| 5 · Evaluation | 0 | – | not started |
| 6 · Deployment | 0 | – | not started |
| Medium article | 0 | – | not started |
