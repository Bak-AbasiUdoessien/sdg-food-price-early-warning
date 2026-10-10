# Food Price Early-Warning System (SDG 2: Zero Hunger)

[![tests](https://github.com/Bak-AbasiUdoessien/sdg-food-price-early-warning/actions/workflows/tests.yml/badge.svg)](https://github.com/Bak-AbasiUdoessien/sdg-food-price-early-warning/actions/workflows/tests.yml)

When the price of staple foods like rice, maize or garri suddenly jumps, poor households cut meals soon after. This project watches market prices and raises a flag the moment a price climbs well above its own recent normal level, so aid can arrive **before** hunger does.

**SDG targets covered:** 2.1 (end hunger) and 2.c (limit extreme food price volatility).

## How it works
1. **Load:** prices go into a normalised SQLite database with `markets`, `commodities` and `prices` tables.
2. **Baseline:** a SQL window function works out each item's average price over the **previous N periods**. The current price is left out, so a spike can't hide inside its own average.
3. **Compare:** for every observation it calculates how far the price is above normal (%) and how much it changed since the last period.
4. **Flag:** Python labels each one **NORMAL**, **WATCH** (≥10% above normal), **ALERT** (≥25%) or **CRISIS** (≥40%). These thresholds are a teaching choice, not an official standard, and you can tune them in `LEVELS`.
5. **Report:** it prints the latest status for every market and item, and saves every flagged observation to `alerts.csv`.

## Run it
```bash
python generate_sample_data.py        # SYNTHETIC weekly prices (2 years, 4 markets, 4 foods)
python ews.py                         # 8-week baseline
python ews.py --window 4              # more sensitive
python -m unittest discover tests     # unit tests
```
Everything uses the Python standard library, so there's nothing to install.

## Use real data (recommended)
The World Food Programme publishes real Nigerian market prices on the Humanitarian Data Exchange:
1. Go to **data.humdata.org**, search "WFP food prices Nigeria" and download the CSV.
2. Run `python import_wfp.py path/to/file.csv`, which keeps retail prices only.
3. Run `python ews.py --window 6`. WFP data is monthly, so use a shorter window.

## Skills shown
- **SQL:** normalised schema, `INSERT OR IGNORE`, window functions (`AVG … OVER (ROWS BETWEEN n PRECEDING AND 1 PRECEDING)`, `LAG`, `COUNT OVER`), and CTEs.
- **Python:** a CSV ETL step, safely building SQL text (`int()` before formatting), dictionaries for grouping, `argparse`, and unit tests that check the edge case of a spike being excluded from its own baseline.

## ⚠️ Data note
`generate_sample_data.py` produces **made-up** prices with seasonality, inflation and one artificial shock per series. Don't present results from it as real.
