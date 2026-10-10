-- =====================================================================
-- schema.sql  -  Food Price Early-Warning System (SDG 2: Zero Hunger)
-- =====================================================================

DROP TABLE IF EXISTS prices;        -- child table first (it points at the other two)
DROP TABLE IF EXISTS markets;
DROP TABLE IF EXISTS commodities;

-- One row per market (where prices are collected).
CREATE TABLE markets (
    market_id  INTEGER PRIMARY KEY,               -- unique id
    name       TEXT NOT NULL,                     -- market name
    state      TEXT NOT NULL,                     -- state/region the market is in
    UNIQUE (name, state)                          -- the same name can exist in two different states
);

-- One row per food item being tracked.
CREATE TABLE commodities (
    commodity_id  INTEGER PRIMARY KEY,            -- unique id
    name          TEXT NOT NULL,                  -- e.g. 'Rice (local)'
    unit          TEXT NOT NULL,                  -- e.g. 'KG' - prices are per this unit
    UNIQUE (name, unit)                           -- 'Rice per KG' and 'Rice per 50KG bag' are different items
);

-- One price observation per market, commodity and period.
CREATE TABLE prices (
    market_id     INTEGER NOT NULL REFERENCES markets(market_id),        -- which market
    commodity_id  INTEGER NOT NULL REFERENCES commodities(commodity_id), -- which food item
    period        TEXT    NOT NULL CHECK (date(period) = period),        -- 'YYYY-MM-DD' (week or month start)
    price         REAL    NOT NULL CHECK (price > 0),                    -- price in local currency
    PRIMARY KEY (market_id, commodity_id, period)                        -- one price per item per market per period
);

-- Speeds up the window functions, which sort by market + commodity + period.
CREATE INDEX idx_prices_series ON prices(market_id, commodity_id, period);
