-- 05 - How does revenue move month by month?
--
-- 60 months (Jan 2021 - Dec 2025). This is the time-series chart on the
-- dashboard. A line chart of this is the single most useful view of the
-- business.
--
-- WHY strftime('%Y-%m', InvoiceDate): InvoiceDate is stored as text in
-- 'YYYY-MM-DD HH:MM:SS' form, so string slicing is enough and avoids casting.
-- If the column were a real DATETIME we would use date() instead.
--
-- WHY SUM(Total) and not the line items: at the month level the invoice total
-- is the right grain. Line items would give the same answer but cost more.

SELECT
    strftime('%Y-%m', InvoiceDate)                               AS month,
    COUNT(*)                                                     AS invoices,
    COUNT(DISTINCT CustomerId)                                   AS unique_customers,
    ROUND(SUM(Total), 2)                                         AS revenue,
    ROUND(SUM(Total) / COUNT(*), 2)                              AS avg_invoice_value,
    ROUND(SUM(SUM(Total)) OVER (ORDER BY strftime('%Y-%m', InvoiceDate)), 2) AS cumulative_revenue
FROM Invoice
GROUP BY strftime('%Y-%m', InvoiceDate)
ORDER BY month;
