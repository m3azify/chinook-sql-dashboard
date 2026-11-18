"""Run every SQL file in sql/ and write one CSV per query.

WHY a separate runner instead of embedding SQL in Python: the SQL lives in
.sql files so it can be read, edited and re-run in any SQL client (DB Browser,
DBeaver, Power BI's native SQLite connector). Python's only job here is to
execute, format and persist the results.

Run from the project root:  python src/run_queries.py
"""
import csv
import json
import sqlite3
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "chinook.sqlite"
SQL_DIR = PROJECT_ROOT / "sql"
OUTPUT_DIR = PROJECT_ROOT / "output"
MANIFEST_PATH = OUTPUT_DIR / "_manifest.json"


def configure_stdout() -> None:
    # Windows consoles default to the system code page, which cannot print the
    # accented names in this dataset (Helena Holy, Ladislav Kovacs). Forcing
    # UTF-8 keeps the printed tables readable; errors="replace" is the safety
    # net for the rare terminal that still cannot handle it.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def read_title(sql_text: str, fallback: str) -> str:
    """Extract the human title from the first '--' comment line."""
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            return stripped.lstrip("-").strip()
    return fallback


def print_table(columns: list[str], rows: list[tuple]) -> None:
    """Print an aligned, readable table. All rows are printed because the
    largest result set here is 60 rows."""
    if not rows:
        print("  (no rows)")
        return
    widths = [len(c) for c in columns]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(str(value)))
    widths = [min(w, 40) for w in widths]   # keep very wide columns tidy
    header = "  " + "  ".join(c.ljust(widths[i]) for i, c in enumerate(columns))
    print(header)
    print("  " + "  ".join("-" * widths[i] for i in range(len(columns))))
    for row in rows:
        cells = []
        for i, value in enumerate(row):
            text = str(value)
            if len(text) > widths[i]:
                text = text[: widths[i] - 1] + "…"
            cells.append(text.ljust(widths[i]))
        print("  " + "  ".join(cells))


def run_one(conn: sqlite3.Connection, path: Path) -> dict:
    sql_text = path.read_text(encoding="utf-8")
    title = read_title(sql_text, path.stem)
    # Split on semicolons that actually terminate a statement. sqlite3's
    # complete_statement() understands string literals and comments, so a ';'
    # inside '...' or inside a '--' comment does not create a false boundary.
    statements = []
    buffer: list[str] = []
    for char in sql_text:
        buffer.append(char)
        if char == ";" and sqlite3.complete_statement("".join(buffer)):
            statements.append("".join(buffer).strip())
            buffer = []
    trailing_code = "\n".join(
        line for line in "".join(buffer).splitlines()
        if not line.strip().startswith("--")).strip()
    if trailing_code:
        raise ValueError(f"{path.name}: unterminated SQL statement "
                         "(missing final semicolon)")
    if len(statements) != 1:
        raise ValueError(f"{path.name}: contains {len(statements)} statements; "
                         f"split it into separate files.")
    cursor = conn.execute(statements[0])
    columns = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    out_csv = OUTPUT_DIR / (path.stem + ".csv")
    with out_csv.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"\n=== {path.name}  ({len(rows)} rows) ===")
    print(f"    {title}")
    print_table(columns, rows)
    print(f"    -> wrote {out_csv.relative_to(PROJECT_ROOT)}")

    return {
        "file": path.name,
        "name": path.stem,
        "title": title,
        "rows": len(rows),
        "columns": columns,
        "csv": str(out_csv.relative_to(PROJECT_ROOT)).replace("\\", "/"),
    }


def main() -> int:
    configure_stdout()
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}", file=sys.stderr)
        print("Run first:  python src/00_download.py", file=sys.stderr)
        return 1
    if not SQL_DIR.exists():
        print(f"SQL directory not found: {SQL_DIR}", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sql_files = sorted(SQL_DIR.glob("*.sql"))
    if not sql_files:
        print("No .sql files found.", file=sys.stderr)
        return 1

    print(f"Running {len(sql_files)} SQL files against {DB_PATH.relative_to(PROJECT_ROOT)}")

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = None
    manifest_entries = []
    total_rows = 0
    started = time.time()
    try:
        for path in sql_files:
            try:
                entry = run_one(conn, path)
            except (sqlite3.Error, ValueError, OSError) as exc:
                print(f"\nFAILED on {path.name}:", file=sys.stderr)
                print(f"  {type(exc).__name__}: {exc}", file=sys.stderr)
                print("  SQL file contents:", file=sys.stderr)
                print(path.read_text(encoding="utf-8"), file=sys.stderr)
                conn.close()
                return 1
            manifest_entries.append(entry)
            total_rows += entry["rows"]
    finally:
        conn.close()

    manifest = {
        "database": str(DB_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "database_sha256": _sha256(DB_PATH),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "query_count": len(manifest_entries),
        "total_rows": total_rows,
        "queries": manifest_entries,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                            encoding="utf-8")

    elapsed = time.time() - started
    print("\n" + "=" * 60)
    print(f"OK: {len(manifest_entries)} queries, {total_rows} rows total, "
          f"{elapsed:.2f}s")
    print(f"Manifest: {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")
    return 0


def _sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
