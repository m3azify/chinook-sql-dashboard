-- 07 - How big is a typical order, and does it differ by market?
--
-- Average order value (AOV) overall and per country, restricted to markets
-- with at least 5 orders so a single big invoice cannot distort the average.
--
-- WHY HAVING COUNT(*) >= 5: Chile has 7 orders and an AOV of $6.66; one
-- market with 1 order and a $25 invoice would look like the best market in
-- the world. A minimum-n filter is the simplest guard against that.
--
-- WHY a separate "All markets" row: the dashboard KPI card shows the global
-- AOV, and the bar chart shows the per-country spread around it. Keeping both
-- in one query means the two can never disagree.

SELECT
    'All markets'                                                AS market,
    COUNT(*)                                                     AS orders,
    ROUND(AVG(Total), 2)                                         AS avg_order_value,
    ROUND(MIN(Total), 2)                                         AS smallest_order,
    ROUND(MAX(Total), 2)                                         AS largest_order,
    ROUND(SUM(Total), 2)                                         AS revenue
FROM Invoice
UNION ALL
SELECT
    c.Country                                                    AS market,
    COUNT(*)                                                     AS orders,
    ROUND(AVG(i.Total), 2)                                       AS avg_order_value,
    ROUND(MIN(i.Total), 2)                                       AS smallest_order,
    ROUND(MAX(i.Total), 2)                                       AS largest_order,
    ROUND(SUM(i.Total), 2)                                       AS revenue
FROM Invoice AS i
JOIN Customer AS c ON c.CustomerId = i.CustomerId
GROUP BY c.Country
HAVING COUNT(*) >= 5
ORDER BY avg_order_value DESC;
