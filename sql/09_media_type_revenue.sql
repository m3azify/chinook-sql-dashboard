-- 09 - Which media format sells?
--
-- Revenue by file format (MPEG, AAC, video). The strategic question behind it:
-- is anyone still buying video, and is it worth keeping those SKUs?
--
-- WHY group by MediaType and not by file extension: the format is already a
-- labelled dimension in the database, so we use it directly. Parsing file
-- names would be slower and would disagree with the catalogue.

SELECT
    m.MediaTypeId                                                AS media_type_id,
    m.Name                                                       AS media_type,
    COUNT(DISTINCT t.TrackId)                                    AS tracks_in_catalog,
    COUNT(*)                                                     AS units_sold,
    ROUND(SUM(il.UnitPrice * il.Quantity), 2)                    AS revenue,
    ROUND(100.0 * SUM(il.UnitPrice * il.Quantity)
          / (SELECT SUM(UnitPrice * Quantity) FROM InvoiceLine), 1) AS pct_of_total_revenue
FROM MediaType AS m
JOIN Track AS t        ON t.MediaTypeId = m.MediaTypeId
JOIN InvoiceLine AS il ON il.TrackId = t.TrackId
GROUP BY m.MediaTypeId
ORDER BY revenue DESC;
