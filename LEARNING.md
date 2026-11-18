# LEARNING.md - how this pipeline works, for a beginner

This file teaches the whole project in the order a beginner should read it.
Every code block is taken from the real files in this repo.

## 1. The shape of the project

```
data/   -> the input (one SQLite file)
sql/    -> the questions (one .sql file each)
src/    -> the machinery (download, run, dashboard)
output/ -> the answers (CSVs + one HTML file)
docs/   -> how to rebuild it yourself
```

Rule of thumb: `data/` and `sql/` are the truth; `output/` is generated and
can be deleted and rebuilt. That separation is what makes the project
reproducible.

## 2. Step one - get the data (`src/00_download.py`)

The script downloads a file over HTTPS and saves it. Three ideas matter:

- **Atomic write.** It downloads to `chinook.sqlite.part` and only renames to
  `chinook.sqlite` at the end. A failed download never leaves a half-written
  database behind.
- **Verify, don't trust.** After downloading it opens the file with SQLite and
  checks that all 11 expected tables exist and have enough rows. A truncated
  100 KB file would otherwise look "fine" until a query failed.
- **Idempotent.** Run it twice and the second run verifies and exits. This
  matters because you will run it many times while learning.

```python
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
```
The `?mode=ro` opens the database read-only. A buggy query can never mutate
the source data - a habit worth keeping for every analytics script.

## 3. What a relational database is

Chinook has 11 tables. A table is a spreadsheet with a fixed set of columns.
Tables connect through **keys**:

- `Artist.ArtistId` is the **primary key** (unique, never null).
- `Album.ArtistId` is a **foreign key** pointing at `Artist.ArtistId`.

The join `Album JOIN Artist ON Album.ArtistId = Artist.ArtistId` is how you
walk from "this album" to "who recorded it". There is no other way to get
there - the name is stored once, in `Artist`, and referenced everywhere else.
That is **normalisation**: store each fact once.

## 4. Reading SQL: the four clauses you will use 90% of the time

```sql
SELECT  column, aggregate(column)   -- what to show
FROM    table                       -- where it lives
JOIN    other ON ...                -- how tables connect
WHERE   condition                   -- filter rows
GROUP BY column                     -- collapse rows
HAVING  aggregate > x               -- filter after grouping
ORDER BY column DESC                -- sort
LIMIT   10                          -- keep the first 10
```

The order of execution is NOT the order written: `FROM/JOIN` first, then
`WHERE`, then `GROUP BY`, then `HAVING`, then `SELECT`, then `ORDER BY`,
then `LIMIT`. That is why you cannot use a column alias in `WHERE` but can in
`ORDER BY`.

## 5. JOIN types, with a Chinook example

- **INNER JOIN** - only rows that match on both sides. `Invoice JOIN Customer`
  drops any invoice with no customer (none exist here, but the rule holds).
- **LEFT JOIN** - keep every row on the left, even with no match. Query 08
  uses this so the five employees with no customers still appear with $0.
  If it used INNER JOIN they would vanish and the ranking would look like
  there are only three employees.
- **Self join** - a table joined to itself. `Employee.ReportsTo -> Employee.EmployeeId`
  gives the org chart.

## 6. GROUP BY and aggregates

```sql
SELECT Country, COUNT(*), SUM(Total)
FROM Invoice JOIN Customer USING (CustomerId)
GROUP BY Country;
```

`GROUP BY Country` collapses all 412 invoices into 24 rows, one per country.
`COUNT(*)` and `SUM(Total)` are computed inside each group. Any column in
`SELECT` that is not inside an aggregate must be in `GROUP BY` - SQLite is
lenient about this and will silently pick a value, which is a common bug.

## 7. Subqueries

A query inside a query. Query 01 uses them to keep KPIs independent:

```sql
SELECT
  (SELECT COUNT(*) FROM Invoice) AS total_invoices,
  (SELECT COUNT(*) FROM Customer) AS total_customers;
```

If you joined Invoice and Customer instead, the counts would multiply (every
invoice paired with every customer) and be wrong. Subqueries in the SELECT list
are the safest way to compute unrelated totals.

## 8. Window functions (`RANK`, `LAG`, running totals)

