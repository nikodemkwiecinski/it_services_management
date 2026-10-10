---
lab3_first_draft:
  source: ai
  tool: "Claude Code (Opus 5.5), in the terminal of this repository, 10 October 2026, 15:02"
  ladder: [0.005, 0.01, 0.025, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.12, 0.14, 0.16, 0.18, 0.2, 0.24, 0.28, 0.33, 0.39, 0.46, 0.55, 0.65, 0.75, 0.9, 1.0, 1.2, 1.4, 1.6, 1.9, 2.25, 2.7]
  verdict: confirmed
  evidence: {p99_seconds: 0.149, bucket: [0.14, 0.16], relative_width: 0.134}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: 0.149, bucket: [0.04, 0.5], relative_width: 3.087}
---
<!-- ai-generated: 90% - the answer is the assistant's, verbatim; the verdicts and their arithmetic drafted by Claude Code from my own measurement and checked by me -->

# The assistant's first draft, and two verdicts

The assistant had read `lab3/MONITORING-SPEC.md` before it answered (it says so in the answer): this draft is not a
blind one, and its ladder was built to satisfy M-11 over a wide range of p99 values rather than from a default.

## Prompt

Zaproponuj granice kubełków histogramu i regułę alertu Prometheus dla endpointu GET /kb/search, który woła zewnętrzny indeks wyszukiwania

## Answer

Nie mierzyłem jeszcze kb-index, więc nie wiem, gdzie leży twoje p99. Dlatego drabinka poniżej jest ustawiona tak, żeby rozdzielić p99 w całym prawdopodobnym zakresie. Nie zgaduje jednej wartości. Przeczytałem lab3/MONITORING-SPEC.md i propozycja trzyma się jego reguł (M-04, M-06, M-11, M-13, M-16 do M-19).

Granice kubełków (w sekundach, 30 granic, czyli limit z M-06)


KB_SEARCH_BUCKETS = [
    0.005, 0.01, 0.025,                                   # zgrubnie: szybkie odpowiedzi i błędy walidacji
    0.05, 0.06, 0.07, 0.08, 0.09, 0.1,                    # gęsto: każdy krok co najwyżej x1.2
    0.12, 0.14, 0.16, 0.18, 0.2,
    0.24, 0.28, 0.33, 0.39, 0.46, 0.55, 0.65, 0.75, 0.9,
    1.0, 1.2, 1.4, 1.6, 1.9, 2.25, 2.7,                   # do timeoutu upstreamu (co najmniej 2 s, M-02) i trochę powyżej
]
Histogram("http_server_request_duration_seconds", "...",
          ["http_request_method", "http_route", "http_response_status_code"],
          buckets=KB_SEARCH_BUCKETS)
Dlaczego tak:

Każda para sąsiednich granic od 0,05 s w górę ma iloraz co najwyżej 1,2. Kubełek (lo, hi] z hi ≤ 1,2·lo ma szerokość co najwyżej 0,2·lo, a lo < q. Każde p99 między 50 ms a 2,7 s spełnia więc warunek M-11 (hi − lo ≤ 0,20·q), niezależnie od tego, gdzie dokładnie wypadnie. Domyślne drabinki tego nie dają: ta z Pythona ma kroki co najmniej 25%, a ta z Go co najmniej 50%.
histogram_quantile się zgodzi. Interpolacja liniowa w kubełku o szerokości ≤ 20% daje błąd mniejszy niż tolerancja 25% z M-12.
Progi to okrągłe liczby (0.24, 0.28, 0.33…). Próg SLI latencji musi być jedną z granic (M-13), a te łatwo wpisać jako le="0.28".
Ta sama drabinka obowiązuje dla wszystkich tras (M-06). Pod 50 ms jest zgrubnie, bo p99 endpointu, który robi wywołanie sieciowe, raczej tam nie spadnie.
Ryzyko: jeśli twoje p99 wyjdzie poniżej 50 ms albo powyżej 2,7 s, ta drabinka go nie rozdzieli. Po pomiarze (.\itsmlab.ps1 load 3) przenieś gęsty pas w okolice zmierzonego p99.
Reguła alertu (multi-window, multi-burn-rate na SLI dostępności)

Założenia: okno 30d, cel 99%, odpowiedź 5xx (czyli 502 z upstream_unavailable) liczy się jako zła. Pasuje to tylko wtedy, gdy własny odsetek błędów kb-index jest wyraźnie poniżej 1%, więc najpierw go zmierz.


groups:
  - name: svcdesk-slo
    rules:
      - alert: KbSearchErrorsBurnFast          # 14.4x: 2% budżetu w 1h
        expr: |
          (
            sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code=~"5.."}[1h]))
              /
            sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[1h]))
          ) > 14.4 * (1 - 0.99)
          and
          (
            sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code=~"5.."}[5m]))
              /
            sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))
          ) > 14.4 * (1 - 0.99)
        for: 2m
        labels:
          service: svcdesk
          slo: availability
          severity: P1
        annotations:
          summary: "/kb/search: >14.4% odpowiedzi 5xx w 1h i 5m - kb-index zawodzi, budżet 30d skończy się za ~2 dni"

      - alert: KbSearchErrorsBurnSlow          # 6x: 5% budżetu w 6h
        expr: |
          (
            sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code=~"5.."}[6h]))
              /
            sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[6h]))
          ) > 6 * (1 - 0.99)
          and
          (
            sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code=~"5.."}[30m]))
              /
            sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[30m]))
          ) > 6 * (1 - 0.99)
        for: 2m
        labels:
          service: svcdesk
          slo: availability
          severity: P2
        annotations:
          summary: "/kb/search: >6% odpowiedzi 5xx w 6h i 30m - budżet 30d skończy się za ~5 dni"
