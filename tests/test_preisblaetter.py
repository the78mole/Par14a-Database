"""Regressionstests der Auslese-Heuristiken (fenster.py, vorschlag.py) an schwierigen echten Preisblättern.

Jeder Fall in tests/preisblaetter/ ist ein auf wenige Zeilen verkleinerter Preisblatt-Text (angelegt mit
scripts/testfall.py), die Sollwerte stammen aus data/<jahr>/. Was die Heuristik bei einem Fall noch falsch
macht, steht unter "bekannte_fehler" und läuft als strenges xfail: Wird es behoben, schlägt der Test fehl,
bis der Eintrag entfernt ist.
"""
import json

import fenster
import pytest
import vorschlag
from conftest import ROOT

ORDNER = ROOT / "tests" / "preisblaetter"
FAELLE = json.loads((ORDNER / "faelle.json").read_text(encoding="utf-8"))
GRUPPEN = {
    "fenster": ("quartale", "HT", "NT"),
    "kern": ("std_ap", "m1", "m2_ap"),
    "m3": ("ht", "nt"),
    "grundpreis": ("std_gp",),
}


def ist(name, jahr):
    text = (ORDNER / f"{name}.txt").read_text(encoding="utf-8")
    f = fenster.extrahiere(text)
    v = vorschlag.analysiere(text, jahr) or {}
    return {"quartale": f.get("quartale"), "HT": sorted(f.get("HT") or []), "NT": sorted(f.get("NT") or []), **v}


def params():
    for name, fall in FAELLE.items():
        for gruppe in GRUPPEN:
            grund = fall["bekannte_fehler"].get(gruppe)
            marks = [pytest.mark.xfail(reason=grund, strict=True)] if grund else []
            yield pytest.param(name, gruppe, id=f"{name}-{gruppe}", marks=marks)


@pytest.mark.parametrize(("name", "gruppe"), list(params()))
def test_preisblatt(name, gruppe):
    fall = FAELLE[name]
    ergebnis = ist(name, fall["jahr"])
    for feld in GRUPPEN[gruppe]:
        soll = fall["soll"][feld]
        wert = ergebnis.get(feld)
        if isinstance(soll, float):
            assert wert == pytest.approx(soll, abs=0.005), f"{feld}: {wert} statt {soll} ({fall['besonderheit']})"
        else:
            assert wert == soll, f"{feld}: {wert} statt {soll} ({fall['besonderheit']})"


def test_fall_dateien_vollstaendig():
    assert sorted(p.stem for p in ORDNER.glob("*.txt")) == sorted(FAELLE)
    for fall in FAELLE.values():
        assert set(fall["bekannte_fehler"]) <= set(GRUPPEN)
        assert len(fall["pdf_sha256"]) == 64
