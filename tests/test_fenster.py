"""Gezielte Tests der Zeitfenster- und Quartalserkennung (fenster.py), je ein Layout aus echten Preisblättern."""
import fenster
import pytest
from eintrag import zf_lesen


@pytest.mark.parametrize(("zeile", "erwartet"), [
    ("NT 23:00 - 7:00 Uhr", ["23:00-24:00", "00:00-07:00"]),       # über Mitternacht, wie in m3_zeitfenster.csv
    ("NT 22:15-06:30", ["22:15-24:00", "00:00-06:30"]),
    ("HT 19:30 – 00:00 Uhr", ["19:30-24:00"]),
    ("HT 17 - 21 Uhr", ["17:00-21:00"]),
    ("Q1: 01.01.-31.03.", []),                                     # Datum, keine Uhrzeit
    ("HT 24:30-25:00", []),
])
def test_bereiche(zeile, erwartet):
    assert [b for _, b in fenster.bereiche(zeile)] == erwartet


@pytest.mark.parametrize(("seite", "erwartet"), [
    ("2026 | Q1 | Q2 | Q3 | Q4\nGültigkeit der drei Tarifstufen je Quartal: | Ja | Nein | Nein | Ja", [1, 4]),
    ("Quartal 1 | Quartal 2 | Quartal 3 | Quartal 3\nZeitraum | 01.01.-31.03.\nAnwendung | Ja | Nein | Nein | Ja", [1, 4]),
    ("AP gilt nur in: | Q1 + Q4 | 13,29", [1, 4]),
    ("Modul 3 - Hochtarif (Q1 und Q4 - Mo. bis Fr. von 12.00 Uhr bis 13.00 Uhr)", [1, 4]),
    ("• NT (Niedriglasttarifstufe): Erstes und viertes Quartal.", [1, 4]),
    ("Zeitfenster Modul 3: Q1: ja, Q2: nein, Q3: nein, Q4: ja", [1, 4]),
    ("Quartal 1 | 0:00 - 10:00 | 17:00 - 22:00\nQuartal 2 | 0:00 - 24:00\nQuartal 3 | 0:00 - 24:00\n"
     "Quartal 4 | 0:00 - 10:00 | 17:00 - 22:00", [1, 4]),
    ("3. Quartalsweise Anwendung\nDie Stufen gelten ganzjährig.", [1, 2, 3, 4]),
    ("Gültig ab 01.01.2026", None),
])
def test_quartale(seite, erwartet):
    assert fenster.quartale(seite) == erwartet


def test_fliesstext_ist_kein_tabellenkopf():
    """"(HT) maximal 100 % über dem Standardtarif" darf die ST-Zeiten nicht der HT-Spalte zuordnen."""
    text = ("Modul 3\nHochlasttarifstufe\n 10:00 - 19:30 Uhr 11,63 ct/kWh\n"
            "(HT)      maximal 100 % über dem Standardtarif.\nStandardtarifstufe     06:00 – 10:00 Uhr\n"
            "Niedriglasttarifstufe\n 00:00 – 06:00 Uhr 3,85 ct/kWh\nErstes und viertes Quartal")
    e = fenster.extrahiere(text)
    assert (e["HT"], e["NT"], e["quartale"], e["sicher"]) == (["10:00-19:30"], ["00:00-06:00"], "1,4", True)


def test_spaltenkopf():
    assert fenster.spaltenkopf("Preise   Standardlasttarif in ct/kWh Hochlasttarif in ct/kWh Niedriglasttarif in ct/kWh")
    assert fenster.spaltenkopf("      Niedriglasttarif NT        Standardtarif ST       Hochlasttarif HT")
    assert not fenster.spaltenkopf("(HT)      maximal 100 % über dem Standardtarif.")


@pytest.mark.parametrize("inhalt", [
    "vnb_id,jahr,quartal,ht,nt\n7,2026,1\n",                      # Zeile zu kurz
    "vnb_id,jahr,quartal,ht,nt\n7,2026,1,17:00,\n",               # Fenster ohne Ende
    "vnb_id,jahr,quartal,ht,nt\n7,2026,1,17:00-19:00-21:00,\n",
])
def test_zf_lesen_meldet_kaputte_zeilen(tmp_path, inhalt):
    pfad = tmp_path / "m3_zeitfenster.csv"
    pfad.write_text(inhalt, encoding="utf-8")
    with pytest.raises(ValueError, match="m3_zeitfenster.csv:2"):
        zf_lesen(pfad)


@pytest.mark.parametrize("a, b, erwartet", [
    ("24:00", "00:00", []),
    ("00:00", "00:00", []),
    ("24:00", "24:00", []),
    ("00:00", "24:00", [(0, "00:00-24:00")]),
    ("22:00", "06:00", [(0, "22:00-24:00"), (0, "00:00-06:00")]),
])
def test_spanne_leere_und_ganze_tage(a, b, erwartet):
    assert fenster.spanne(0, a, b) == erwartet


@pytest.mark.parametrize("seite, erwartet", [
    ("1. Quartal | 2. Quartal | 3. Quartal | 4. Quartal\nja | nein | nein | ja", [1, 4]),
    ("Erstes Quartal  Zweites Quartal  Drittes Quartal  Viertes Quartal\nJa  Nein  Nein  Ja", [1, 4]),
    ("Q4 | Q3 | Q2 | Q1\nja | nein | nein | nein", [4]),
    ("Q1 | Q2 | Q3 | Q4\nnein | nein | nein | nein\nQuartale 1 und 4", None),
])
def test_quartale_tabelle_beschriftung(seite, erwartet):
    assert fenster.quartale(seite) == erwartet
