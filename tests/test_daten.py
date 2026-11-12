"""Plausibilitätsprüfungen für die CSV-Daten in data/.

Die Tests prüfen Form und innere Stimmigkeit, nicht die Preise selbst: maßgeblich bleibt das
Preisblatt des Netzbetreibers. Ein fehlschlagender Test zeigt einen Tipp- oder Zuordnungsfehler.
"""
import re
import sqlite3
from contextlib import closing

import pytest
from conftest import JAHRE, ROOT, lies

STATUS = {"endgueltig", "vorlaeufig", "nicht_gefunden"}
PREISE = ["std_grundpreis_eur_a", "std_arbeitspreis_ct_kwh", "m1_reduzierung_eur_a", "m2_grundpreis_eur_a",
          "m2_arbeitspreis_ct_kwh", "m3_ht_ct_kwh", "m3_st_ct_kwh", "m3_nt_ct_kwh"]
DATUM = re.compile(r"\d{4}-\d{2}-\d{2}")
FENSTER = re.compile(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})")


def spalten(tabelle):
    with closing(sqlite3.connect(":memory:")) as con:
        con.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
        return [r[1] for r in con.execute(f"PRAGMA table_info({tabelle})")]


@pytest.fixture(scope="module")
def vnb_ids():
    return {r["vnb_id"] for r in lies(ROOT / "data" / "vnb.csv")}


def test_vnb_eindeutig_und_vollstaendig():
    rows = lies(ROOT / "data" / "vnb.csv")
    assert list(rows[0]) == spalten("vnb")
    ids = [r["vnb_id"] for r in rows]
    assert len(ids) == len(set(ids)), "doppelte vnb_id in data/vnb.csv"
    for r in rows:
        assert r["vnb_id"].isdigit(), r
        assert r["name"].strip(), f"VNB {r['vnb_id']} ohne Namen"


@pytest.mark.parametrize("jahr", JAHRE)
def test_preisblatt(jahr, vnb_ids):
    rows = lies(ROOT / "data" / jahr / "preisblatt.csv")
    assert list(rows[0]) == spalten("preisblatt")
    gesehen = set()
    for r in rows:
        vid = r["vnb_id"]
        assert vid in vnb_ids, f"{jahr}: VNB {vid} fehlt in data/vnb.csv"
        assert vid not in gesehen, f"{jahr}: VNB {vid} doppelt"
        gesehen.add(vid)
        assert r["jahr"] == jahr, f"{jahr}: VNB {vid} mit jahr={r['jahr']}"
        assert r["status"] in STATUS, f"{jahr}: VNB {vid} mit Status {r['status']!r}"
        for feld in ("gueltig_ab", "abgerufen_am"):
            assert not r[feld] or DATUM.fullmatch(r[feld]), f"{jahr}: VNB {vid} {feld}={r[feld]!r}"
        for feld in ("preisblatt_url", "quelle_seite_url"):
            assert not r[feld] or r[feld].startswith(("https://", "http://")), f"{jahr}: VNB {vid} {feld}"
        assert not r["pdf_sha256"] or re.fullmatch(r"[0-9a-f]{64}", r["pdf_sha256"]), f"{jahr}: VNB {vid} sha256"
        for feld in PREISE:
            if r[feld]:
                assert float(r[feld]) >= 0, f"{jahr}: VNB {vid} {feld}={r[feld]} negativ"
        if r["m3_quartale_aktiv"]:
            q = r["m3_quartale_aktiv"].split(",")
            assert set(q) <= {"1", "2", "3", "4"}, f"{jahr}: VNB {vid} m3_quartale_aktiv={r['m3_quartale_aktiv']!r}"
        if r["status"] != "nicht_gefunden":
            # Ohne Download-URL (z. B. Bot-Schutz) muss wenigstens die Quellseite angegeben sein.
            assert r["preisblatt_url"] or r["quelle_seite_url"], f"{jahr}: VNB {vid} mit Preisblatt, aber ohne Quelle"


@pytest.mark.parametrize("jahr", JAHRE)
def test_modul3_stufen(jahr):
    """Modul 3: HT >= ST >= NT, soweit alle drei angegeben sind."""
    for r in lies(ROOT / "data" / jahr / "preisblatt.csv"):
        if r["m3_ht_ct_kwh"] and r["m3_st_ct_kwh"] and r["m3_nt_ct_kwh"]:
            ht, st, nt = (float(r[f"m3_{s}_ct_kwh"]) for s in ("ht", "st", "nt"))
            assert ht >= st >= nt, f"{jahr}: VNB {r['vnb_id']} HT {ht} / ST {st} / NT {nt}"


def minuten(h, m):
    return int(h) * 60 + int(m)


@pytest.mark.parametrize("jahr", JAHRE)
def test_zeitfenster(jahr):
    pbs = {r["vnb_id"] for r in lies(ROOT / "data" / jahr / "preisblatt.csv")}
    gesehen = set()
    for r in lies(ROOT / "data" / jahr / "m3_zeitfenster.csv"):
        vid, q = r["vnb_id"], r["quartal"]
        assert vid in pbs, f"{jahr}: Zeitfenster für VNB {vid} ohne Preisblatt"
        assert r["jahr"] == jahr
        assert q in {"1", "2", "3", "4"}, f"{jahr}: VNB {vid} Quartal {q!r}"
        assert (vid, q) not in gesehen, f"{jahr}: VNB {vid} Quartal {q} doppelt"
        gesehen.add((vid, q))
        belegt = []
        for stufe in ("ht", "nt"):
            for span in filter(None, r[stufe].split("|")):
                m = FENSTER.fullmatch(span)
                assert m, f"{jahr}: VNB {vid} Q{q} {stufe}={span!r}"
                von, bis = minuten(*m.groups()[:2]), minuten(*m.groups()[2:])
                assert von < 24 * 60 and bis <= 24 * 60 and von != bis, f"{jahr}: VNB {vid} Q{q} {stufe} {span}"
                # Fenster über Mitternacht (z. B. 22:00-06:00) in zwei Teile zerlegen, wie die Webseite
                teile = [(von, bis)] if von < bis else [(von, 24 * 60), (0, bis)]
                belegt += [(a, b, f"{stufe} {span}") for a, b in teile if a < b]
        belegt.sort()
        for (_, bis_a, a), (von_b, _, b) in zip(belegt, belegt[1:], strict=False):
            assert bis_a <= von_b, f"{jahr}: VNB {vid} Q{q}: {a} überschneidet {b}"