Normal aggregates collapse rows. Window functions compute over a set of rows
without collapsing:

```sql
RANK() OVER (ORDER BY SUM(i.Total) DESC)   -- position in the ranking
LAG(revenue) OVER (ORDER BY month)         -- previous row's value
SUM(revenue) OVER (ORDER BY month)         -- running total
```

Query 10 uses `LAG()` to get last month's revenue without a self-join. Query 02
uses `RANK()` instead of `ROW_NUMBER()` so the $45.62 tie stays visible -
`ROW_NUMBER()` would invent an ordering that does not exist.

## 9. CTEs (`WITH ... AS`)

A named subquery. Query 10 needs to aggregate first (month totals) and then
window over the result, which needs two different GROUP BY levels. A CTE
makes that readable:

```sql
WITH monthly AS (
    SELECT strftime('%Y-%m', InvoiceDate) AS month, SUM(Total) AS revenue
    FROM Invoice GROUP BY month
)
SELECT month, revenue, LAG(revenue) OVER (ORDER BY month) FROM monthly;
```

## 10. Date handling in SQLite

SQLite has no real date type. Chinook stores dates as text in
`'YYYY-MM-DD HH:MM:SS'` form, so `strftime('%Y-%m', InvoiceDate)` slices the
string into `'2021-01'`. If the column were a Unix timestamp you would use
`date(InvoiceDate, 'unixepoch')` instead.

## 11. The Python side (`src/run_queries.py`)

Three jobs: execute, format, persist.

- **Execute** with `conn.execute(sql_text)`. One statement per file; more than
  one raises an error on purpose.
- **Format** with a small aligned-table printer. No external library.
- **Persist** as CSV with `utf-8-sig` (BOM) so Excel on Windows reads the
  accented names (Helena Holý) correctly.
- **Fail loudly.** Any `sqlite3.Error` prints the file name, the error, and
  the full SQL, then exits with code 1. Silent failures are the enemy of a
  portfolio project.
- **Manifest.** `_manifest.json` records row counts and a DB hash so the
  dashboard and the README can never disagree about how many rows there are.

## 12. The dashboard (`src/dashboard.py`)

Plotly builds charts in Python; `fig.to_html()` turns each into a div. The
trick is embedding `plotly.js` once in the page header and telling every chart
`include_plotlyjs=False`, so the file is ~4.7 MB instead of ~33 MB.

Design points worth copying:

- One `style()` function applied to every figure, so 7 charts look like one
  document.
- Read-only data: the dashboard only reads CSVs, never the database. If a
  chart is wrong, the CSV (and the SQL behind it) is where you fix it.
- Computed insights: the "Key findings" bullets are calculated from the data,
  not typed by hand, so they cannot drift from the numbers.

## 13. How to check your own work

1. **Reconcile totals.** `SUM(Invoice.Total)` must equal
   `SUM(InvoiceLine.UnitPrice * Quantity)`. Here both are $2,328.60 with 0
   mismatches. If they differ, your join is wrong.
2. **Check row counts against the source.** 412 invoices, 59 customers, 2,240
   lines. If a query returns 412 customers, you grouped by the wrong column.
3. **Look for the zero rows.** Opera sold nothing, five employees own no
   customers. A query that silently drops them (INNER JOIN) is wrong even
   though it "runs".
4. **Spot the synthetic data.** Eleven months at exactly $37.62 is not a real
   business. Question suspiciously round patterns before quoting them.

## 14. Glossary

- **Primary key (PK):** the column that uniquely identifies a row.
- **Foreign key (FK):** a column pointing at another table's PK.
- **Normalisation:** storing each fact once.
- **Aggregate:** a function over many rows (COUNT, SUM, AVG, MIN, MAX).
- **Window function:** an aggregate-like calculation that does not collapse rows.
- **CTE:** a named subquery (`WITH name AS (...)`).
- **BOM:** byte-order mark; `utf-8-sig` writes one so Windows Excel reads
  UTF-8 correctly.
- **Idempotent:** safe to run more than once with the same result.
- **Read-only connection:** `mode=ro`, cannot mutate data.
- **Reconciliation:** proving two independent calculations agree.
