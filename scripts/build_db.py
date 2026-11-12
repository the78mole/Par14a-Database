"""Baut data/vnb.csv + data/<jahr>/*.csv zu dist/par14a_<jahr>.sqlite zusammen."""
import csv, datetime, sqlite3, subprocess, sys
from pathlib import Path

from eintrag import zf_lesen

ROOT = Path(__file__).resolve().parent.parent


def load(con, table, path, jahr=None, rows=None):
    if rows is None:
        if not path.exists():
            return 0
        with path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    if jahr is not None:
        rows = [r for r in rows if r.get("jahr") in (None, "", str(jahr))]
    if not rows:
        return 0
    cols = list(rows[0].keys())
    # Spaltennamen kommen aus den CSV-Köpfen und landen im SQL-Text, Werte nur als Parameter.
    if not all(c.isidentifier() for c in cols):
        raise ValueError(f"{path}: ungültiger Spaltenname in {cols}")
    con.executemany(
        f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",  # noqa: S608
        [[r[c] if r[c] != "" else None for c in cols] for r in rows],
    )
    return len(rows)


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def version():
    """Eindeutige Version des Datenstands: Commit-Datum und kurzer Commit-Hash, z. B. 2026-11-12+837ea02."""
    stand, sha = git("log", "-1", "--format=%cs"), git("rev-parse", "--short", "HEAD")
    if not sha:
        return "lokal"
    return f"{stand}+{sha}" + ("-geaendert" if git("status", "--porcelain", "data", "schema.sql") else "")


def build(jahr):
    out = ROOT / "dist" / f"par14a_{jahr}.sqlite"
    out.parent.mkdir(exist_ok=True)
    out.unlink(missing_ok=True)
    con = sqlite3.connect(out)
    con.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
    n_vnb = load(con, "vnb", ROOT / "data" / "vnb.csv")
    n_ro = load(con, "rollout_quote", ROOT / "data" / "rollout_quote.csv")
    n_pb = load(con, "preisblatt", ROOT / "data" / str(jahr) / "preisblatt.csv", jahr)
    # CSV kompakt (eine Zeile je Quartal), Tabelle normalisiert (eine Zeile je Fenster)
    zf = ROOT / "data" / str(jahr) / "m3_zeitfenster.csv"
    n_zf = load(con, "m3_zeitfenster", zf, jahr, zf_lesen(zf))
    v = version()
    con.executemany("INSERT INTO meta (schluessel, wert) VALUES (?, ?)", [
        ("version", v), ("jahr", str(jahr)), ("commit", git("rev-parse", "HEAD")),
        ("lizenz", "CC-BY-4.0, Namensnennung: Par14a-Database (the78mole), https://github.com/the78mole/Par14a-Database"),
        ("gebaut_am", datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"))])
    con.commit()
    con.close()
    print(f"{out.name} ({v}): {n_vnb} VNB, {n_pb} Preisblätter, {n_zf} Zeitfenster, {n_ro} Roll-out-Quoten")


if __name__ == "__main__":
    jahre = sys.argv[1:] or sorted(p.name for p in (ROOT / "data").iterdir() if p.is_dir())
    for j in jahre:
        build(int(j))
