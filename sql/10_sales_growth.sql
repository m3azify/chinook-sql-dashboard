-- 10 - Is the business growing?
--
-- Month-over-month revenue change in both dollars and percent, plus a running
-- total. This is the window-function showcase: LAG() reads the previous
-- month's revenue without a self-join.
--
-- WHY a CTE (WITH monthly): the aggregation and the window calculation need
-- different GROUP BY levels. Doing both in one SELECT is illegal in SQL, so
-- we aggregate first, then window over the result.
--
-- WHY the first month shows NULL growth: there is no previous month to
-- compare against. NULL is the honest answer; 0% would be a lie.

WITH monthly AS (
    SELECT
        strftime('%Y-%m', InvoiceDate) AS month,
        COUNT(*)                       AS invoices,
        ROUND(SUM(Total), 2)           AS revenue
    FROM Invoice
    GROUP BY strftime('%Y-%m', InvoiceDate)
)
SELECT
    month,
    invoices,
    revenue,
    LAG(revenue) OVER (ORDER BY month)                                 AS previous_month_revenue,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 2)              AS revenue_change,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
          / LAG(revenue) OVER (ORDER BY month), 1)                      AS growth_pct,
    ROUND(SUM(revenue) OVER (ORDER BY month), 2)                       AS cumulative_revenue
FROM monthly
ORDER BY month;
