#!/usr/bin/env python3
"""Daily IIF dashboard updater.

1. Fetches the latest closes for WTI (CL=F), Brent (BZ=F), Henry Hub nat gas (NG=F)
   from Yahoo Finance (no API key needed).
2. Asks Gemini (GEMINI_API_KEY env var) for the judgment fields Chase used to
   curate by hand: globalLiquids estimate, shadowOther weight, and the event note.
3. Validates the AI's output, appends the row to data/iif.json, and exits 0.
   Any failure exits non-zero so the GitHub Action fails LOUDLY instead of
   writing a bad row.

Run from the repo root:  python3 scripts/daily_update.py
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "iif.json")
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "iif_prompt.md")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

SYMBOLS = {"wtiPrice": "CL=F", "brentPrice": "BZ=F", "natGasPrice": "NG=F"}


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def yahoo_last_close(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=10d"
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
    except (urllib.error.URLError, TimeoutError) as e:
        fail(f"Yahoo Finance request failed for {symbol}: {e}")
    try:
        res = d["chart"]["result"][0]
        closes = res["indicators"]["quote"][0]["close"]
        stamps = res["timestamp"]
    except (KeyError, IndexError, TypeError):
        fail(f"Unexpected Yahoo response shape for {symbol}")
    # Walk back to the last non-null close (latest bar can be partial/None)
    for ts, c in reversed(list(zip(stamps, closes))):
        if c is not None:
            bar_date = datetime.fromtimestamp(ts, ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
            return round(float(c), 2), bar_date
    fail(f"No usable closes returned for {symbol}")


def gemini_row(prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        fail("GEMINI_API_KEY is not set")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={key}")
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3},
    }).encode()
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json", **UA})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        fail(f"Gemini API HTTP {e.code}: {e.read()[:300]}")
    except (urllib.error.URLError, TimeoutError) as e:
        fail(f"Gemini API request failed: {e}")
    try:
        text = d["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        fail(f"Could not parse Gemini response: {e}")


def main():
    with open(DATA_PATH) as f:
        rows = json.load(f)

    today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    if any(r["date"] == today for r in rows):
        print(f"Row for {today} already exists — nothing to do.")
        return

    prices, bar_dates = {}, {}
    for field, sym in SYMBOLS.items():
        price, bar_date = yahoo_last_close(sym)
        prices[field] = price
        bar_dates[field] = bar_date
    print(f"Market closes: {prices} (bars dated {bar_dates})")

    template = open(PROMPT_PATH).read()
    recent = json.dumps(rows[-7:], indent=2)
    prompt = (template
              .replace("{{TODAY}}", today)
              .replace("{{WTI}}", str(prices["wtiPrice"]))
              .replace("{{BRENT}}", str(prices["brentPrice"]))
              .replace("{{NATGAS}}", str(prices["natGasPrice"]))
              .replace("{{RECENT_ROWS}}", recent))

    ai = gemini_row(prompt)
    print(f"Gemini returned: {ai}")

    # --- validation: never write a bad row silently ---
    try:
        gl = float(ai["globalLiquids"])
        sh = float(ai["shadowOther"])
        ev = str(ai["events"]).strip()
    except (KeyError, TypeError, ValueError):
        fail(f"Gemini output missing/invalid fields: {ai}")
    if not (90.0 <= gl <= 110.0):
        fail(f"globalLiquids {gl} outside sane range 90-110")
    if not (0.0 <= sh <= 20.0):
        fail(f"shadowOther {sh} outside sane range 0-20")
    if not ev or len(ev) > 140:
        fail(f"events note empty or too long: {ev!r}")

    new_row = {
        "date": today,
        "globalLiquids": round(gl, 1),
        "wtiPrice": prices["wtiPrice"],
        "brentPrice": prices["brentPrice"],
        "natGasPrice": prices["natGasPrice"],
        "shadowOther": round(sh, 1),
        "events": ev,
    }
    rows.append(new_row)
    with open(DATA_PATH, "w") as f:
        json.dump(rows, f, indent=2)
        f.write("\n")
    print(f"Appended row for {today}: {new_row}")


if __name__ == "__main__":
    main()
