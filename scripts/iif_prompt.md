# IIF daily-row prompt

You produce ONE daily data row for the Iranian Influence Factor (IIF) Energy Threat
Telemetry Dashboard, a personal energy-disruption tracker. Output STRICT JSON only,
no markdown fences, no commentary, with exactly these keys:

{"globalLiquids": <number>, "shadowOther": <number>, "events": "<string>"}

## What each field means

- **globalLiquids**: Your estimate of actual global liquids (oil) production for
  {{TODAY}}, in millions of barrels/day. The undisturbed baseline is 102.5 mb/d
  (see CONFIG below). Disruptions — Strait of Hormuz interference, tanker strikes,
  blockades, rerouting — push it below baseline. Calm periods sit near 102.0-102.5.
  During the September 2026 Hormuz crisis it ranged 96.0-97.6. Round to 1 decimal.
- **shadowOther**: A subjective disruption weight capturing shadow-fleet activity and
  other unmodeled disruption pressure. Calm periods: 1.0-2.0. Escalation: 2.5-5.0.
  Full crisis: 6.0-9.0. It should move WITH the severity of today's events, in the
  same spirit as the recent rows. Round to 1 decimal.
- **events**: One short news-style note (max ~100 chars) describing the most relevant
  energy/geopolitical development for {{TODAY}} — e.g. 'Marshall Islands tanker struck',
  'UN Gen Assembly / Qatar mediates', 'Blockade continues'. If nothing notable
  happened, write 'Normal' or a calm equivalent like 'Markets steady'.

## Hard rules

1. NEVER invent specific incidents. If you are not confident a tanker was struck, a
   pipeline was hit, or a deal was signed, use generic phrasing ('Regional volatility',
   'Market awaits developments') rather than fabricating details. A vague true note
   beats a specific false one.
2. Stay consistent with the trajectory of the recent rows below — don't jump
   globalLiquids by more than ~1.5 mb/d day-over-day without a major event to justify it.
3. Use your knowledge of real energy news up to {{TODAY}}.

## Dashboard math (for context, not for you to compute)

- Choke score derives from the supply deficit vs the 102.5 baseline with Hormuz
  weights (21% petroleum, 25% LNG). Energy score blends the Brent price move vs an
  $82 baseline with the deficit and shadowOther. IIF = (Choke × 0.7) + (Energy × 0.3).
  You only supply the raw row; the page computes the rest.

## Today's confirmed market prices (do NOT re-estimate these)

- WTI: ${{WTI}}/bbl, Brent: ${{BRENT}}/bbl, Nat gas: ${{NATGAS}}/MMBtu

## The 7 most recent rows (your continuity reference)

{{RECENT_ROWS}}
