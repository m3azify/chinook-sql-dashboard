# Rebuilding the dashboard in Power BI Desktop (free)

Power BI Desktop is free on Windows (Microsoft Store or direct download).
This guide rebuilds the same dashboard from the CSVs that `run_queries.py`
produces, so the SQL stays the single source of truth.

## 1. Prerequisites

- Power BI Desktop installed (latest, free).
- The project's `output\` folder populated: run `python src\run_queries.py`.
- Optional: a Power BI account only if you want to publish to the web. Desktop
  alone is free and is enough for this project.

## 2. Load the data

1. Open Power BI Desktop -> **Get Data** -> **Text/CSV**.
2. Load these files one at a time (or use **Get Data -> Folder** pointed at
   `output\` and filter to `*.csv`):
   - `01_kpis.csv`
   - `02_top_customers.csv`
   - `03_revenue_by_country.csv`
   - `04_top_artists.csv`
   - `05_monthly_revenue.csv`
   - `06_genre_performance.csv`
   - `07_avg_order_value.csv`
   - `08_employee_sales.csv`
   - `09_media_type_revenue.csv`
   - `10_sales_growth.csv`
3. In the preview dialog, check the delimiter is **Comma** and encoding is
   **UTF-8** (accented names). Click **Load** for the simple ones and
   **Transform Data** for `07_avg_order_value.csv` to remove the `All markets`
   row if you want a pure country chart (keep it for the KPI card).
4. In Power Query, set data types: revenue columns -> **Decimal Number**,
   counts -> **Whole Number**, `month` -> **Text** (do not let Power BI turn it
   into a date, it will group by day).

## 3. A note on the data model

Each CSV is already aggregated, so no relationships are required and the
report is a set of independent visuals. If you want a relational model instead,
connect Power BI to the SQLite file via the **SQLite ODBC driver** (free,
separate download) and rebuild the queries as DAX measures - that is the
"real" BI workflow but is out of scope for this guide.

## 4. KPI cards (top of the page)

Insert **Card** visuals. For each, drag the field from `01_kpis`:

- Total revenue -> `total_revenue` (format: Currency, 2 decimals)
- Invoices -> `total_invoices` (Whole number)
- Avg. order value -> `avg_order_value` (Currency)
- Customers -> `total_customers`
- Units sold -> `units_sold`
- Catalog coverage -> `pct_catalog_sold` (Percentage, or append "%")

Arrange in a 6-column row. Title the page "Chinook store - sales dashboard".

## 5. Charts (match the HTML dashboard)

| Visual | Source table | Fields |
|---|---|---|
| Line chart | `05_monthly_revenue` | Axis: `month`, Values: `revenue` |
| Bar chart (horizontal) | `03_revenue_by_country` | Axis: `country`, Values: `revenue`, Top N = 10 by revenue |
| Donut chart | `06_genre_performance` | Legend: `genre`, Values: `revenue` (top 8 + Other) |
| Bar chart (horizontal) | `04_top_artists` | Axis: `artist_name`, Values: `revenue`, Top N = 10 |
| Bar chart (vertical) | `08_employee_sales` | Axis: `employee_name`, Values: `revenue` |
| Donut chart | `09_media_type_revenue` | Legend: `media_type`, Values: `revenue` |
| Bar chart (horizontal) | `07_avg_order_value` | Axis: `market`, Values: `avg_order_value`, filter `market <> "All markets"` |

Formatting tips:

- Turn on data labels on every bar and donut.
- Set currency format on revenue axes; 0 or 1 decimal on AOV.
- Use a single accent colour (teal `#0F766E`) for bars and a muted grey
  (`#CBD5E1`) for the zero-revenue employees, matching the HTML dashboard.
- Add a constant line on the AOV chart at the global value (5.65).

## 6. Top-10 customers table

Insert a **Table** visual from `02_top_customers`: columns `revenue_rank`,
`customer_name`, `country`, `orders`, `lifetime_revenue`,
`pct_of_total_revenue`. Sort by `revenue_rank` ascending. Format
`lifetime_revenue` as currency.

## 7. Slicers (optional, makes it interactive)

Add a slicer on `03_revenue_by_country[country]` and one on
`05_monthly_revenue[month]`. Wire them to all visuals so a reviewer can
drill into one country or one month.

## 8. Insights text box

Insert a **Text box** with the six findings from the HTML dashboard's
"Key findings" list, or use a **Smart narrative** visual pointed at the
revenue and country visuals to auto-generate sentences.

## 9. Save and share

- Save as `output\chinook_dashboard.pbix`.
- To publish: **Publish** requires a work or school Microsoft account. With a
  personal account you can still share the `.pbix` file directly.
- To export a PDF for a client: **File -> Export -> Export to PDF**.

## 10. Keeping it in sync

When the data changes, re-run `python src\run_queries.py`, then in Power BI
click **Refresh** (or **Transform Data -> Refresh Preview**). The CSVs are
the contract between the SQL layer and the BI layer - never edit them by hand.
