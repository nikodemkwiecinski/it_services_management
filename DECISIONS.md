---
svcdesk_decisions:
  C1: wallclock      # wallclock | business
  C2: immutable      # reopen | immutable
  C3: matrix         # matrix | vip
---
<!-- ai-generated: 60% - Claude Code drafted the text from my choice of the three resolutions; I reviewed and edited the reasons -->

# Decisions

## C1 - SLA clock for P1

**Decision:** Both P1 targets run on the wall clock: acknowledgement is due at `created_at + 15 min` and
resolution at `created_at + 4 h`, around the clock. P2 to P4 keep the business-hours clock of R-13. The part of
R-13 that is rejected is its scope, "any SLA target", for the two P1 targets only.

**Rejected alternative:** `business`: every priority, P1 included, pauses outside Monday to Friday 08:00-16:00
Europe/Warsaw. That keeps R-13 whole and drops R-14's "around the clock", so a P1 raised on Friday at 17:00 is
first due on Monday at 08:15.

**Reason:** R-14 is the specific rule and R-13 the general one; R-14 even names the case it exists for (a P1 on
Friday evening is late at 15 minutes past, not on Monday). A P1 means the whole organisation has stopped
working. Under the business clock, an outage that lasted a whole weekend would be reported as on time, which
defeats the reason the desk is being built: knowing on Monday at 09:00 which tickets are late. What we give up
is a single clock for all priorities and a desk that can ignore evenings and weekends; a P1 outside business
hours now needs someone on call, or it is reported as breached. R-13 still governs three of the four
priorities, and a P1 raised inside business hours has identical due instants under either clock (T1).

**Service owner:** The Service Level Manager. The clock definition is part of the service level agreement with
the organisation, and the consequence of this decision is an out-of-hours on-call cost for P1, which only the
role that negotiates targets and their funding can accept.

**Customer outcome:** When the whole organisation is down, it gets an acknowledgement within 15 minutes and a
fix target of 4 hours at any time of day or week. The Monday report shows weekend outages that were not handled
in time as breached instead of hiding them.

## C2 - Closed tickets and reopening

**Decision:** A closed ticket is immutable. Reopen is accepted only from `resolved`, while
`now <= resolved_at + 7 days`; reopen on a `closed` ticket answers 409 at any age, and further work on the
same issue is a new ticket that references the closed one through `related_to`. The part of R-10 that is
rejected is the words "or closed"; R-09 and the rest of R-10 and R-11 hold.

**Rejected alternative:** `reopen`: a closed ticket can also be reopened within 7 days of `closed_at` and
returns to `in_progress`. That keeps R-10 whole and breaks R-09, because a closed ticket would change state
again.

**Reason:** R-07 closes a ticket only after the reporter has confirmed the fix, and until then the ticket sits
in `resolved` where the 7-day reopen window of R-10 still applies, so the reporter keeps a way back while the
fix is being checked. After confirmation the record is final. The reports count closed tickets; letting them
change state rewrites figures that were already reported, which is what the requirements say the service must
refuse. There is also an SLA reason: R-11 keeps the original resolution target on reopen, so a closed ticket
reopened days later would be breached the moment it is reopened, while a new ticket gets a target that fits the
new work and stays linked to the history through `related_to`. What we give up is one step for the reporter:
if a confirmed fix fails, they raise a new ticket instead of reopening the old one.

**Service owner:** The Service Desk Manager. The ticket life cycle, the meaning of "closed" and the closure
confirmation with the reporter are how the desk runs day to day, and the Monday report that depends on closed
tickets staying closed is theirs to publish.

**Customer outcome:** Reporters can still reopen a fix that did not work for 7 days after resolution. The
organisation gets closure figures that never change once reported, and a recurring problem shows up as a new
linked ticket with its own fair SLA instead of an instant breach on an old one.

## C3 - VIP reporters and the priority matrix

**Decision:** Priority comes from the impact and urgency matrix only. `reporter.vip` is validated, stored and
returned, but it does not change the priority: impact 3, urgency 3 from a VIP is `P4`, and impact 1, urgency 1
is `P1` as for anyone. R-06 is the rejected requirement; its whole content is the conflicting part, so none of
it can be kept as a priority rule.

**Rejected alternative:** `vip`: after the matrix, a VIP ticket at P3 or P4 is raised to P2. That keeps R-06
and breaks R-05's "from nothing else", because a reporter attribute would then decide the priority.

**Reason:** Priority is the desk's measure of business impact and urgency, and it decides who waits. A
cosmetic issue that affects one person has the same impact whoever raises it. Raising it to P2 gives it a
1-hour acknowledgement and 8-hour resolution target, ahead of a team whose work is degraded (P3), and fills the
P2 figures in the SLA report with tickets that are not urgent. R-05 already says that the reporter cannot
request a priority, and a VIP flag is exactly that: a request for priority. An executive whose work has
actually stopped is not disadvantaged: the matrix gives that ticket P1 to P3 through impact and urgency. What we
give up is R-06's goal of making executive issues visible at once; the flag is kept on the ticket so a future
view or filter can show them without distorting priority.

**Service owner:** The incident management process owner. The priority matrix is the organisation-wide
prioritisation policy of the incident process, and an exception for one group of reporters is a change to that
policy that needs their approval and the business's agreement.

**Customer outcome:** Teams whose work is stopped or degraded are served in order of business impact and are
not queued behind low-impact VIP requests. The organisation gets priority and SLA figures that mean the same for
every reporter.
