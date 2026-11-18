-- 00 - What does the database look like?
--
-- This is not a business question. It is a map of the warehouse: every table,
-- every column, its data type, and the foreign-key edges that connect tables.
-- Run it first so you know what you are allowed to join on. The output becomes
-- output/00_schema.csv and the "schema in text" section of README.md.
--
-- WHY we read sqlite_master instead of hard-coding: the database is a
-- third-party file. Reading the catalogue means the file proves its own
-- structure and this query never goes stale if a column is added.
--
-- Relationships (for humans):
--   Artist 1--* Album 1--* Track *--1 Genre
--                                 *--1 MediaType
--   Track *--* Playlist (via PlaylistTrack)
--   Customer 1--* Invoice 1--* InvoiceLine *--1 Track
--   Employee 1--* Customer (SupportRepId = the rep who owns the account)
--   Employee *--1 Employee (ReportsTo = manager)

WITH tables AS (
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%'          -- hide SQLite's own bookkeeping tables
)
SELECT t.name                                              AS table_name,
       p.cid + 1                                           AS column_no,
       p.name                                              AS column_name,
       p.type                                              AS data_type,
       CASE p.[notnull] WHEN 1 THEN 'required' ELSE 'optional' END AS nullability,
       CASE p.pk WHEN 1 THEN 'PK' ELSE '' END              AS key_type,
       COALESCE(
         (SELECT group_concat('-> ' || fk.[table] || '.' || fk.[to], ', ')
          FROM pragma_foreign_key_list(t.name) AS fk
          WHERE fk.[from] = p.name),
         '')                                               AS foreign_key
FROM tables AS t
JOIN pragma_table_info(t.name) AS p
ORDER BY t.name, p.cid;
