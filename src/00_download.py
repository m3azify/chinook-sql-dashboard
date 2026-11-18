"""Download (or verify) the Chinook SQLite database.

WHY this script exists: every other script assumes data/chinook.sqlite is present.
Keeping the download in its own file means the data step is reproducible and
re-runnable without re-running the queries or the dashboard.

Run from the project root:  python src/00_download.py
"""
import hashlib
import os
import shutil
import sqlite3
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "chinook.sqlite"
URL = ("https://raw.githubusercontent.com/lerocha/chinook-database/"
       "master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite")
EXPECTED_TABLES = [
    "Album", "Artist", "Customer", "Employee", "Genre", "Invoice",
    "InvoiceLine", "MediaType", "Playlist", "PlaylistTrack", "Track",
]
# These are the "does the file look like Chinook?" checks. We do not pin the
# exact counts to a hard failure because the dataset is owned by a third party,
# but we print them so a human can spot a truncated download.
MIN_INVOICES = 400
MIN_TRACKS = 3000


def verify(db_path: Path) -> tuple[bool, str]:
    """Open the SQLite file and confirm it is a complete Chinook database.

    Returns (ok, message). We check the schema, not the data, because the
    data is owned by a third party and may drift over time.
    """
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        return False, f"cannot open as SQLite: {exc}"
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    except sqlite3.Error as exc:
        return False, f"cannot read sqlite_master: {exc}"
    finally:
        conn.close()

    present = {r[0] for r in rows}
    missing = [t for t in EXPECTED_TABLES if t not in present]
    if missing:
        return False, f"missing tables: {missing}"
    # Quick sanity check on row counts to catch a truncated file.
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        inv = conn.execute("SELECT COUNT(*) FROM Invoice").fetchone()[0]
        trk = conn.execute("SELECT COUNT(*) FROM Track").fetchone()[0]
    finally:
        conn.close()
    if inv < MIN_INVOICES or trk < MIN_TRACKS:
        return False, (f"row counts too small (Invoice={inv}, Track={trk}); "
                       f"expected at least {MIN_INVOICES} / {MIN_TRACKS}")
    return True, f"verified: {len(present)} tables, Invoice={inv}, Track={trk}"


def print_tables(db_path: Path) -> None:
    """Print every table with its row count and column list."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()]
        print(f"  {'table':<15}{'rows':>8}   columns")
        print("  " + "-" * 60)
        for t in tables:
            n = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{t}")').fetchall()]
            print(f"  {t:<15}{n:>8}   {', '.join(cols)}")
    finally:
        conn.close()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_via_urllib(target: Path) -> None:
    """Download with a simple progress indicator. Uses a .part file so a
    failed download never leaves a half-written chinook.sqlite."""
    part = target.with_suffix(".sqlite.part")
    try:
        with urllib.request.urlopen(URL, timeout=60) as response:
            total = int(response.headers.get("Content-Length", 0))
            done = 0
            with part.open("wb") as out:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    done += len(chunk)
                    if total:
                        pct = 100 * done // total
                        print(f"\r  downloaded {done // 1024} KB / {total // 1024} KB "
                              f"({pct}%)", end="", flush=True)
            print()
        if total and part.stat().st_size != total:
            raise RuntimeError(f"size mismatch: got {part.stat().st_size}, expected {total}")
        part.replace(target)
    except Exception:
        if part.exists():
            part.unlink()
        raise


def download_via_git(target: Path) -> None:
    """Fallback: shallow clone the whole repo and copy the file out."""
    clone_dir = DATA_DIR / "_chinook_clone"
    if clone_dir.exists():
        shutil.rmtree(clone_dir)
    print("  trying git clone fallback...")
    rc = os.system(f'git clone --depth 1 https://github.com/lerocha/chinook-database "{clone_dir}"')
    if rc != 0:
        raise RuntimeError("git clone failed")
    src = clone_dir / "ChinookDatabase" / "DataSources" / "Chinook_Sqlite.sqlite"
    if not src.exists():
        raise FileNotFoundError(f"expected file not found inside clone: {src}")
    shutil.copyfile(src, target)
    shutil.rmtree(clone_dir)


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        ok, msg = verify(DB_PATH)
        if ok:
            print(f"Database already present at {DB_PATH}")
            print(f"  {msg}")
            print(f"  sha256: {sha256_file(DB_PATH)}")
            print(f"  size:   {DB_PATH.stat().st_size // 1024} KB")
            print("\nTables:")
            print_tables(DB_PATH)
            return 0
        print(f"Existing file failed verification ({msg}); re-downloading.")

    print(f"Downloading Chinook SQLite from:\n  {URL}")
    try:
        download_via_urllib(DB_PATH)
        print("  download complete")
    except Exception as exc:
        print(f"  urllib failed: {exc}")
        try:
            download_via_git(DB_PATH)
            print("  cloned and copied")
        except Exception as exc2:
            print(f"  git fallback also failed: {exc2}", file=sys.stderr)
            print("Manual fallback:", file=sys.stderr)
            print("  git clone --depth 1 https://github.com/lerocha/chinook-database", file=sys.stderr)
            print(f"  then copy ChinookDatabase/DataSources/Chinook_Sqlite.sqlite -> {DB_PATH}", file=sys.stderr)
            return 1

    ok, msg = verify(DB_PATH)
    if not ok:
        print(f"Verification failed after download: {msg}", file=sys.stderr)
        return 1
    print(f"  {msg}")
    print(f"  sha256: {sha256_file(DB_PATH)}")
    print(f"  size:   {DB_PATH.stat().st_size // 1024} KB")
    print("\nTables:")
    print_tables(DB_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