Dlaczego tak:

Okno krótkie to najwyżej 1/4 długiego (5m/1h, 30m/6h). Dzięki temu alert gaśnie po kilku minutach od końca spalania, a nie po pół godziny. To jest sonda „reset” z M-19.
Progi są stałymi wpisanymi w regułę (14.4 * (1 - 0.99)). Nie ukrywam ich w regule nagrywającej, bo M-18 wymaga stałej, a checker robi z niej mutanty.
Filtr to job="svcdesk" i http_route="/kb/search", bez instance. Ruch z /tickets/{id} nie rozcieńcza wtedy proporcji.
Wymagania M-16 są spełnione: 14.4 × 0.01 = 0.144 ≤ 0.5. Są dwa alerty na tym samym SLI z różnymi burn rate i co najmniej jeden ma P1.
Do tego slo.md deklaruje:


alerts:
  - {alert: KbSearchErrorsBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
  - {alert: KbSearchErrorsBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
Opcjonalnie: alert latencji. Złe żądanie to _count − _bucket{le="<próg>"}, a próg to jedna z granic powyżej, wybrana po pomiarze. Przy celu 0.95 burn rate może wynieść najwyżej 10, bo 10 × 0.05 = 0.5 (M-16). Wartość 14.4 nie przejdzie.

Uwaga do labu: jeśli wklejasz to do ai-first-draft.md jako ## Answer, odpowiedź nie ma linii zaczynających się od ## , więc nie trzeba jej cytować przez > . W polu ladder wpisz 30 granic dokładnie w tej kolejności. Wpisz też uczciwie, że ta odpowiedź powstała po przeczytaniu MONITORING-SPEC, a nie „na ślepo”. Werdykt (confirmed albo refuted) wynika dopiero z twojego pomiaru p99.

## Verdict on the draft ladder

The measurement is `.\itsmlab.ps1 load 3` for login `nikodemkwiecinski` (10 October 2026): 60 s open-loop at 40
requests per second, 2,399 responses. p50 29.6 ms, p95 70.3 ms, **p99 149.0 ms**, p99.9 196.7 ms; `kb-index` measured
directly had a p99 of 163.8 ms. Most searches finish in 20 to 60 ms; a slow mode between about 110 and 220 ms holds
roughly 3 % of them, and the p99 sits inside it.

In the draft ladder 0.149 s falls between the boundaries 0.14 and 0.16, so the bucket is (0.14, 0.16]: 0.02 s wide,
0.02 / 0.149 = 0.134 of the p99, below the 0.20 that M-11 allows. `histogram_quantile` can only interpolate inside
that bucket, so the p99 it reports lies between 140 and 160 ms, at most 13 % away from the real one; the service's
own histogram, which used this ladder during the run, reported 152.0 ms. The result is the same at 0.95 x q
(0.1416 s) and 1.05 x q (0.1565 s), which stay in the same bucket. Verdict: **confirmed**, the draft ladder resolves
my p99.

It resolves it because the assistant had read the rulebook and kept every step above 50 ms at a ratio of at most
1.2, not because it knew where my p99 was; it spent 20 of its 30 boundaries on a range of 50 ms to 2.7 s that my
distribution mostly does not use.

## The draft alert rule

The draft's two alerts are a multiwindow, multi-burn-rate pair on the availability SLI: 14.4x over 1h and 5m (P1)
and 6x over 6h and 30m (P2), at an objective of 0.99, thresholds written as constants in the rule, filtered on
`job="svcdesk"` and `http_route="/kb/search"`. For my service that fits: `kb-index` failed 7 of 2,399 searches
(0.29 %) in the measurement, which is a burn rate of 0.29 against a 1 % budget, far below both thresholds, so the
alerts stay quiet on a normal day and fire when the index really degrades. I kept the structure, the windows, the
burn rates, the severities and the objective in `prometheus/alerts.yml`; the summaries are rewritten, and the tests
in `alerts_test.yml` are mine. The draft's own caveat - that 0.99 only fits when the index's own error rate is well
below 1 % - is exactly what the measurement checked.

## Verdict on the instructor's flawed ladder

The flawed ladder spends twelve of its fourteen boundaries below 40 ms, where my median (29.6 ms) lives, and then
jumps to 0.5 and 2.5. My p99 of 0.149 s falls in (0.04, 0.5]: 0.46 s wide, 0.46 / 0.149 = 3.087 of the p99, fifteen
times the 0.20 that M-11 allows. `histogram_quantile` would report anything between 40 and 500 ms: about 69 % of my
requests are at or below 40 ms (from oha's histogram), so the 99th rank sits at (0.99 - 0.69) / 0.31, about 97 %, of
the way through that bucket, and the interpolated p99 would be near 0.48 s, more than three times the real one. Its
whole slow mode, 110 to 220 ms, is invisible in one bucket. Verdict: **refuted**.
