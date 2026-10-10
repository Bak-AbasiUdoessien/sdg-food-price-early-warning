"""
import_wfp.py  -  Convert REAL World Food Programme (WFP) price data into data/prices.csv.

1. Download "Nigeria - Food Prices" (WFP) from the Humanitarian Data Exchange:
   https://data.humdata.org  -> search "wfp food prices nigeria" -> download the CSV.
2. Run:  python import_wfp.py path/to/wfp_food_prices_nga.csv
3. Then: python ews.py --window 6        (WFP data is monthly, so use a smaller window)

The column names below match the HDX file format at the time of writing.
If WFP changes them, the script stops and tells you which column is missing.
"""

import csv                                  # read and write CSV files
import sys                                  # command-line arguments and exit messages
from pathlib import Path

OUT = Path(__file__).parent / "data" / "prices.csv"     # where our own format is written
NEEDED = ["date", "admin1", "market", "commodity", "unit", "pricetype", "price"]  # columns we use


def main():
    if len(sys.argv) != 2:                                       # sys.argv[0] is the script name itself
        sys.exit("usage: python import_wfp.py <wfp_csv_file>")
    src = Path(sys.argv[1])
    with open(src, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)                               # each row becomes a dict keyed by header
        missing = [c for c in NEEDED if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit(f"Columns not found in {src.name}: {missing}. Has the WFP format changed?")
        rows = []
        for r in reader:
            if r["date"].startswith("#"):                        # HDX files have a 2nd header row of #tags - skip it
                continue
            if r["pricetype"] != "Retail":                       # keep retail prices only (what households pay)
                continue
            try:
                price = float(r["price"])                        # text -> number
            except ValueError:
                continue                                         # skip blank or broken prices
            if price <= 0:
                continue
            rows.append([r["market"], r["admin1"], r["commodity"], r["unit"], r["date"][:10], price])  # [:10] keeps YYYY-MM-DD
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["market", "state", "commodity", "unit", "period", "price"])
        writer.writerows(rows)
    print(f"Imported {len(rows)} real WFP retail prices -> data/prices.csv")


if __name__ == "__main__":
    main()
