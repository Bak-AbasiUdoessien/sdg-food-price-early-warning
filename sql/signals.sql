-- =====================================================================
-- signals.sql  -  Compare every price with its own recent "normal" level.
-- {window} is replaced by ews.py with a whole number (e.g. 8) before running,
-- because SQLite does not allow a ? placeholder inside a window frame.
-- =====================================================================
WITH ordered AS (
    SELECT
        m.name                                    AS market,        -- market name
        m.state                                   AS state,         -- state
        c.name                                    AS commodity,     -- food item
        c.unit                                    AS unit,          -- unit of the price
        p.period                                  AS period,        -- date of this observation
        p.price                                   AS price,         -- price this period
        AVG(p.price) OVER (                                         -- average of...
            PARTITION BY p.market_id, p.commodity_id                --  ...the same item in the same market...
            ORDER BY p.period                                       --  ...in date order...
            ROWS BETWEEN {window} PRECEDING AND 1 PRECEDING         --  ...over the previous {window} periods (NOT this one)
        )                                         AS baseline,
        COUNT(p.price) OVER (                                       -- how many past periods the baseline used
            PARTITION BY p.market_id, p.commodity_id
            ORDER BY p.period
            ROWS BETWEEN {window} PRECEDING AND 1 PRECEDING
        )                                         AS baseline_n,
        LAG(p.price) OVER (                                         -- the previous period's price
            PARTITION BY p.market_id, p.commodity_id
            ORDER BY p.period
        )                                         AS prev_price
    FROM prices p
    JOIN markets m     ON m.market_id = p.market_id                 -- attach market name
    JOIN commodities c ON c.commodity_id = p.commodity_id           -- attach commodity name
)
SELECT
    market, state, commodity, unit, period, price,
    ROUND(baseline, 2)                                   AS baseline,         -- the "normal" price
    ROUND(100.0 * (price - baseline) / baseline, 1)      AS pct_above_normal, -- how far above normal, in %
    ROUND(100.0 * (price - prev_price) / prev_price, 1)  AS pct_change        -- change since last period, in %
FROM ordered
WHERE baseline_n = {window}                       -- skip early periods that don't have a full history yet
ORDER BY market, commodity, period;
