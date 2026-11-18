-- 03 - Where does the money come from geographically?
--
-- Revenue, order count and customer count per country. Answers "which markets
-- should I advertise in?" and "am I over-exposed to one country?".
--
-- WHY group by Customer.Country and not Invoice.BillingCountry: they agree in
-- this dataset (checked in 01_kpis indirectly via a 0-mismatch join), but the
-- customer's country is the marketing-relevant one. BillingCountry is just the
-- address printed on the invoice.

SELECT
    c.Country                                                    AS country,
    COUNT(DISTINCT c.CustomerId)                                 AS customers,
    COUNT(DISTINCT i.InvoiceId)                                  AS orders,
    ROUND(SUM(i.Total), 2)                                       AS revenue,
    ROUND(100.0 * SUM(i.Total)
          / (SELECT SUM(Total) FROM Invoice), 1)                  AS pct_of_total_revenue
FROM Customer AS c
JOIN Invoice AS i ON i.CustomerId = c.CustomerId
GROUP BY c.Country
ORDER BY revenue DESC;
