"""Baut data/vnb.csv + data/<jahr>/*.csv zu dist/par14a_<jahr>.sqlite zusammen."""
import csv, sqlite3, sys
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
    con.executemany(
        f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
        [[r[c] if r[c] != "" else None for c in cols] for r in rows],
    )
    return len(rows)


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
    con.commit()
    con.close()
    print(f"{out.name}: {n_vnb} VNB, {n_pb} Preisblätter, {n_zf} Zeitfenster, {n_ro} Roll-out-Quoten")


if __name__ == "__main__":
    jahre = sys.argv[1:] or sorted(p.name for p in (ROOT / "data").iterdir() if p.is_dir())
    for j in jahre:
        build(int(j))
