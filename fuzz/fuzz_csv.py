"""Atheris-Fuzzer für den Datenimport: beliebiger CSV-Inhalt in build_db.load (Tabellen aus schema.sql)
und in die Zeitfenster-Zerlegung eintrag.zf_lesen. Erlaubt sind nur die vorgesehenen Fehler: ValueError
für fremde Spalten oder kaputte Zeitfenster und Constraint-Verletzungen von SQLite. Alles andere (etwa ein
SQL-Syntaxfehler durch einen Spaltennamen oder eine unerwartete Ausnahme) gilt als Fund.

    python fuzz/fuzz_csv.py -max_total_time=60 -max_len=2048
"""
import csv
import io
import sqlite3
import sys
import tempfile
from pathlib import Path

import atheris

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
with atheris.instrument_imports():
    import build_db
    import eintrag

SCHEMA = (ROOT / "schema.sql").read_text(encoding="utf-8")
TABELLEN = ["vnb", "preisblatt", "m3_zeitfenster", "rollout_quote"]
TMP = Path(tempfile.mkdtemp()) / "m3_zeitfenster.csv"


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    tabelle = fdp.PickValueInList(TABELLEN)
    text = fdp.ConsumeUnicodeNoSurrogates(len(data))
    try:
        zeilen = list(csv.DictReader(io.StringIO(text)))
    except csv.Error:
        return
    con = sqlite3.connect(":memory:")
    try:
        con.executescript(SCHEMA)
        build_db.load(con, tabelle, Path("fuzz.csv"), rows=zeilen)
    except (ValueError, sqlite3.IntegrityError):
        pass
    finally:
        con.close()
    TMP.write_text(text, encoding="utf-8")
    try:
        for f in eintrag.zf_lesen(TMP):
            if not {"vnb_id", "jahr", "quartal", "stufe", "von", "bis"} <= set(f):
                raise AssertionError(f"unvollständiges Fenster {f}")
    except (ValueError, csv.Error):
        pass


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
