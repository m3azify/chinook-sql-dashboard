# How to rebuild this project without AI

This is the checklist a human follows to reproduce the project from scratch.
Every step has an expected result so you know you are on track.

## 0. Prerequisites

- Windows 11, Python 3.11+ installed, Git installed.
- A terminal (PowerShell).
- ~15 minutes and ~200 MB of disk (mostly the venv).

Check: `python --version` prints 3.11 or newer.

## 1. Scaffold

```powershell
mkdir C:\Users\YOURNAME\freelance-portfolio\proj2
cd C:\Users\YOURNAME\freelance-portfolio\proj2
mkdir data, sql, src, output, docs
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install plotly==7.1.0
```

Expected: `.\.venv\Scripts\python.exe -c "import plotly; print(plotly.__version__)"` prints `7.1.0`.

## 2. Download the data

Create `src\00_download.py` (see the repo) and run:

```powershell
.\.venv\Scripts\python.exe src\00_download.py
```

Expected output ends with `verified: 11 tables, Invoice=412, Track=3503` and a
table list. If you see `urllib failed`, the script falls back to `git clone`
automatically.

Checkpoint: `data\chinook.sqlite` exists and is ~984 KB.

## 3. Write the schema query

Create `sql\00_schema.sql`. The query reads `sqlite_master` and
`pragma_table_info()` / `pragma_foreign_key_list()`. Run nothing yet - the
runner executes all files at once.

## 4. Write the ten business queries, one file each

Create `sql\01_kpis.sql` ... `sql\10_sales_growth.sql`. Rules:

- One statement per file (the runner enforces this).
- Start each file with a `--` line stating the question in plain English.
- Explain WHY in comments, not just what.
- Use CTEs (`WITH`) when you need two levels of aggregation.
- Use `LEFT JOIN` when dropping zero-row groups would be wrong (employees,
  genres).
- Use `RANK()` when ties matter, `ROW_NUMBER()` only when they do not.
- Use `LAG()` for month-over-month instead of a self-join.

After writing each file, test it alone:

```powershell
.\.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('data/chinook.sqlite'); print(c.execute(open('sql/01_kpis.sql').read()).fetchall())"
```

Checkpoint: every file runs and returns the expected shape.

## 5. Build the runner

Create `src\run_queries.py`. It must:

- Find `*.sql` in `sql/`, sorted.
- Execute each, print an aligned table, write `output\<name>.csv` as UTF-8-BOM.
- On `sqlite3.Error`, print the file, the error and the SQL, then exit 1.
- Write `output\_manifest.json` with row counts.

Run:

```powershell
.\.venv\Scripts\python.exe src\run_queries.py
```

Expected: `OK: 11 queries, 292 rows total`. Eleven CSVs in `output\`.

## 6. Build the dashboard

Create `src\dashboard.py`. Steps inside it:

1. Read each CSV with `csv.DictReader` (encoding `utf-8-sig`).
2. Build 7 figures with `plotly.graph_objects`.
3. Apply one `style()` function to all of them.
4. Embed `plotly.offline.get_plotlyjs()` once in the HTML head.
5. Write `output\chinook_dashboard.html`.

Run:

```powershell
.\.venv\Scripts\python.exe src\dashboard.py
start output\chinook_dashboard.html
```

Expected: a 4.66 MB HTML file that opens in the browser with 6 KPI cards,
8 charts and a top-10 customer table, and works with Wi-Fi off.

## 7. Write the docs

- `README.md`: what it is, schema in text, ten questions with answers, how to
  run, design decisions, caveats.
- `LEARNING.md`: teach the pipeline (this file's content).
- `docs\POWERBI_GUIDE.md`: rebuild the dashboard in Power BI Desktop.

Fill in real numbers from `output\*.csv`, never guess.

## 8. Git

```powershell
git init
git config user.name "YOUR NAME"
git config user.email "you@example.com"
git add -A
git commit -m "Build Chinook SQL + BI portfolio project"
```

Checkpoint: `git log --oneline` shows one commit and `git status` is clean.

## 9. Verify end to end

1. Delete `output\` entirely.
2. Run `python src\run_queries.py` then `python src\dashboard.py`.
3. Confirm 11 CSVs + 1 HTML reappear with the same row counts.
4. Open the HTML offline (disconnect Wi-Fi) and confirm charts render.

If step 3 or 4 fails, restore from your last commit and re-read the error.

## Common pitfalls

- **Accented names look like `Helena Hol?`.** Console code page issue. The
  runner calls `sys.stdout.reconfigure(encoding="utf-8")`; if it still breaks,
  run `chcp 65001` first.
- **`Activate.ps1` is blocked.** Use `.\.venv\Scripts\python.exe` directly.
- **PowerShell splits multi-line `python -c`.** Pipe a here-string instead:
  `@' ... '@ | python -`.
- **Query returns 0 rows.** Check whether an INNER JOIN dropped them; switch
  to LEFT JOIN if needed.
- **Numbers disagree between dashboard and README.** Re-run the runner; the
  README numbers must come from `output\*.csv`, not from memory.
- **HTML is 33 MB.** You forgot `include_plotlyjs=False` on the charts.
