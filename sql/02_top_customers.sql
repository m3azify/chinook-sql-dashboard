-- 02 - Which customers spend the most?
--
-- Top 10 customers by lifetime revenue. A small business lives or dies by its
-- repeat buyers, so this is the first question a store owner asks.
--
-- WHY RANK() and not ROW_NUMBER(): two customers can tie on revenue (they do
-- here, at $45.62). RANK() keeps the tie visible; ROW_NUMBER() would invent
-- an ordering that does not exist in the data.
--
-- WHY the percent column: revenue share is more actionable than raw dollars
-- when the owner asks "how much of my business is these 10 people?".

SELECT
    RANK() OVER (ORDER BY SUM(i.Total) DESC)                    AS revenue_rank,
    c.CustomerId                                                 AS customer_id,
    c.FirstName || ' ' || c.LastName                             AS customer_name,
    c.Country                                                    AS country,
    c.Email                                                      AS email,
    COUNT(DISTINCT i.InvoiceId)                                  AS orders,
    ROUND(SUM(i.Total), 2)                                       AS lifetime_revenue,
    ROUND(100.0 * SUM(i.Total)
          / (SELECT SUM(Total) FROM Invoice), 2)                  AS pct_of_total_revenue
FROM Customer AS c
JOIN Invoice AS i ON i.CustomerId = c.CustomerId
GROUP BY c.CustomerId
ORDER BY lifetime_revenue DESC
LIMIT 10;
