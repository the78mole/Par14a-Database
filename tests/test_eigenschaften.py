"""Eigenschaftsbasierte Tests (Fuzzing mit Hypothesis) für alles, was fremden Text oder CSV-Inhalt parst.

Hypothesis erzeugt zufällige und gezielt zusammengesetzte Eingaben (Preisblatt-Bausteine wie "Q1 + Q4",
"17:00 - 21:00 Uhr", "4,26 ct/kWh") und prüft Invarianten, die für jede Eingabe gelten müssen. Gefundene
Gegenbeispiele landen in .hypothesis/ und werden beim nächsten Lauf zuerst wiederholt. Die längeren
Fuzzing-Läufe mit Atheris stehen in fuzz/ und .github/workflows/fuzz.yml.
"""
import re
import sqlite3
from contextlib import closing

import build_db
import fenster
import pytest
import vorschlag
from eintrag import zf_lesen, zf_schreiben
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

EINSTELLUNGEN = settings(max_examples=300, deadline=None, suppress_health_check=[HealthCheck.too_slow])

UHRZEIT = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$|^24:00$")
BAUSTEINE = [
    "Modul 3", "HT", "NT", "ST", "Hochlasttarif", "Niedriglasttarif", "Standardtarif", "Hochlasttarifstufe",
    "Niedertarif", "Tarifstufe", "Quartal", "Quartale", "Q1", "Q2", "Q3", "Q4", "Q1 + Q4", "Q1 und Q4",
    "Erstes und viertes Quartal", "3. Quartalsweise", "1. Quartal", "ja", "nein", "Ja", "Nein", "x", "✓",
    "entfällt", "gilt", "ganzjährig", "Januar", "bis", "März", "Oktober", "Dezember", "01.01.-31.03.",
    "01.10. - 31.12.", "17:00", "21:00", "0:00", "24:00", "00:00", "23:45", "7:15", "12.00 Uhr", "2.30 Uhr",
    "17 - 21 Uhr", "-", "–", "bis", "|", "Uhr", "h", "4,26", "99,18", "1,70", "105,00", "7,41", "0,29",
    "ct/kWh", "€/Jahr", "€/Tag", "Grundpreis", "Arbeitspreis", "Modul 1", "pauschal", "Leistungspreis",
    "maximal 100 % über dem Standardtarif", "in ct/kWh", "   ", "\n", "\n", "\n", "\f",
]
baustein_text = st.lists(st.one_of(st.sampled_from(BAUSTEINE), st.text(max_size=6)), max_size=60).map(" ".join)
beliebiger_text = st.one_of(st.text(max_size=400), baustein_text)


def fenster_gueltig(spannen):
    for s in spannen:
        von, _, bis = s.partition("-")
        assert UHRZEIT.match(von) and UHRZEIT.match(bis), s
        assert von < bis, f"Fenster {s} ist leer oder läuft über Mitternacht"


@EINSTELLUNGEN
@given(beliebiger_text)
@example("NT 23:00 - 7:00 Uhr")
@example("HT 24:00-24:00")
@example("HT 24:30-25:00")
def test_bereiche_liefert_gueltige_fenster(text):
    out = fenster.bereiche(text)
    fenster_gueltig(b for _, b in out)
    assert all(0 <= pos < max(len(text), 1) for pos, _ in out)


@EINSTELLUNGEN
@given(st.integers(0, 23), st.integers(0, 59), st.integers(0, 24), st.integers(0, 59))
def test_spanne_deckt_dieselben_minuten_ab(h1, m1, h2, m2):
    """Ein Fenster über Mitternacht wird geteilt, deckt aber genau die gleichen Minuten ab."""
    a, b = fenster.hhmm(h1, m1), fenster.hhmm(h2, m2)
    teile = [s for _, s in fenster.spanne(0, a, b)]
    if not a or not b or a == b:
        assert teile == []
        return
    fenster_gueltig(teile)
    minute = lambda t: int(t[:2]) * 60 + int(t[3:])  # noqa: E731
    gedeckt = {x for s in teile for x in range(minute(s[:5]), minute(s[6:]))}
    start, ende = minute(a), minute(b) or 24 * 60
    erwartet = set(range(start, ende)) if start < ende else set(range(start, 24 * 60)) | set(range(0, ende))
    assert gedeckt == erwartet


