"""Tests für die Build-Skripte (SQLite-Datenbanken und Webseite)."""
import json
import sqlite3
from contextlib import closing

import build_db
import build_web
import pytest
from conftest import JAHRE, ROOT, lies
from eintrag import zf_lesen, zf_schreiben


def test_zeitfenster_hin_und_zurueck(tmp_path):
    """zf_schreiben fasst Einzelfenster wieder zu genau der Zeile zusammen, die zf_lesen gelesen hat."""
    quelle = tmp_path / "ein.csv"
    quelle.write_text("vnb_id,jahr,quartal,ht,nt\n"
                      "7,2026,1,07:00-09:00|17:00-19:00,00:00-05:00\n"
                      "7,2026,4,17:00-20:00,\n", encoding="utf-8")
    fenster = zf_lesen(quelle)
    assert {"vnb_id": "7", "jahr": "2026", "quartal": "1", "stufe": "HT", "von": "17:00", "bis": "19:00"} in fenster
    assert len(fenster) == 4
    ziel = tmp_path / "aus.csv"
    zf_schreiben(ziel, fenster)
    assert ziel.read_text(encoding="utf-8") == quelle.read_text(encoding="utf-8")


def test_load_lehnt_fremde_spaltennamen_ab(tmp_path):
    with closing(sqlite3.connect(":memory:")) as con:
        con.execute("CREATE TABLE t (a TEXT)")
        with pytest.raises(ValueError):
            build_db.load(con, "t", tmp_path / "x.csv", rows=[{"a); DROP TABLE t; --": "1"}])


def test_load_leere_werte_werden_null():
    with closing(sqlite3.connect(":memory:")) as con:
        con.execute("CREATE TABLE t (a TEXT, b REAL, jahr INTEGER)")
        n = build_db.load(con, "t", None, 2026, rows=[{"a": "x", "b": "", "jahr": "2026"},
                                                      {"a": "y", "b": "1.5", "jahr": "2027"}])
        assert n == 1
        assert con.execute("SELECT a, b FROM t").fetchall() == [("x", None)]


@pytest.mark.parametrize("jahr", JAHRE)
def test_build_db(jahr):
    build_db.build(int(jahr))
    with closing(sqlite3.connect(ROOT / "dist" / f"par14a_{jahr}.sqlite")) as con:
        assert con.execute("PRAGMA foreign_key_check").fetchall() == []
        n_pb = con.execute("SELECT count(*) FROM preisblatt").fetchone()[0]
        n_zf = con.execute("SELECT count(*) FROM m3_zeitfenster").fetchone()[0]
        meta = dict(con.execute("SELECT schluessel, wert FROM meta"))
    assert n_pb == len(lies(ROOT / "data" / jahr / "preisblatt.csv"))
    assert n_zf == len(zf_lesen(ROOT / "data" / jahr / "m3_zeitfenster.csv"))
    assert meta["jahr"] == jahr
    assert meta["version"]
    assert meta["lizenz"].startswith("CC-BY-4.0")


def test_build_web(tmp_path):
    ziel = tmp_path / "web"
    build_web.main(ziel)
    assert (ziel / "index.html").exists()
    assert json.loads((ziel / "daten" / "jahre.json").read_text(encoding="utf-8")) == sorted(JAHRE, reverse=True)
    badge = json.loads((ziel / "daten" / "badge.json").read_text(encoding="utf-8"))
    assert badge["schemaVersion"] == 1
    daten = json.loads((ziel / "daten" / f"{JAHRE[-1]}.json").read_text(encoding="utf-8"))
    assert len(daten) == len(lies(ROOT / "data" / "vnb.csv"))
