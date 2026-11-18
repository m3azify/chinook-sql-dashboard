-- 08 - Which sales rep brings in the most revenue?
--
-- Each customer is owned by one employee (SupportRepId). We attribute every
-- invoice to that employee and rank them. Managers and IT staff appear with
-- zero because they own no customers - that is correct and worth showing.
--
-- WHY LEFT JOINs: an INNER JOIN would silently drop the 5 employees who have
-- no customers, and the ranking would look like there are only 3 employees.
-- LEFT JOIN keeps the whole org chart visible.
--
-- WHY attribute by SupportRepId and not by who closed the deal: the dataset
-- has no deal/owner history, so SupportRepId is the only defensible link
-- between an employee and revenue. The README says so explicitly.

SELECT
    RANK() OVER (ORDER BY COALESCE(SUM(i.Total), 0) DESC)        AS sales_rank,
    e.EmployeeId                                                 AS employee_id,
    e.FirstName || ' ' || e.LastName                             AS employee_name,
    e.Title                                                      AS title,
    e.City || ', ' || e.Country                                  AS location,
    COUNT(DISTINCT c.CustomerId)                                 AS customers_owned,
    COUNT(DISTINCT i.InvoiceId)                                  AS invoices,
    ROUND(COALESCE(SUM(i.Total), 0), 2)                         AS revenue,
    ROUND(100.0 * COALESCE(SUM(i.Total), 0)
          / (SELECT SUM(Total) FROM Invoice), 1)                  AS pct_of_total_revenue
FROM Employee AS e
LEFT JOIN Customer AS c ON c.SupportRepId = e.EmployeeId
LEFT JOIN Invoice AS i  ON i.CustomerId = c.CustomerId
GROUP BY e.EmployeeId
ORDER BY revenue DESC;
