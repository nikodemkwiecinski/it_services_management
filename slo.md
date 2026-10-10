---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 30d
  slis:
    availability:
      objective: 0.99
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code!~"5.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
    latency:
      objective: 0.995
      threshold_seconds: 0.25
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.25"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.005, minutes: 216}
  alerts:
    - {alert: KbSearchErrorsBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchErrorsBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
---
<!-- ai-generated: 80% - Claude Code drafted the numbers and the prose from my two measurements, I reviewed and own them -->

# SLO for `GET /kb/search`

The numbers below come from two runs of `.\itsmlab.ps1 load 3` for login `nikodemkwiecinski` on 10 October 2026,
each 60 s open-loop at 40 requests per second (about 2,400 searches):

| run | p50 | p95 | p99 (q) | p99.9 | 502s |
|---|---|---|---|---|---|
| 1 | 29.6 ms | 70.3 ms | 149.0 ms | 196.7 ms | 7 of 2,399 (0.29 %) |
| 2 | 30.6 ms | 67.5 ms | 153.5 ms | 184.2 ms | 10 of 2,399 (0.42 %) |

The shape: almost every search takes 15 to 70 ms, and a slow mode between about 110 and 220 ms holds roughly 3 % of
them. The p99 lands inside that slow mode, and nothing in either run took longer than about 220 ms. The window is
30 days, a month of service as the desk's users would remember it.

## Availability

A search is good when `svcdesk` answers it with anything but a 5xx; every `/kb/search` request counts as valid. In
practice the only 5xx is the 502 `upstream_unavailable`, which `svcdesk` gives exactly when `kb-index` fails, so the
SLI measures `kb-index`'s failures as the user sees them. A 422 for an empty or overlong `q` is the user's own
mistake and stays good.

Objective **0.99**: an error budget of 1 %, 432 minutes of a 30-day window. `kb-index` fails on its own between
0.29 % and 0.42 % of searches in my measurements, which I cannot fix from `svcdesk` (no retry, M-02). That spends 30
to 40 % of the budget on a normal month and leaves the rest for real incidents. 0.995 would put the normal month at
60 to 85 % of its budget, and one bad hour would breach it, so a Lab 6 canary gate would roll back honest releases
for the index's sake. 0.999 is below what the dependency itself delivers.

## Latency

A search is good when it is answered in at most **0.25 s**, counted from the bucket `le="0.25"` of the histogram;
valid is every `/kb/search` request. 0.25 is one of the ladder's boundaries (M-13), so the SLI counts requests
instead of interpolating them.

The threshold sits just above the slow mode: the slow searches at 110 to 220 ms are how `kb-index` normally
behaves and a user waits for them without noticing much, while a search above 250 ms means something beyond the
index's normal slow mode - the service queueing, the host overloaded, or the index degraded. A threshold inside
the slow mode (say 0.15 s) would count 1 to 2 % of normal traffic as bad and make the SLI follow the index's random
draws rather than real trouble.

Objective **0.995**: a budget of 0.5 %, 216 minutes. In both runs no search went above 0.25 s, so the objective
holds with a wide margin on my machine, and still holds on a slower one: even if the grader's or the Lab 6 canary's
host is 30 % slower, the slow mode's tail (about 220 ms x 1.3 = 286 ms) moves only the last ~0.1 % of searches
over the threshold. 0.999 would leave no room for that. The threshold is well under Lab 6's 1 s cap.

## Alerts

| alert | SLI | burn rate | long / short window | budget spent when it fires | severity: page or chat |
|---|---|---|---|---|---|
| KbSearchErrorsBurnFast | availability | 14.4 | 1h / 5m | 2 % (14.4 x 1h / 720h) | P1, page |
| KbSearchErrorsBurnSlow | availability | 6 | 6h / 30m | 5 % (6 x 6h / 720h) | P2, chat |

At 14.4x more than 14 % of searches fail, the whole month's budget is gone in about two days, and the users who
search for workarounds during an outage get none - so it pages a person, at night too: the cost of being woken is
paid against losing the month's budget before morning, and the fix (restarting the index, failing over) is
something a person must do now. At 6x about 6 % of searches fail; the budget lasts five days, so a message in the
team's chat that someone reads in working hours is enough, and waking a person for it would cost more than the
few hours of degraded searching. `kb-index`'s normal failure rate is a burn of 0.3 to 0.4, far below both, so
neither fires on a normal day. Each alert has a short window of a twelfth of its long one, so it stops within
minutes of the index recovering instead of half an hour later; `for: 2m` keeps a single bad scrape from paging.

There is no latency alert: no search crossed 0.25 s in either measurement, and the error alerts already cover the
index failing outright. A latency burn alert would be the next one to add once the service runs under real load.

## Buckets

The ladder has 29 boundaries, in seconds: `0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.11, 0.12, 0.13,
0.135, 0.14, 0.145, 0.15, 0.155, 0.16, 0.165, 0.17, 0.18, 0.19, 0.2, 0.25, 0.3, 0.5, 1.0, 2.0, 2.5, 5.0`.

My q was 149.0 and 153.5 ms. 153.5 ms falls in (0.15, 0.155]: 5 ms wide, 3.3 % of q, and the service's own
histogram gave a p99 of 153.6 ms over the same run. Fifteen boundaries go to 0.1 to 0.2 s, in 5 ms steps from 0.13
to 0.17 and 10 ms steps around them, so every q from 0.1 s to 0.2 s is resolved - the widest bucket there is
(0.1, 0.11], 10 % of a q of 0.1. That is a band of -35 % / +30 % around my q, much wider than the few per cent by
which two runs, or the grader's run, differ; it also covers the whole slow mode, so the dashboard's p99 stays
honest if the slow mode drifts. Below 0.1 s seven boundaries describe the bulk of the searches (p50, p95) well
enough for a dashboard; above 0.2 s, 0.25 is the latency threshold, and 0.3, 0.5, 1, 2, 2.5 and 5 s cover
degradations up to the 5 s upstream timeout.
