"""
ews.py  -  Food Price Early-Warning System (SDG 2: Zero Hunger)
Loads data/prices.csv into SQLite, compares each price with its own recent
average, and raises NORMAL / WATCH / ALERT / CRISIS flags. Sudden food price
spikes are one of the earliest warning signs that households may go hungry.

Run:
    python generate_sample_data.py      # made-up data (or use import_wfp.py for real data)
    python ews.py                       # weekly data, 8-week baseline
    python ews.py --window 6            # e.g. for monthly WFP data
"""

import argparse                         # command-line options
import csv                              # read prices.csv, write alerts.csv
import sqlite3                          # database
import sys                              # exit with a message
from pathlib import Path

ROOT = Path(__file__).parent
DB_PATH = ROOT / "food_prices.db"       # database file (rebuilt every run)
PRICES_CSV = ROOT / "data" / "prices.csv"

# Alert levels: (minimum % above normal, label). Checked from the top down.
# These thresholds are a simple teaching choice, not an official standard - tune them.
LEVELS = [(40, "CRISIS"), (25, "ALERT"), (10, "WATCH")]


def classify(pct_above_normal):
    """Turn '% above normal price' into an alert label."""
    for threshold, label in LEVELS:             # LEVELS is ordered from most to least severe
        if pct_above_normal >= threshold:
            return label                        # first threshold we pass wins
    return "NORMAL"                             # below every threshold


def build_db(conn):
    """Create tables and load the CSV, filling the lookup tables as we go."""
    conn.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))   # fresh tables
    with open(PRICES_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))          # every row as a dict
    for r in rows:
        # INSERT OR IGNORE adds the market only if it isn't already there (UNIQUE stops duplicates).
        conn.execute("INSERT OR IGNORE INTO markets (name, state) VALUES (?, ?)", (r["market"], r["state"]))
        conn.execute("INSERT OR IGNORE INTO commodities (name, unit) VALUES (?, ?)", (r["commodity"], r["unit"]))
        conn.execute(
            """INSERT OR REPLACE INTO prices (market_id, commodity_id, period, price)
               SELECT m.market_id, c.commodity_id, ?, ?            -- look up the ids we just made sure exist
               FROM markets m, commodities c
               WHERE m.name = ? AND m.state = ? AND c.name = ? AND c.unit = ?""",
            (r["period"], float(r["price"]), r["market"], r["state"], r["commodity"], r["unit"]),
        )
    conn.commit()
    return len(rows)


def signals(conn, window):
    """Run sql/signals.sql with the chosen window size and return the rows."""
    sql = (ROOT / "sql" / "signals.sql").read_text(encoding="utf-8")
    sql = sql.replace("{window}", str(int(window)))  # int() guarantees only a number is inserted into SQL
    conn.row_factory = sqlite3.Row                    # rows act like dicts
    return conn.execute(sql).fetchall()


def main():
    parser = argparse.ArgumentParser(description="Flag unusual food price rises.")
    parser.add_argument("--window", type=int, default=8, help="periods in the 'normal price' baseline (default 8)")
    args = parser.parse_args()
    if args.window < 2:
        sys.exit("--window must be at least 2")
    if not PRICES_CSV.exists():
        sys.exit("data/prices.csv not found. Run: python generate_sample_data.py (or import_wfp.py)")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        n = build_db(conn)
        print(f"Loaded {n} prices into {DB_PATH.name}")
        rows = signals(conn, args.window)

    if not rows:
        sys.exit("Not enough history for that window. Try a smaller --window.")

    # --- Latest status for every market + commodity ------------------------
    latest = {}                                       # (market, commodity) -> newest row
    for r in rows:                                    # rows are sorted by period, so later rows overwrite earlier
        latest[(r["market"], r["commodity"])] = r
    print(f"\nLATEST STATUS (baseline = previous {args.window} periods)")
    print(f"{'Market':<16}{'Commodity':<16}{'Period':<12}{'Price':>10}{'Normal':>10}{'Above':>8}  Level")
    print("-" * 82)
    for (market, commodity), r in sorted(latest.items()):
        level = classify(r["pct_above_normal"])
        print(f"{market:<16}{commodity:<16}{r['period']:<12}{r['price']:>10.2f}{r['baseline']:>10.2f}"
              f"{r['pct_above_normal']:>7.1f}%  {level}")

    # --- Every non-normal signal in history, saved for analysis --------------
    flagged = [dict(r, level=classify(r["pct_above_normal"])) for r in rows       # dict(r, level=...) copies r and adds a key
               if classify(r["pct_above_normal"]) != "NORMAL"]
    with open(ROOT / "alerts.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + ["level"])
        writer.writeheader()
        writer.writerows(flagged)

    counts = {}                                       # how many of each level
    for r in flagged:
        counts[r["level"]] = counts.get(r["level"], 0) + 1   # .get(key, 0) = 0 if the key isn't there yet
    print(f"\nHistory: {len(flagged)} flagged observations {counts} -> alerts.csv")
    worst = max(flagged, key=lambda r: r["pct_above_normal"], default=None)   # biggest spike ever seen
    if worst:
        print(f"Biggest spike: {worst['commodity']} in {worst['market']} on {worst['period']}, "
              f"{worst['pct_above_normal']}% above normal")


if __name__ == "__main__":
    main()
