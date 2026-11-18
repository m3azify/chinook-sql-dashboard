-- 04 - Which artists make me the most money?
--
-- Top 10 artists by revenue. The join path is the interesting part: an artist
-- has albums, albums have tracks, tracks appear on invoice lines. Four tables
-- to reach the money.
--
-- WHY sum UnitPrice * Quantity from InvoiceLine instead of Invoice.Total:
-- Invoice.Total is the whole order. Splitting by artist needs the line-level
-- price, which is what the customer actually paid for that track.

SELECT
    RANK() OVER (ORDER BY SUM(il.UnitPrice * il.Quantity) DESC)  AS revenue_rank,
    ar.ArtistId                                                  AS artist_id,
    ar.Name                                                      AS artist_name,
    COUNT(DISTINCT al.AlbumId)                                   AS albums_in_catalog,
    COUNT(DISTINCT t.TrackId)                                    AS tracks_sold,
    SUM(il.Quantity)                                             AS units_sold,
    ROUND(SUM(il.UnitPrice * il.Quantity), 2)                    AS revenue,
    ROUND(100.0 * SUM(il.UnitPrice * il.Quantity)
          / (SELECT SUM(UnitPrice * Quantity) FROM InvoiceLine), 2) AS pct_of_total_revenue
FROM Artist AS ar
JOIN Album AS al  ON al.ArtistId = ar.ArtistId
JOIN Track AS t   ON t.AlbumId = al.AlbumId
JOIN InvoiceLine AS il ON il.TrackId = t.TrackId
GROUP BY ar.ArtistId
ORDER BY revenue DESC
LIMIT 10;
