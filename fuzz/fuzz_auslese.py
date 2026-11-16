"""Atheris-Fuzzer für die Auslese-Heuristiken: beliebiger (Preisblatt-)Text in fenster.extrahiere und
vorschlag.analysiere. Preisblatt-Texte sind fremde Eingaben (PDFs der Netzbetreiber, OCR), die Heuristiken
dürfen daran nie abstürzen und müssen ihre Invarianten einhalten.

    python fuzz/fuzz_auslese.py -max_total_time=60 -max_len=4096 <korpus-ordner>
"""
import re
import sys
from pathlib import Path

import atheris

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
with atheris.instrument_imports():
    import fenster
    import vorschlag

FENSTER = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d-(?:(?:[01]\d|2[0-3]):[0-5]\d|24:00)")


def pruefe_fenster(liste):
    for s in liste:
        if not FENSTER.fullmatch(s) or s[:5] >= s[6:]:
            raise AssertionError(f"ungültiges Zeitfenster {s!r}")


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    jahr = fdp.ConsumeIntInRange(2024, 2030)
    text = fdp.ConsumeUnicodeNoSurrogates(len(data))
    e = fenster.extrahiere(text)
    if "HT" in e:
        pruefe_fenster(e["HT"] + e["NT"])
        if e["quartale"] is not None and not re.fullmatch(r"[1-4](,[1-4])*", e["quartale"]):
            raise AssertionError(f"ungültige Quartale {e['quartale']!r}")
    q = fenster.quartale(text)
    if q is not None and not (q and q == sorted(set(q)) and set(q) <= {1, 2, 3, 4}):
        raise AssertionError(f"ungültige Quartale {q!r}")
    v = vorschlag.analysiere(text, jahr)
    if v is not None:
        if not 1.5 <= v["std_ap"] <= 16:
            raise AssertionError(f"Arbeitspreis außerhalb des Suchbereichs: {v}")
        if v["m2_ap"] is not None and abs(v["m2_ap"] - round(0.4 * v["std_ap"], 2)) > 0.011:
            raise AssertionError(f"Modul 2 passt nicht zu 0,4 × AP: {v}")


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