@EINSTELLUNGEN
@given(beliebiger_text)
@example("2026 | Q1 | Q2 | Q3 | Q4\nGültigkeit: | Ja | Nein | Nein | Ja")
@example("Quartal 1 | Quartal 2 | Quartal 3\nja | nein")
def test_quartale_ist_none_oder_teilmenge(text):
    q = fenster.quartale(text)
    assert q is None or (q == sorted(set(q)) and set(q) <= {1, 2, 3, 4} and q)


@EINSTELLUNGEN
@given(beliebiger_text)
def test_extrahiere_stuerzt_nie_ab(text):
    e = fenster.extrahiere(text)
    assert isinstance(e["sicher"], bool)
    if "HT" in e:
        fenster_gueltig(e["HT"] + e["NT"])
        assert e["quartale"] is None or re.fullmatch(r"[1-4](,[1-4])*", e["quartale"])
    if e["sicher"]:
        assert e["NT"] and e["quartale"] and not set(e["HT"]) & set(e["NT"])


@EINSTELLUNGEN
@given(beliebiger_text, st.integers(2024, 2030))
@example("Arbeitspreis 4,26 ct/kWh\nModul 1 99,18 €/Jahr\nModul 2 1,70 ct/kWh", 2026)
def test_analysiere_haelt_die_modulformeln_ein(text, jahr):
    v = vorschlag.analysiere(text, jahr)
    if v is None:
        return
    assert 1.5 <= v["std_ap"] <= 16
    if v["m2_ap"] is not None:
        assert abs(v["m2_ap"] - round(0.4 * v["std_ap"], 2)) <= 0.011  # wie in vorschlag.analysiere
    assert v["m1"] > 0
    if v["ht"] is not None:
        assert v["std_ap"] < v["ht"] <= 2 * v["std_ap"] + 0.011
    if v["nt"] is not None:
        assert 0.1 * v["std_ap"] - 0.011 <= v["nt"] <= 0.4 * v["std_ap"] + 0.011


def zeitpunkt(h, m):
    return f"{h:02d}:{m:02d}"


fenster_zeile = st.tuples(st.integers(0, 23), st.sampled_from([0, 15, 30, 45]), st.integers(1, 96)).map(
    lambda t: (zeitpunkt(t[0], t[1]), min(t[0] * 60 + t[1] + t[2] * 15, 24 * 60)))
einzelfenster = st.lists(st.tuples(st.sampled_from(["1", "7", "42"]), st.sampled_from(["1", "2", "3", "4"]),
                                   st.sampled_from(["HT", "NT"]), fenster_zeile), max_size=12)


@EINSTELLUNGEN
@given(einzelfenster)
def test_zeitfenster_csv_hin_und_zurueck(tmp_path_factory, liste):
    """zf_schreiben und zf_lesen sind zueinander invers (bis auf die Reihenfolge)."""
    fenster_in = []
    for vnb, q, stufe, (von, ende) in liste:
        bis = zeitpunkt(ende // 60, ende % 60)
        if von != bis:
            fenster_in.append({"vnb_id": vnb, "jahr": "2026", "quartal": q, "stufe": stufe, "von": von, "bis": bis})
    pfad = tmp_path_factory.mktemp("zf") / "m3_zeitfenster.csv"
    zf_schreiben(pfad, fenster_in)
    schluessel = lambda f: tuple(sorted(f.items()))  # noqa: E731
    assert sorted(map(schluessel, zf_lesen(pfad))) == sorted(map(schluessel, fenster_in))


@EINSTELLUNGEN
@given(st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=10), min_size=1, max_size=4))
@example({"a); DROP TABLE t; --": "1"})
@example({'a" , "b': "1"})
def test_load_laesst_nur_bekannte_spalten_zu(zeile):
    """Spaltennamen aus CSV-Köpfen landen nie ungeprüft im SQL."""
    with closing(sqlite3.connect(":memory:")) as con:
        con.execute("CREATE TABLE t (a TEXT, b REAL)")
        if set(zeile) <= {"a", "b"}:
            assert build_db.load(con, "t", None, rows=[zeile]) == 1
        else:
            with pytest.raises(ValueError):
                build_db.load(con, "t", None, rows=[zeile])
        assert con.execute("SELECT name FROM sqlite_master").fetchall() == [("t",)]
