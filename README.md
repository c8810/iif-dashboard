# IIF Dashboard — auto-updating

The Iranian Influence Factor (IIF) Energy Threat Telemetry Dashboard, migrated from
CodePen to GitHub Pages with a daily auto-update pipeline.

**Live site:** (URL goes here once Pages is enabled)

## How it works

- `index.html` — the dashboard. Loads its data from `data/iif.json`, computes
  choke/energy/IIF scores in the browser exactly as the original pen did.
- `data/iif.json` — one row per day: date, global liquids estimate, WTI/Brent/nat-gas
  prices, shadow disruption weight, event note.
- `scripts/daily_update.py` — run daily by GitHub Actions:
  1. Pulls the latest WTI / Brent / nat-gas closes from Yahoo Finance (no key needed).
  2. Asks Gemini for the three judgment fields (liquids estimate, shadow weight,
     event note) using the methodology in `scripts/iif_prompt.md`.
  3. Validates the response and appends the row. Any failure aborts loudly —
     it never writes a bad row.
- `.github/workflows/daily-update.yml` — runs the script nightly at 9:05 PM ET
  and commits the new row. GitHub Pages rebuilds automatically.

## One-time setup

1. **Create the repo** and push this project to `main`.
2. **Add the Gemini key:** get a free key at https://aistudio.google.com/apikey →
   repo Settings → Secrets and variables → Actions → New repository secret →
   name `GEMINI_API_KEY`, value the key. (Free tier covers 1 call/day easily.)
3. **Enable Pages:** repo Settings → Pages → Deploy from branch → `main`, folder
   `/ (root)` → Save.
4. **Test it:** Actions tab → `daily-iif-update` → Run workflow → check the new
   row in `data/iif.json` and the live dashboard.

## Notes

- The prompt's "never invent incidents" rule is load-bearing: spot-check the
  `events` notes for the first week or two until the output matches your judgment.
- If Google renames the model, set the `GEMINI_MODEL` repository variable
  (Settings → Secrets and variables → Actions → Variables) to the new name.
- Weekend rows use the latest available futures closes, matching how the manual
  versions were curated.
