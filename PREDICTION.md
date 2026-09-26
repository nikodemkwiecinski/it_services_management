---
feature: "DORA metrics engine behind POST /dora/metrics: validation, the five metrics and the six edge cases E1-E6"
predicted_minutes: 60
predicted_at: "2026-09-26T13:34:47Z"
feature_path: src/svcdesk/dora.py
---
<!-- ai-generated: 30% - Claude Code wrote the file around my own estimate of 60 minutes -->

# Prediction - Lab 2 Stretch 1 (METR n=1)

The feature is the metric computation in `src/svcdesk/dora.py`. It covers:

- parsing and validating the event log (section 1 of `lab2/METRIC-SPEC.md`);
- the window and the arithmetic (R-01..R-05);
- change identity (R-06, R-07);
- the five metrics with the six edge cases (R-08..R-15);
- the ground truth (R-16, R-17).

It is done when `POST /dora/metrics` answers the practice fixture exactly as `fixtures/metrics-practice.json`
does. I estimate 60 minutes of work, starting after this prediction is receipted.
