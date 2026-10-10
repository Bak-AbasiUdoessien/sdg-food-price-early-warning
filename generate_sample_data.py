"""
generate_sample_data.py
Creates data/prices.csv with SYNTHETIC (made-up) weekly food prices.
These are NOT real prices - they exist so you can test the alert logic.
For real prices, use import_wfp.py (see README).
"""

import csv                                  # writes the CSV file
import math                                 # math.sin for a seasonal wave
import random                               # random noise
from datetime import date, timedelta        # building weekly dates
from pathlib import Path                    # file paths

OUT = Path(__file__).parent / "data" / "prices.csv"   # output file
random.seed(11)                                       # same "random" data every run

# Fictional markets: (name, state)
MARKETS = [("Central Market", "North State"), ("River Market", "North State"),
           ("Harbour Market", "South State"), ("Hill Market", "South State")]

# Commodities: (name, unit, starting price) - starting prices are invented.
COMMODITIES = [("Rice (local)", "KG", 1200), ("Maize (white)", "KG", 700),
               ("Garri (white)", "KG", 900), ("Beans (brown)", "KG", 1500)]

WEEKS = 104                                  # two years of weekly data
START = date(2024, 10, 7)                    # a Monday, the first week


def main():
    OUT.parent.mkdir(exist_ok=True)                                   # make data/ if missing
    rows = []                                                         # collected CSV rows
    for market, state in MARKETS:
        for name, unit, base in COMMODITIES:
            price = base * random.uniform(0.9, 1.1)                   # each market starts slightly different
            shock_week = random.randint(60, 100)                      # a week when a sudden price shock starts
            for w in range(WEEKS):
                season = 1 + 0.06 * math.sin(2 * math.pi * w / 52)    # gentle yearly up-and-down (lean season)
                inflation = 1.004 ** w                                # about 0.4% general price rise per week
                shock = 1.35 if shock_week <= w < shock_week + 4 else 1.0   # 35% spike lasting 4 weeks
                noise = random.uniform(0.97, 1.03)                    # small week-to-week wobble
                value = round(price * season * inflation * shock * noise, 2)
                period = (START + timedelta(weeks=w)).isoformat()     # 'YYYY-MM-DD'
                rows.append([market, state, name, unit, period, value])
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["market", "state", "commodity", "unit", "period", "price"])  # header
        writer.writerows(rows)
    print(f"wrote {len(rows)} SYNTHETIC price rows -> {OUT.relative_to(OUT.parent.parent)}")


if __name__ == "__main__":
    main()
