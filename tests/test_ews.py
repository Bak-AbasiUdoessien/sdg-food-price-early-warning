"""Unit tests for ews.py. Run from the project folder:  python -m unittest discover tests"""

import sqlite3                                          # in-memory database for tests
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # make "import ews" work
import ews                                              # noqa: E402


class ClassifyTests(unittest.TestCase):
    def test_levels(self):
        self.assertEqual(ews.classify(5), "NORMAL")     # below 10%
        self.assertEqual(ews.classify(10), "WATCH")     # boundary counts as WATCH
        self.assertEqual(ews.classify(30), "ALERT")
        self.assertEqual(ews.classify(55), "CRISIS")


class SignalTests(unittest.TestCase):
    def test_spike_measured_against_previous_periods_only(self):
        conn = sqlite3.connect(":memory:")              # temporary database
        conn.executescript((ews.ROOT / "sql" / "schema.sql").read_text())
        conn.execute("INSERT INTO markets VALUES (1, 'M', 'S')")
        conn.execute("INSERT INTO commodities VALUES (1, 'Rice', 'KG')")
        prices = [100, 100, 100, 150]                   # three normal weeks then a 50% jump
        for week, price in enumerate(prices, start=1):
            conn.execute("INSERT INTO prices VALUES (1, 1, ?, ?)", (f"2026-01-0{week}", price))
        rows = ews.signals(conn, window=3)
        self.assertEqual(len(rows), 1)                  # only the 4th week has 3 periods of history
        self.assertEqual(rows[0]["baseline"], 100)      # the spike itself is NOT in its own baseline
        self.assertEqual(rows[0]["pct_above_normal"], 50.0)
        conn.close()


if __name__ == "__main__":
    unittest.main()
