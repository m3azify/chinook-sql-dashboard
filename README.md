# Chinook SQL + BI portfolio project

A small, end-to-end data project: a real relational database (SQLite), ten
business questions answered in real `.sql` files, and an offline HTML dashboard
built from the results. Built to prove SQL + BI skills on a dataset a reviewer
can reproduce in under a minute.

**Author:** Moaz - final-year CS & Data Science student, Alexandria, Egypt.
**Stack:** Python 3.15.2, SQLite (stdlib), plotly 7.1.0. No paid services, no API keys.

## What it is

The [Chinook](https://github.com/lerocha/chinook-database) sample database is a
digital music store (artists, albums, tracks, customers, invoices, employees).
It ships as a single SQLite file, which makes it a perfect stand-in for the
kind of "small business with a messy relational database" that freelance clients
actually have.

The project answers ten questions a store owner would ask, in SQL, and turns
the answers into a dashboard that opens in a browser with no server.

## Numbers at a glance

| Metric | Value |
|---|---|
| Tables | 11 (64 columns, 11 foreign keys) |
| Customers | 59 (all have purchased; 0 inactive) |
| Invoices | 412 (Jan 2021 - Dec 2025) |
| Invoice lines | 2,240 (2,240 units; 5.44 per invoice) |
| Revenue | $2,328.60 |
| Avg. order value | $5.65 |
| Distinct tracks sold | 1,984 of 3,503 (56.6% of catalogue) |
| Countries | 24 |
| Artists in catalogue | 275 |

Revenue reconciles exactly: `SUM(Invoice.Total)` = `SUM(InvoiceLine.UnitPrice *
InvoiceLine.Quantity)` = $2,328.60, with 0 mismatches.

## Schema (text)

```
Artist  1--*  Album  1--*  Track  *--1  Genre
                                 *--1  MediaType
                                 *--*  Playlist   (via PlaylistTrack)
Customer 1--*  Invoice  1--*  InvoiceLine  *--1  Track
Employee  1--*  Customer   (SupportRepId = the rep who owns the account)
Employee  *--1  Employee   (ReportsTo = manager)
```

Every table, column, type and foreign key is also in `sql/00_schema.sql` and
`output/00_schema.csv`, generated straight from `sqlite_master` so it can never
go stale.

## The ten questions and their answers

1. **Headline KPIs** (`01_kpis.sql`) - 412 invoices, 59 customers, $2,328.60
   revenue, $5.65 AOV, 2,240 units, 1,984 of 3,503 tracks sold (56.6%).
   *0 customers have never purchased.*
2. **Top customers** (`02_top_customers.sql`, 10 rows) - Helena Holý leads at
   $49.62; the top 10 account for 19.4% of revenue. Ranks use `RANK()` so the
   $45.62 tie between Ladislav Kovács and Hugh O'Reilly stays visible.
3. **Revenue by country** (`03_revenue_by_country.sql`, 24 rows) - USA $523.06
   (22.5%), Canada $303.96 (13.1%), France $195.10 (8.4%), Brazil $190.10
   (8.2%), Germany $156.48 (6.7%). Top 5 = 58.8%.
4. **Top artists** (`04_top_artists.sql`, 10 rows) - Iron Maiden $138.60, U2
   $105.93, Metallica $90.09, Led Zeppelin $86.13, Lost $81.59. Top 10 = 31.0%.
5. **Monthly revenue** (`05_monthly_revenue.sql`, 60 rows) - $35.64 in Jan 2021
   rising to a $52.62 peak in Jan 2022; full-year revenue 2021 $449.46,
   2022 $481.45, 2023 $469.58, 2024 $477.53, 2025 $450.58.
6. **Genre performance** (`06_genre_performance.sql`, 25 rows) - Rock $826.65
   (35.5%), Latin $382.14 (16.4%), Metal $261.36 (11.2%), Alternative & Punk
   $241.56 (10.4%). The top four genres = 73.5%. Opera sold nothing.
7. **Avg. order value by market** (`07_avg_order_value.sql`, 25 rows) - global
   $5.65; Chile highest at $6.66, Argentina lowest at $5.37. Markets with
   fewer than 5 orders are excluded so one big invoice cannot fake a trend.
8. **Employee sales ranking** (`08_employee_sales.sql`, 8 rows) - Jane Peacock
   $833.04, Margaret Park $775.40, Steve Johnson $720.16. The other five
   employees (managers, IT) own no customers and correctly show $0.
9. **Media type revenue** (`09_media_type_revenue.sql`, 5 rows) - MPEG audio
   $1,956.24 (84.0%), Protected MPEG-4 video $220.89 (9.5%), Protected AAC
   $144.54 (6.2%).
10. **Revenue growth** (`10_sales_growth.sql`, 60 rows) - month-over-month change
    via `LAG()`, plus a running total. Largest single-month jump: +58.3% in
    Dec 2023; deepest drop: -36.8% in Nov 2023.

## How to run

```powershell
cd C:\Users\Moaz\freelance-portfolio\proj2
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # or: .\.venv\Scripts\python.exe ...
pip install -r requirements.txt
python src\00_download.py            # downloads + verifies chinook.sqlite
python src\run_queries.py            # 11 queries -> output\*.csv
python src\dashboard.py              # -> output\chinook_dashboard.html
start output\chinook_dashboard.html  # open in the default browser
```

If PowerShell blocks the activation script, run the scripts directly with
`.\.venv\Scripts\python.exe src\run_queries.py` instead - they only need the
interpreter, not an activated shell.

## Project layout

```
proj2/
  data/chinook.sqlite          # downloaded, verified, sha256 recorded
  sql/00_schema.sql .. 10_sales_growth.sql
  src/00_download.py  run_queries.py  dashboard.py
  output/*.csv  _manifest.json  chinook_dashboard.html
  docs/HOW_TO_REBUILD.md  POWERBI_GUIDE.md
  README.md  LEARNING.md  requirements.txt
```

## Design decisions (and their trade-offs)

- **SQLite, not a server.** A single file, zero setup, opens in DB Browser for
  SQLite for free. Trade-off: no concurrent writers, which does not matter for
  an analytics workload.
- **SQL in `.sql` files, not Python strings.** The queries are the deliverable;
  Python only executes and persists. A reviewer can paste any file into DBeaver
  and get the same result.
- **CSV as the hand-off between SQL and BI.** Power BI, Tableau and Excel all
  read CSV natively, so the same files feed the Python dashboard and a Power BI
  rebuild (see `docs/POWERBI_GUIDE.md`).
- **Offline HTML.** plotly.js is embedded (~4.7 MB) so the file works on a
  plane. Trade-off: large file; acceptable for a portfolio artifact.
- **stdlib only for the pipeline.** `sqlite3` + `csv` + `json`. Fewer moving
  parts to explain line by line, and no pandas version risk on Python 3.15.
- **Read-only database connection** (`mode=ro`) so a buggy query can never
  mutate the source data.

## Known caveats (read before quoting the numbers)

- Chinook is **synthetic**: Jan-Dec 2021 repeats the same $37.62 for eleven
  straight months. Month-over-month growth is therefore noisy and should be
  read as "the data is flat", not as a real trend. Full-year figures (2021-2024)
  are the honest comparison.
- 2025 is **partial** (through Dec 22): 80 invoices vs 83 in other years, so
  its $450.58 is not comparable to a full year.
- Revenue is **not profit**: the dataset has no cost column.
- Employee credit uses `Customer.SupportRepId` because there is no deal/owner
  history. Managers and IT staff correctly show $0.
- Top-artist and top-customer shares are revenue shares of total store revenue.

## Data source and license

Chinook sample database by Luis Rocha (`lerocha/chinook-database`), downloaded
from the repository's `master` branch. No license file or SPDX identifier is
published in that repository; it is a well-known free sample dataset used for
learning and demos. `src/00_download.py` records the SHA-256 of the downloaded
file (`7651ba378ac2fcd0dfc3c66fb101f7a7eed3ba39a612ec642b96e20702061f15`)
so a reviewer can confirm they have the exact file.

## Credits

Built by Moaz as a portfolio piece. SQL and Python written to be explainable
line by line - see `LEARNING.md`.
