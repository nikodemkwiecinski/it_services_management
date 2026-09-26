---
feature: "DORA metrics engine behind POST /dora/metrics: validation, the five metrics and the six edge cases E1-E6"
predicted_minutes: 60
actual_minutes: 4.33
ratio_actual_over_predicted: 0.07
started_at: "2026-09-26T13:37:26Z"
finished_at: "2026-09-26T13:41:46Z"
---
<!-- ai-generated: 60% - Claude Code drafted the text from the receipt and commit times; I reviewed and edited it -->

# METR n=1 - outcome

**Ratio actual/predicted: 4.33 / 60 = 0.07.**

## How it was measured

The clock started at the prediction receipt (`received_at` 2026-09-26T13:37:26Z, issue 126, bound to `main` at
`6fc8474`). It stopped when the feature was done: `src/svcdesk/dora.py` answered the practice fixture field for
field, and the commit `18d5056` held it together with the two routes. The last check ran at 13:41:46Z. The
interval is 4 minutes 20 seconds, or 4.33 minutes. Git author dates played no part; the times come from the
receipt and the shell clock.

## What happened

The prediction of 60 minutes assumed the course's own budget for this part: 30 minutes for the endpoint and 25
for the six edge-case rules. It also assumed that at least one edge case would need a few rounds of "run,
compare, fix". In fact Claude Code wrote the whole engine in one pass, and the first comparison against
`fixtures/metrics-practice.json` showed zero mismatches, so no correction loop happened at all.

The result is a big speed-up, but it is an n=1 with two obvious confounders:

- Before the clock started, the whole specification had already been read and turned into a written plan.
  That plan named every rule, the rounding trap (half-up rather than Python's banker's rounding) and the
  expected counts. The measured four minutes are the typing and one check, not the understanding.
- The practice fixture is a published target with the answer next to it. Matching it on the first try says the
  rules were applied correctly to this log. It does not guarantee the same for the unseen Tier B log.

The original METR study found experienced developers slower with AI while believing they were faster. My
prediction erred in the opposite direction: I expected the work to take as long as the handout budgets for a
student. The lesson I take is that the prediction should have been made for the task as it would really be
done, with the assistant and after the planning, rather than for the task as the handout describes it.
