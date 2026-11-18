"""Build an offline HTML dashboard from the query CSVs.

WHY a separate build step: the dashboard is a view of the data, not the data
itself. Re-running run_queries.py updates the CSVs; re-running this script
rebuilds the HTML. Keeping them separate means a broken chart never corrupts
the numbers, and a broken query never corrupts the charts.

Offline mode: plotly.js is embedded in the file, so the dashboard opens in any
browser with no server and no internet connection.

Run from the project root:  python src/dashboard.py
"""
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import plotly
    from plotly import graph_objects as go
    from plotly.offline import get_plotlyjs
except ImportError:
    print("plotly is not installed. Activate the virtualenv and run:", file=sys.stderr)
    print("  .venv\\Scripts\\python.exe -m pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"
MANIFEST_PATH = OUTPUT_DIR / "_manifest.json"
DASHBOARD_PATH = OUTPUT_DIR / "chinook_dashboard.html"

ACCENT = "#0f766e"
ACCENT_LIGHT = "#5eead4"
INK = "#111827"
MUTED = "#6b7280"
GRID = "#f3f4f6"
PIE_PALETTE = ["#0f766e", "#14b8a6", "#2dd4bf", "#f59e0b", "#fb7185",
               "#6366f1", "#84cc16", "#94a3b8", "#f97316"]


def read_csv(name: str) -> list[dict]:
    path = OUTPUT_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run `python src/run_queries.py` first.")
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def money(x) -> str:
    return f"${float(x):,.2f}"


def style(fig: go.Figure, title: str, height: int = 360) -> go.Figure:
    """Apply one consistent theme to every chart so the dashboard reads as a
    single document rather than 7 unrelated plots."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=INK, family="Segoe UI"),
                   x=0, xanchor="left", pad=dict(b=6)),
        height=height,
        margin=dict(l=12, r=12, t=46, b=12),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Segoe UI, system-ui, sans-serif", size=12, color="#374151"),
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left",
                    x=1.02, font=dict(size=11, color=MUTED), title_text=""),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, tickfont=dict(size=11, color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(size=11, color=MUTED))
    return fig


def fig_to_div(fig: go.Figure) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False,
                       config={"displayModeBar": False, "responsive": True})


# ---------- charts ----------

def chart_monthly(rows: list[dict]) -> str:
    months = [r["month"] for r in rows]
    revenue = [float(r["revenue"]) for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=revenue, mode="lines+markers", name="Revenue",
        line=dict(color=ACCENT, width=2.5),
        marker=dict(size=4, color=ACCENT),
        fill="tozeroy", fillcolor="rgba(15,118,110,0.08)",
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>",
    ))
    style(fig, "Revenue over time (monthly)", height=340)
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    fig.update_xaxes(tickangle=-45, nticks=12)
    fig.update_layout(showlegend=False)
    return fig_to_div(fig)


def chart_country(rows: list[dict]) -> str:
    top = sorted(rows, key=lambda r: float(r["revenue"]), reverse=True)[:10]
    top.reverse()  # so the largest sits at the top of a horizontal bar
    fig = go.Figure(go.Bar(
        y=[r["country"] for r in top],
        x=[float(r["revenue"]) for r in top],
        orientation="h",
        marker=dict(color=ACCENT, line=dict(width=0)),
        text=[f"${float(r['revenue']):,.0f}" for r in top],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>",
    ))
    style(fig, "Revenue by country (top 10)", height=360)
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(showlegend=False, margin=dict(l=12, r=40, t=46, b=12))
    return fig_to_div(fig)


def chart_genre(rows: list[dict]) -> str:
    top = sorted(rows, key=lambda r: float(r["revenue"]), reverse=True)[:8]
    other_rev = sum(float(r["revenue"]) for r in rows) - sum(float(r["revenue"]) for r in top)
    labels = ([r["genre"] for r in top] +
              ([f"Other ({len(rows) - len(top)} genres)"] if other_rev > 0 else []))
    values = [float(r["revenue"]) for r in top] + ([other_rev] if other_rev > 0 else [])
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.45,
        marker=dict(colors=PIE_PALETTE, line=dict(color="white", width=1.5)),
        textinfo="label+percent", textposition="outside",
        hovertemplate="<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>%{percent}<extra></extra>",
    ))
    style(fig, "Revenue by genre", height=400)
    fig.update_layout(showlegend=False)
    return fig_to_div(fig)


def chart_artists(rows: list[dict]) -> str:
    top = sorted(rows, key=lambda r: float(r["revenue"]), reverse=True)[:10]
    top.reverse()
    fig = go.Figure(go.Bar(
        y=[r["artist_name"] for r in top],
        x=[float(r["revenue"]) for r in top],
        orientation="h",
        marker=dict(color=ACCENT_LIGHT, line=dict(width=0)),
        text=[f"${float(r['revenue']):,.0f}" for r in top],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>",
    ))
    style(fig, "Top 10 artists by revenue", height=380)
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(showlegend=False, margin=dict(l=12, r=40, t=46, b=12))
    return fig_to_div(fig)


def chart_employees(rows: list[dict]) -> str:
    # Sort so the three sellers lead, then the rest of the org chart.
    sellers = [r for r in rows if float(r["revenue"]) > 0]
    others = [r for r in rows if float(r["revenue"]) == 0]
    ordered = sellers + others
    fig = go.Figure(go.Bar(
        x=[r["employee_name"].split()[0] + " " + r["employee_name"].split()[-1]
           for r in ordered],
        y=[float(r["revenue"]) for r in ordered],
        marker=dict(color=[ACCENT if float(r["revenue"]) > 0 else "#cbd5e1"
                          for r in ordered],
                    line=dict(width=0)),
        text=[money(r["revenue"]) for r in ordered],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{customdata}<br>Revenue: $%{y:,.2f}<extra></extra>",
        customdata=[r["title"] for r in ordered],
    ))
    style(fig, "Revenue by sales rep", height=340)
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(showlegend=False, xaxis_tickangle=-20)
    return fig_to_div(fig)


def chart_media(rows: list[dict]) -> str:
    fig = go.Figure(go.Pie(
        labels=[r["media_type"] for r in rows],
        values=[float(r["revenue"]) for r in rows],
        hole=0.45,
        marker=dict(colors=PIE_PALETTE, line=dict(color="white", width=1.5)),
        textinfo="label+percent", textposition="outside",
        hovertemplate="<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>%{percent}<extra></extra>",
    ))
    style(fig, "Revenue by media type", height=380)
    fig.update_layout(showlegend=False)
    return fig_to_div(fig)


def chart_aov(rows: list[dict]) -> str:
    # Exclude the "All markets" summary row; sort by AOV descending, top 10.
    data = [r for r in rows if r["market"] != "All markets"]
    data.sort(key=lambda r: float(r["avg_order_value"]), reverse=True)
    data = data[:10]
    data.reverse()
    global_aov = next(float(r["avg_order_value"]) for r in rows if r["market"] == "All markets")
    fig = go.Figure(go.Bar(
        y=[r["market"] for r in data],
        x=[float(r["avg_order_value"]) for r in data],
        orientation="h",
        marker=dict(color="#6366f1", line=dict(width=0)),
        text=[f"${float(r['avg_order_value']):.2f}" for r in data],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>AOV: $%{x:.2f}<br>Orders: %{customdata}<extra></extra>",
        customdata=[int(r["orders"]) for r in data],
    ))
    fig.add_vline(x=global_aov, line_dash="dash", line_color=MUTED,
                  annotation_text=f"global AOV ${global_aov:.2f}",
                  annotation_position="top right",
                  annotation_font=dict(size=10, color=MUTED))
    style(fig, "Average order value by market (min. 5 orders)", height=380)
    fig.update_xaxes(tickprefix="$", tickformat=".2f")
    fig.update_layout(showlegend=False, margin=dict(l=12, r=40, t=46, b=12))
    return fig_to_div(fig)


def chart_growth(rows: list[dict]) -> str:
    # Month-over-month revenue change. The first month has no predecessor and
    # is dropped (NULL growth is not a zero change). Bars are coloured by sign
    # so the eye catches the swings the flat series otherwise hides.
    data = [r for r in rows if r["growth_pct"] not in ("", "None")]
    colors = [ACCENT if float(r["growth_pct"]) >= 0 else "#dc2626" for r in data]
    fig = go.Figure(go.Bar(
        x=[r["month"] for r in data],
        y=[float(r["growth_pct"]) for r in data],
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate=("<b>%{x}</b><br>Growth: %{y:+.1f}%<br>"
                      "Revenue: $%{customdata:,.2f}<extra></extra>"),
        customdata=[float(r["revenue"]) for r in data],
    ))
    fig.add_hline(y=0, line_width=1, line_color="#cbd5e1")
    style(fig, "Month-over-month revenue growth", height=260)
    fig.update_yaxes(ticksuffix="%", tickformat=".0f")
    fig.update_xaxes(tickangle=-45, nticks=12)
    fig.update_layout(showlegend=False, bargap=0.2)
    return fig_to_div(fig)


def build_kpi_cards(kpi: dict) -> str:
    first = datetime.strptime(kpi["first_invoice_date"][:10], "%Y-%m-%d")
    last = datetime.strptime(kpi["last_invoice_date"][:10], "%Y-%m-%d")
    no_invoices = int(kpi["customers_with_no_invoices"])
    customers_sub = ("all have purchased" if no_invoices == 0
                     else f"{no_invoices} never purchased")
    cards = [
        ("Total revenue", money(kpi["total_revenue"]),
         f"across {int(kpi['total_invoices']):,} invoices"),
        ("Invoices", f"{int(kpi['total_invoices']):,}",
         f"{first:%b %Y} - {last:%b %Y}"),
        ("Avg. order value", money(kpi["avg_order_value"]), "per invoice"),
        ("Customers", f"{int(kpi['total_customers']):,}", customers_sub),
        ("Units sold", f"{int(kpi['units_sold']):,}", "track purchases"),
        ("Catalog coverage", f"{kpi['pct_catalog_sold']}%",
         f"{int(kpi['distinct_tracks_sold']):,} of "
         f"{int(kpi['tracks_in_catalog']):,} tracks sold"),
    ]
    html = []
    for label, value, sub in cards:
        html.append(f"""
        <div class="kpi">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-sub">{sub}</div>
        </div>""")
    return "\n".join(html)


def build_insights(kpi: dict, country_rows, genre_rows, monthly_rows, emp_rows) -> str:
    top_country = max(country_rows, key=lambda r: float(r["revenue"]))
    top_genre = max(genre_rows, key=lambda r: float(r["revenue"]))
    top_artist_row = None
    # artist file is not passed; read it here for the insight
    artist_rows = read_csv("04_top_artists.csv")
    top_artist = max(artist_rows, key=lambda r: float(r["revenue"]))
    sellers = [r for r in emp_rows if float(r["revenue"]) > 0]
    rev_2021 = sum(float(r["revenue"]) for r in monthly_rows
                   if r["month"].startswith("2021"))
    rev_2024 = sum(float(r["revenue"]) for r in monthly_rows
                   if r["month"].startswith("2024"))
    growth = (rev_2024 - rev_2021) / rev_2021 * 100
    bullets = [
        f"<b>{top_country['country']}</b> is the largest market at "
        f"{money(top_country['revenue'])} ({top_country['pct_of_total_revenue']}% of revenue).",
        f"<b>{top_genre['genre']}</b> dominates the catalogue at "
        f"{top_genre['pct_of_total_revenue']}% of revenue; "
        f"{top_genre['tracks_sold']} of {top_genre['tracks_in_genre']} tracks sell.",
        f"<b>{top_artist['artist_name']}</b> is the top artist at "
        f"{money(top_artist['revenue'])} ({top_artist['pct_of_total_revenue']}% of revenue).",
        f"Only <b>{len(sellers)} of {len(emp_rows)} employees</b> own customers; "
        f"they account for 100% of revenue.",
        f"Full-year revenue moved from {money(rev_2021)} (2021) to {money(rev_2024)} (2024), "
        f"a {growth:+.1f}% change; the series is otherwise flat month to month.",
        f"{kpi['pct_catalog_sold']}% of the {int(kpi['tracks_in_catalog']):,}-track catalogue "
        f"({int(kpi['distinct_tracks_sold']):,} tracks) has ever sold.",
    ]
    return "\n".join(f"<li>{b}</li>" for b in bullets)


def build_top_customers_table(rows: list[dict]) -> str:
    body = []
    for r in rows:
        body.append(
            f"<tr><td class='num'>{r['revenue_rank']}</td>"
            f"<td>{r['customer_name']}</td>"
            f"<td>{r['country']}</td>"
            f"<td class='num'>{r['orders']}</td>"
            f"<td class='num'>{money(r['lifetime_revenue'])}</td>"
            f"<td class='num'>{r['pct_of_total_revenue']}%</td></tr>")
    return f"""
    <table class="data-table">
      <thead><tr>
        <th>#</th><th>Customer</th><th>Country</th>
        <th>Orders</th><th>Lifetime revenue</th><th>Share</th>
      </tr></thead>
      <tbody>{''.join(body)}</tbody>
    </table>"""


def main() -> int:
    # Ensure every required CSV exists before we start building.
    for name in ("01_kpis.csv", "02_top_customers.csv", "03_revenue_by_country.csv",
                 "04_top_artists.csv", "05_monthly_revenue.csv",
                 "06_genre_performance.csv", "07_avg_order_value.csv",
                 "08_employee_sales.csv", "09_media_type_revenue.csv",
                 "10_sales_growth.csv"):
        if not (OUTPUT_DIR / name).exists():
            print(f"Missing {name}. Run `python src/run_queries.py` first.",
                  file=sys.stderr)
            return 1

    kpi_rows = read_csv("01_kpis.csv")
    kpi = kpi_rows[0]
    customers = read_csv("02_top_customers.csv")
    countries = read_csv("03_revenue_by_country.csv")
    artists = read_csv("04_top_artists.csv")
    monthly = read_csv("05_monthly_revenue.csv")
    genres = read_csv("06_genre_performance.csv")
    aov = read_csv("07_avg_order_value.csv")
    employees = read_csv("08_employee_sales.csv")
    media = read_csv("09_media_type_revenue.csv")
    growth = read_csv("10_sales_growth.csv")

    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    charts = {
        "monthly": chart_monthly(monthly),
        "country": chart_country(countries),
        "genre": chart_genre(genres),
        "artists": chart_artists(artists),
        "employees": chart_employees(employees),
        "media": chart_media(media),
        "aov": chart_aov(aov),
        "growth": chart_growth(growth),
    }

    kpi_cards = build_kpi_cards(kpi)
    insights = build_insights(kpi, countries, genres, monthly, employees)
    top_customers_table = build_top_customers_table(customers)

    plotly_js = get_plotlyjs()
    generated = manifest.get("generated_at", "unknown")
    query_count = manifest.get("query_count", 11)
    total_rows = manifest.get("total_rows", 292)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chinook store - sales dashboard</title>
<style>
  :root {{
    --ink: {INK}; --muted: {MUTED}; --accent: {ACCENT};
    --bg: #f1f5f9; --card: #ffffff; --border: #e2e8f0;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--ink);
    font-family: "Segoe UI", "Segoe UI Variable", system-ui, -apple-system, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .wrap {{ max-width: 1280px; margin: 0 auto; padding: 32px 24px 48px; }}
  header {{ margin-bottom: 24px; }}
  h1 {{ margin: 0 0 4px; font-size: 26px; font-weight: 700; letter-spacing: -0.02em; }}
  .subtitle {{ color: var(--muted); font-size: 14px; }}
  .meta {{ margin-top: 8px; font-size: 12px; color: var(--muted); }}
  .kpi-grid {{
    display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px;
    margin-bottom: 24px;
  }}
  .kpi {{
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 16px 18px; box-shadow: 0 1px 2px rgba(15,23,42,0.04);
  }}
  .kpi-label {{ font-size: 12px; color: var(--muted); text-transform: uppercase;
    letter-spacing: 0.06em; font-weight: 600; }}
  .kpi-value {{ font-size: 26px; font-weight: 700; margin: 6px 0 2px;
    color: var(--ink); letter-spacing: -0.02em; }}
  .kpi-sub {{ font-size: 12px; color: var(--muted); }}
  .grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 18px;
  }}
  .card {{
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 8px 12px 4px; box-shadow: 0 1px 2px rgba(15,23,42,0.04);
  }}
  .card.wide {{ grid-column: 1 / -1; }}
  .card.tall {{ min-height: 420px; }}
  .insights {{
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 20px 24px; margin-bottom: 18px; box-shadow: 0 1px 2px rgba(15,23,42,0.04);
  }}
  .insights h2 {{ margin: 0 0 10px; font-size: 15px; font-weight: 700; }}
  .insights ul {{ margin: 0; padding-left: 20px; line-height: 1.7; font-size: 14px; }}
  .insights li {{ margin-bottom: 4px; }}
  .section-title {{ font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--muted); font-weight: 700; margin: 24px 0 10px; }}
  .data-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .data-table th {{ text-align: left; padding: 8px 10px; border-bottom: 2px solid var(--border);
    color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase;
    letter-spacing: 0.06em; }}
  .data-table td {{ padding: 8px 10px; border-bottom: 1px solid var(--border); }}
  .data-table tr:last-child td {{ border-bottom: none; }}
  .data-table .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);
    font-size: 12px; color: var(--muted); line-height: 1.6; }}
  @media (max-width: 900px) {{
    .kpi-grid {{ grid-template-columns: repeat(3, 1fr); }}
    .grid {{ grid-template-columns: 1fr; }}
  }}
  @media (max-width: 560px) {{
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
<script>{plotly_js}</script>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Chinook music store - sales dashboard</h1>
    <div class="subtitle">SQL + BI portfolio project &middot; 10 business questions answered on a real relational database</div>
    <div class="meta">Dataset: Chinook (SQLite) &middot; {int(kpi['total_invoices'])} invoices &middot;
      {kpi['first_invoice_date'][:10]} to {kpi['last_invoice_date'][:10]} &middot;
      {query_count} SQL queries &middot; {total_rows} result rows &middot;
      generated {generated}</div>
  </header>

  <div class="kpi-grid">
    {kpi_cards}
  </div>

  <div class="insights">
    <h2>Key findings</h2>
    <ul>
      {insights}
    </ul>
  </div>

  <div class="section-title">Revenue over time</div>
  <div class="grid">
    <div class="card wide">{charts['monthly']}</div>
    <div class="card wide">{charts['growth']}</div>
  </div>

  <div class="section-title">Markets and products</div>
  <div class="grid">
    <div class="card">{charts['country']}</div>
    <div class="card">{charts['genre']}</div>
    <div class="card">{charts['artists']}</div>
    <div class="card">{charts['media']}</div>
  </div>

  <div class="section-title">Customers and operations</div>
  <div class="grid">
    <div class="card">{charts['employees']}</div>
    <div class="card">{charts['aov']}</div>
    <div class="card wide">
      <div class="section-title" style="margin-top:4px;">Top 10 customers by lifetime revenue</div>
      {top_customers_table}
    </div>
  </div>

  <footer>
    Built with Python (sqlite3, csv, plotly) from <code>sql/01_*.sql</code> ... <code>sql/10_*.sql</code>.
    Every number on this page comes from those CSVs; re-run <code>python src/run_queries.py</code>
    then <code>python src/dashboard.py</code> to refresh. Plotly.js is embedded, so this file works
    offline. Data source: Chinook sample database (lerocha/chinook-database), used for learning.
  </footer>
</div>
</body>
</html>"""

    DASHBOARD_PATH.write_text(html, encoding="utf-8")
    size_mb = DASHBOARD_PATH.stat().st_size / (1024 * 1024)
    print(f"Dashboard written: {DASHBOARD_PATH}")
    print(f"  size: {size_mb:.2f} MB (plotly.js embedded for offline use)")
    print(f"  charts: {len(charts)}  |  kpi cards: 6  |  insights: 6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
