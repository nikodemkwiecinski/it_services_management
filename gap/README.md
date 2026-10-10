<!-- ai-generated: 80% - Claude Code ran the measurement and drafted the explanation, reviewed by me -->
# The client-server latency gap (Lab 3 Stretch 2)

## What was measured

Toxiproxy 2.12.0 ran next to `svcdesk` (compose profile `gap`) with one proxy, `0.0.0.0:8666` to `svcdesk:8080`,
and one toxic on it: `latency`, stream `downstream`, toxicity 1, latency 100 ms, jitter 10 ms. Every chunk of every
response from `svcdesk` back to the client is held for 100 ms plus or minus up to 10 ms before it is passed on.
Then `.\itsmlab.ps1 load 3 --base-url http://host.docker.internal:8666` ran the M-08 load through the proxy (60 s
open-loop at 40 requests per second, latency-corrected), on 10 October 2026, login `nikodemkwiecinski`:

| | p50 | p99 |
|---|---|---|
| client, oha through the proxy | 135.1 ms | **259.9 ms** |
| server, `svcdesk`'s own histogram over the same run | - | **155.0 ms** |
| without the proxy (an earlier run, client) | 30.6 ms | 153.5 ms |

The gap is 259.9 - 155.0 = **104.9 ms** (`gap.json`).

## Why the two numbers differ

The server's histogram measures from the moment `svcdesk`'s middleware receives the request to the moment it has
handed the last byte of the answer to the socket. Everything that happens on the wire after that - here, the
proxy holding the answer for 100 ms - happens outside that interval, so the server's p99 (155 ms) is the same as
without the proxy (149 to 155 ms in earlier runs): the service did not get slower. The client measures from the
instant the request was scheduled until the last byte arrived, so it sees the server's time plus the toxic plus
the extra network hop through the proxy and the host's published port.

The gap is about the toxic's latency, 100 ms, and slightly more: the p50 moved by 104.5 ms (30.6 to 135.1) and the
p99 by 104.9 ms. The extra 4 to 5 ms is the proxy's own hop (oha in the checker's container to the host, the
published port, Toxiproxy, then `svcdesk`), and at the tail the jitter: a p99 picks the slow end of the sum, where
the server's slow mode meets a draw of the toxic above 100 ms. A percentile of a sum is not the sum of the
percentiles, but with a near-constant delay of 100 +- 10 ms it is close to it, which is why the gap at p99 and at
p50 is almost the same.

## What it means for monitoring

A dashboard built only on the server's histogram would show a healthy p99 of 155 ms while every user waits about
260 ms: a slow network, a proxy, a load balancer or a TLS terminator in front of the service is invisible from
inside it. The server-side SLI is still the right one to alert on for what the team controls, but a latency SLO
that promises what users experience needs a client-side measurement too - a synthetic probe or real-user
monitoring - and the difference between the two is where to look when users complain and the service's own
graphs are green.
