---
lab2_edge_cases:
  E1: {rule: R-08, count: 3}
  E2: {rule: R-06, count: 2}
  E3: {rule: R-09, count: 4}
  E4: {rule: R-10, count: 4}
  E5: {rule: R-12, count: 1}
  E6: {rule: R-13, count: 11}
---
<!-- ai-generated: 70% - Claude Code drafted the text from the counts my service reports; I reviewed and edited it -->

# Edge cases in the practice event log

The counts above are the ones my service reports for `fixtures/events-practice.jsonl` over the published window
(`metrics.json`).

## E1 - clock skew produces a negative lead time

- What the log contains: three successful production deployments ship a commit that is timestamped after the
  deployment itself. DEP-0012 ships `sha-0040` 834 s "before" it was committed, DEP-0024 ships `sha-0094` 51 s
  early, and DEP-0031 ships `sha-0123` 780 s early. That is impossible in reality: the committing machine's clock
  ran ahead of the deploy pipeline's.
- What a default definition would have done: the usual definition, `deploy time - commit time`, would either
  drop these three pairs as "bad data" or keep them as negative numbers. Dropping them silently removes the
  fastest deliveries from the median. Keeping them negative lets a skewed clock pull the median down, and at
  the extreme it produces a negative lead time on a dashboard, which no reader can interpret.
- Why the rule is defensible: the commit really did reach production in that deployment, so the pair is real
  delivery and must count. Its true lead time is almost zero, so zero is the honest floor. Reporting the three
  clamped pairs as `negative_lead_time_pairs` keeps the clock problem visible instead of hiding it inside the
  median, so someone can go and fix the clocks.

## E2 - a revert of a revert

- What the log contains: `sha-0070` reverts `sha-0069`, which belongs to CHG-0033, and `sha-0071` then reverts
  `sha-0070`. All three ship in DEP-0018. The two revert commits carry no `change_id` of their own.
- What a default definition would have done: counting "one commit = one change", or grouping by `change_id`
  with `null` as its own group, gives three changes (or two plus a bogus null change) where there is one. It
  inflates `changes` and `changes_delivered`, and it measures the reverts' lead time from their own late commit
  instants. That makes CHG-0033 look faster and more numerous than it was, although the work went back and
  forth and ended up where it started.
- Why the rule is defensible: a revert is not new work. It is more history of the change it undoes, so it
  inherits that change's identity transitively. The change is measured from its earliest commit (R-07), which
  is where the work really started. `revert_chains_collapsed` = 2 shows how many commits were folded into
  existing changes.

## E3 - a hotfix that never touched `main`

- What the log contains: four commits reach production from hotfix branches that were never merged to `main`
  first. They are `sha-0019` (`hotfix/2609`, DEP-0006), `sha-0077` (`hotfix/4347`, DEP-0019), `sha-0108`
  (`hotfix/6085`, DEP-0028) and `sha-0127` (`hotfix/1544`, DEP-0033).
- What a default definition would have done: a definition that "measures from commit to main to production"
  filters on `branch == "main"` and loses these pairs. Hotfixes are typically the fastest deliveries (`sha-0019`
  reached production in 77 minutes), so dropping them biases the median lead time upwards. It also makes the
  most urgent production changes of the period invisible on the dashboard.
- Why the rule is defensible: what matters for delivery is that the code ran in production, not which branch
  it came from; the branch name is a team convention, not a fact about delivery. Counting the shas as
  `commits_never_on_main` still lets a reviewer see how much went around the normal path without distorting
  the metric.

## E4 - a deployment with zero linked commits

- What the log contains: four production deployments in the window carry an empty `commits` list. DEP-0026 and
  DEP-0032 succeeded, and DEP-0043 and DEP-0044 failed; the last two are covered by INC-0010 and INC-0011. These
  are typically configuration, infrastructure or plain redeploys.
