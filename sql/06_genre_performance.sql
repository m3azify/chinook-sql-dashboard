-- 06 - Which genres actually sell?
--
-- Revenue, units and track coverage per genre. Tells a store owner what to
-- stock more of and what to stop buying.
--
-- WHY COALESCE(SUM(Quantity), 0): a genre with zero sales still appears in
-- the list (with 0 revenue) so the owner sees the dead categories, not just
-- the winners. Every genre in Chinook happens to have at least one sale, but
-- the query is written to survive a dataset where that is not true.
--
-- WHY count distinct tracks sold: "tracks_in_genre" alone would hide that
-- most of the catalogue never sells. See sql/01 for the overall figure.

SELECT
    g.GenreId                                                    AS genre_id,
    g.Name                                                       AS genre,
    COUNT(DISTINCT t.TrackId)                                    AS tracks_in_genre,
    COUNT(DISTINCT CASE WHEN il.TrackId IS NOT NULL THEN t.TrackId END) AS tracks_sold,
    COALESCE(SUM(il.Quantity), 0)                                AS units_sold,
    ROUND(COALESCE(SUM(il.UnitPrice * il.Quantity), 0), 2)      AS revenue,
    ROUND(100.0 * COALESCE(SUM(il.UnitPrice * il.Quantity), 0)
          / (SELECT SUM(UnitPrice * Quantity) FROM InvoiceLine), 1) AS pct_of_total_revenue
FROM Genre AS g
LEFT JOIN Track AS t       ON t.GenreId = g.GenreId
LEFT JOIN InvoiceLine AS il ON il.TrackId = t.TrackId
GROUP BY g.GenreId
ORDER BY revenue DESC;
