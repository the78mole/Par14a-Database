"""Legt aus einem erfassten Preisblatt einen Testfall für tests/test_preisblaetter.py an.

Der Preisblatt-Text aus .cache/text wird auf die Zeilen verkleinert, die das Ergebnis von
fenster.extrahiere und vorschlag.analysiere bestimmen (Delta-Debugging auf Zeilenebene). So landen
nur wenige Zeilen im Repository, nicht das ganze Preisblatt. Die Sollwerte kommen aus data/<jahr>/.

    python scripts/testfall.py <jahr> <vnb_id> "<was an dem Preisblatt schwierig ist>"
"""
import csv, json, re, sys
from pathlib import Path

import fenster, vorschlag
from eintrag import zf_lesen

ROOT = Path(__file__).resolve().parent.parent
ZIEL = ROOT / "tests" / "preisblaetter"


def ergebnis(text, jahr):
    return fenster.extrahiere(text), vorschlag.analysiere(text, jahr)


def verkleinern(zeilen, gleich):
    """Entfernt Zeilenblöcke, solange gleich(rest) wahr bleibt (ddmin, nur Komplemente)."""
    n = 2
    while len(zeilen) >= 2:
        groesse = -(-len(zeilen) // n)
        for i in range(0, len(zeilen), groesse):
            rest = zeilen[:i] + zeilen[i + groesse:]
            if gleich(rest):
                zeilen, n = rest, max(n - 1, 2)
                break
        else:
            if n >= len(zeilen):
                break
            n = min(len(zeilen), n * 2)
    return zeilen


def soll(jahr, vid):
    pb = next(r for r in csv.DictReader(open(ROOT / "data" / str(jahr) / "preisblatt.csv", encoding="utf-8"))
              if r["vnb_id"] == vid)
    zf = [r for r in zf_lesen(ROOT / "data" / str(jahr) / "m3_zeitfenster.csv") if r["vnb_id"] == vid]
    zahl = lambda k: float(pb[k]) if pb[k] else None  # noqa: E731
    return pb, {
        "quartale": ",".join(sorted({r["quartal"] for r in zf})) or None,
        "HT": sorted({f"{r['von']}-{r['bis']}" for r in zf if r["stufe"] == "HT"}),
        "NT": sorted({f"{r['von']}-{r['bis']}" for r in zf if r["stufe"] == "NT"}),
        "std_ap": zahl("std_arbeitspreis_ct_kwh"), "m1": zahl("m1_reduzierung_eur_a"),
        "m2_ap": zahl("m2_arbeitspreis_ct_kwh"), "std_gp": zahl("std_grundpreis_eur_a"),
        "ht": zahl("m3_ht_ct_kwh"), "nt": zahl("m3_nt_ct_kwh"),
    }


def fehlerhafte_werte(voll, sollwerte):
    """Sollwerte, die die Heuristik am vollständigen Text nicht trifft."""
    f, v = voll
    ist = {"quartale": f.get("quartale"), "HT": sorted(f.get("HT") or []), "NT": sorted(f.get("NT") or []), **(v or {})}
    out = []
    for k, soll_wert in sollwerte.items():
        wert = ist.get(k)
        if isinstance(soll_wert, float) and isinstance(wert, float) and abs(wert - soll_wert) < 0.005:
            continue
        if wert != soll_wert and soll_wert is not None:
            out += ["quartale"] if k == "quartale" else soll_wert if isinstance(soll_wert, list) else [soll_wert]
    return out


def anker_zeilen(zeilen, werte):
    """Zeilen (mit Nachbarn), in denen ein Sollwert oder, bei falschen Quartalen, eine Quartalsangabe steht."""
    muster = []
    for w in werte:
        if w == "quartale":
            muster.append(r"Quartal|\bQ\s?[1-4]\b")
        elif isinstance(w, float):
            muster.append(re.escape(f"{w:.2f}".replace(".", ",")) + r"(?!\d)")
        elif isinstance(w, str) and "-" in w and ":" in w:
            for t in w.split("-"):
                h, m = t.split(":")
                if t not in ("00:00", "24:00"):
                    muster.append(rf"(?<!\d)0?{int(h)}[:.]{m}(?!\d)")
    treffer = {i for i, z in enumerate(zeilen) for p in muster if re.search(p, z)}
    return {j for i in treffer for j in (i - 1, i, i + 1) if 0 <= j < len(zeilen)}


def main(jahr, vid, besonderheit):
    jahr = int(jahr)
    pb, sollwerte = soll(jahr, vid)
    sha = pb["pdf_sha256"]
    ocr = ROOT / ".cache" / "text" / f"{sha}.ocr.txt"
    text = (ocr if ocr.exists() else ROOT / ".cache" / "text" / f"{sha}.txt").read_text(encoding="utf-8")
    voll = ergebnis(text, jahr)
    # Seitenumbrüche (\f) als eigene Zeilen behalten, extrahiere arbeitet seitenweise
    zeilen = text.replace("\f", "\n\f\n").split("\n")
    # Wo die Heuristik falsch liegt, bleiben die Zeilen mit den Sollwerten (und ihre Nachbarn) stehen,
    # damit eine spätere Korrektur am Testfall überhaupt möglich ist.
    anker = anker_zeilen(zeilen, fehlerhafte_werte(voll, sollwerte))
    frei = [i for i in range(len(zeilen)) if i not in anker]

    def text_aus(auswahl):
        return "\n".join(zeilen[i] for i in sorted(anker | set(auswahl))).replace("\n\f\n", "\f")

    rest = [zeilen[i] for i in sorted(anker | set(verkleinern(frei, lambda a: ergebnis(text_aus(a), jahr) == voll)))]
    name = f"{vid}_{jahr}"
    ZIEL.mkdir(parents=True, exist_ok=True)
    (ZIEL / f"{name}.txt").write_text("\n".join(rest).replace("\n\f\n", "\f") + "\n", encoding="utf-8")
    faelle_pfad = ZIEL / "faelle.json"
    faelle = json.loads(faelle_pfad.read_text(encoding="utf-8")) if faelle_pfad.exists() else {}
    faelle[name] = {"vnb_id": vid, "jahr": jahr, "preisblatt_url": pb["preisblatt_url"], "pdf_sha256": sha,
                    "besonderheit": besonderheit, "soll": sollwerte,
                    "bekannte_fehler": faelle.get(name, {}).get("bekannte_fehler", {})}
    faelle_pfad.write_text(json.dumps(dict(sorted(faelle.items(), key=lambda kv: (kv[1]["jahr"], int(kv[1]["vnb_id"])))),
                                      ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: {len(zeilen)} -> {len(rest)} Zeilen")


if __name__ == "__main__":
    main(*sys.argv[1:4])