- What a default definition would have done: joining deployments to their commits silently drops the four
  deployments. Frequency becomes 38/21 = 1.81 instead of 2.0, and the change fail rate becomes 6/38 = 0.158
  instead of 8/42 = 0.190. Two real production failures vanish from the instability metrics just because no
  code was attached. A per-commit average might even divide by zero.
- Why the rule is defensible: a deployment without code still changes production and can still break it, as
  DEP-0043 and DEP-0044 did. It therefore counts in frequency, in the change fail rate and in the rework rate.
  It contributes no lead-time pair only because there is no commit to measure from.

## E5 - a deployment that failed and never recovered

- What the log contains: DEP-0015 failed at 2026-09-07T06:12:35Z. INC-0004 opened for it at 06:35:41 and has
  no `resolved` event anywhere in the log, so the failure is still open when the window ends.
- What a default definition would have done: one common default "closes" the incident at the window's end and
  books a recovery of about 14.7 days. That invented number depends only on when someone happened to cut the
  window, and it would drag the recovery median up. The other default drops the deployment entirely, which
  also removes the worst failure of the period from the change fail rate.
- Why the rule is defensible: we do not know the recovery time, so the service does not make one up. The
  failure is excluded from the recovery median but reported as `open_failures`, so the reader sees that one
  failure is still burning. It still counts in the change fail rate, because it did fail.

## E6 - overlapping incidents

- What the log contains: 11 unordered pairs of incidents overlap in time.
  - INC-0004 stays open from 2026-09-07 to the window's end, so it overlaps each of the seven later incidents
    (INC-0005 to INC-0011).
  - On 2026-09-07, INC-0010 (06:17-10:37) and INC-0011 (06:37-13:10) cover DEP-0043 and DEP-0044, and overlap
    each other and INC-0005 (10:10-12:18).
  - On 2026-09-19, INC-0007 and INC-0008 overlap.
- What a default definition would have done: merging overlapping incidents into one outage gives DEP-0043 and
  DEP-0044 one shared recovery and hides that they were separate failures. Summing incident durations counts
  the same wall-clock time two or three times. Either way the recovery time on the dashboard stops describing
  any real failure.
- Why the rule is defensible: the metric is about how long a failed deployment took to recover, so it is
  computed per failed deployment from its own covering incident: DEP-0043 recovered in 4 h 23 min and DEP-0044
  in 6 h 31 min. Incidents are neither merged nor added. The overlap is reported separately as
  `overlapping_incident_pairs`, as a signal about operational load rather than as a distortion of recovery
  time.

## Gaming demonstration

I improved `deployment_frequency_per_day` by exploiting R-11. That rule counts every production deployment in
the window whatever it carries, including deployments with no commits at all (R-10). `gaming/after.jsonl` is
produced by `gaming/make_after.py` and makes two changes to the practice log:

- It holds back six real releases from the last days of the window (DEP-0031, DEP-0037 and DEP-0039 to
  DEP-0042) to a "release day" on 23 September, after the window.
- It adds 20 empty, successful production redeploys spread across the window.

No commit, incident or outcome was changed, and no deployment moved earlier.

The effect on the dashboard:

- Deployment frequency rises from 2.0 to 2.67 per day (+33 %).
- The change fail rate falls from 0.190 to 0.143 and the rework rate from 0.119 to 0.089, only because the
  empty redeploys inflate the denominator.
- The median lead time even falls from 375 643 s to 351 500 s, because the held-back work no longer counts at
  all.

Four of the five metrics look better. Measured on the base work alone, however, only 54 of the 65 changes that
were delivered in the window are still delivered: 11 finished changes reach users later.

The incentive that produces this is a target on deployment frequency, for example an OKR or a bonus for
reaching "elite" DORA performance of several deployments a day. For a team under that target, scheduling
no-op redeploys is cheap. Batching the real releases into a later release day feels safer, and it makes this
window's numbers look better as well. The people rewarded are the team and its engineering manager, whose
dashboard now shows an elite deploy rate and a lower failure rate. Customers pay for it: they wait longer for
the same work, and the number meant to show that nothing is shipped less often shows the opposite.
