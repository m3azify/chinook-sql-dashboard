-- 01 - What are the headline numbers for the whole business?
--
-- A single row of KPIs. This feeds the dashboard's cards and gives a reader
-- the scale of the dataset before they look at any chart.
--
-- WHY subqueries instead of joins: each KPI is an independent count/sum, so
-- joining would multiply rows (Invoice x InvoiceLine) and corrupt the totals.
-- Subqueries in the SELECT list keep every figure independent and exact.
--
-- "customers_with_no_invoices" is the answer to the classic "customers who
-- never bought" question: in this dataset it is 0, which is itself a finding
-- (every one of the 59 customers has at least one invoice).

SELECT
    (SELECT COUNT(*) FROM Invoice)                              AS total_invoices,
    (SELECT COUNT(*) FROM Customer)                              AS total_customers,
    (SELECT COUNT(*) FROM Customer c
       WHERE NOT EXISTS (SELECT 1 FROM Invoice i
                          WHERE i.CustomerId = c.CustomerId))     AS customers_with_no_invoices,
    (SELECT COUNT(*) FROM InvoiceLine)                          AS invoice_lines,
    (SELECT COALESCE(SUM(Quantity), 0) FROM InvoiceLine)        AS units_sold,
    (SELECT ROUND(SUM(Total), 2) FROM Invoice)                  AS total_revenue,
    (SELECT ROUND(AVG(Total), 2) FROM Invoice)                  AS avg_order_value,
    (SELECT COUNT(DISTINCT TrackId) FROM InvoiceLine)           AS distinct_tracks_sold,
    (SELECT COUNT(*) FROM Track)                                AS tracks_in_catalog,
    (SELECT ROUND(100.0 * (SELECT COUNT(DISTINCT TrackId) FROM InvoiceLine)
                       / (SELECT COUNT(*) FROM Track), 1))        AS pct_catalog_sold,
    (SELECT MIN(InvoiceDate) FROM Invoice)                      AS first_invoice_date,
    (SELECT MAX(InvoiceDate) FROM Invoice)                      AS last_invoice_date;
