"""Heuristische Erkennung der Modul-3-Zeitfenster (HT/NT) und aktiven Quartale aus Preisblatt-Text.

Liefert {"quartale": "1,4", "HT": ["17:00-21:00"], "NT": [...], "sicher": bool, "grund": "..."}.
"sicher" ist nur gesetzt, wenn HT und NT gefunden, überschneidungsfrei und die Quartale explizit erkannt wurden.

    python scripts/fenster.py test        # gegen die bereits manuell erfassten Daten prüfen
"""
import re

M3 = re.compile(r"Modul\s*3|zeitvariabl|Hochlast|Niedriglast|Tarifstufe|Hochtarif|Niedrigtarif|Niedertarif", re.I)
HT = re.compile(r"\bHT\b|Hochlast|Hochtarif|Haupttarif|Hochpreis", re.I)
NT = re.compile(r"\bNT\b|Niedriglast|Niedertarif|Niedrigtarif|Nebentarif|Niedrigpreis", re.I)
ST = re.compile(r"\bST\b|Standardlast|Standardtarif|Normallast|Normaltarif", re.I)
T = r"(\d{1,2})(?:[:.](\d{2}))?"
BEREICH = re.compile(rf"(?<![\d,.]){T}\s*(?:Uhr|h)?\s*(?:-|–|—|bis)\s*{T}\s*(?:Uhr|h)?(?![\d,])")
PAAR = re.compile(r"(?<![\d,.])(\d{1,2}:\d{2})\s*(?:Uhr)?\s*(?:\||\s)\s*(\d{1,2}:\d{2})(?![\d,])")
QWORT = {"januar": 1, "februar": 1, "märz": 1, "april": 2, "mai": 2, "juni": 2,
         "juli": 3, "august": 3, "september": 3, "oktober": 4, "november": 4, "dezember": 4}


def hhmm(h, m):
    h, m = int(h), int(m or 0)
    if h > 24 or m > 59:
        return None
    return f"{h:02d}:{m:02d}"


def bereiche(z):
    out = []
    for m in BEREICH.finditer(z):
        # reine Stundenangaben ("17 - 21") nur mit Uhr/h, sonst Verwechslung mit Datums-/Zahlenbereichen
        if not (m.group(2) or m.group(4)) and not re.search(r"Uhr|h\b", z[m.end() - 4:m.end() + 4]):
            continue
        if re.match(r"\s*\d{1,2}\.\d{2}\.", z[m.start():]):  # Datum 01.01.-31.03.
            continue
        a, b = hhmm(m.group(1), m.group(2)), hhmm(m.group(3), m.group(4))
        if a and b and a != b:
            out.append((m.start(), f"{a}-{'24:00' if b == '00:00' else b}"))
    if not out:
        for m in PAAR.finditer(z):
            a, b = hhmm(*m.group(1).split(":")), hhmm(*m.group(2).split(":"))
            if a and b and a != b:
                out.append((m.start(), f"{a}-{'24:00' if b == '00:00' else b}"))
    return out


def quartale(seite):
    """Erkennt die aktiven Quartale; None, wenn nichts Eindeutiges gefunden."""
    s = re.sub(r"\s+", " ", seite)
    akt, inakt = set(), set()
    for z in seite.splitlines():
        m = re.search(r"(?:Quartal|Q)\s*([1-4])(?:\s*(?:-|–|bis)\s*([1-4]))?|([1-4])\.\s*Quartal", z)
        if not m:
            continue
        if m.group(3):
            qs = [int(m.group(3))]
        else:
            qs = list(range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1))
        rest = z[m.end():]
        if re.search(r"\bnein\b|keine Anwendung|nicht aktiv|entfällt|\binaktiv", rest, re.I):
            inakt.update(qs)
        elif re.search(r"\bja\b|\bx\b|✓|Anwendung|\baktiv|gilt", rest, re.I) or bereiche(rest):
            akt.update(qs)
    if akt:
        return sorted(akt - inakt) if akt - inakt else None
    for pat in (r"(?:Quartal(?:e|en)?|Q)\s*([1-4])\s*(?:,|und|&|sowie)\s*(?:Quartal|Q)?\s*([1-4])(?:\s*(?:,|und)\s*(?:Q)?([1-4]))?",
                r"([1-4])\.\s*(?:Quartal)?\s*(?:,|und|&|sowie)\s*([1-4])\.\s*Quartal"):
        m = re.search(pat, s)
        if m:
            return sorted({int(g) for g in m.groups() if g})
    m = re.findall(r"(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*(?:-|–|bis)\s*"
                   r"(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)", s)
    if m:
        qs = set()
        for a, b in m:
            qs.update(range(QWORT[a.lower()], QWORT[b.lower()] + 1))
        return sorted(qs)
    m = re.findall(r"01\.(01|04|07|10)\.(?:\d{2,4})?\s*(?:-|–|bis)\s*3[01]\.(03|06|09|12)\.", s)
    if m:
        qs = set()
        for a, b in m:
            qs.update(range((int(a) + 2) // 3, int(b) // 3 + 1))
        return sorted(qs)
    if re.search(r"ganzjährig|alle(?:n)? (?:vier )?Quartale|Quartal(?:e)? 1\s*(?:-|–|bis)\s*4", s, re.I):
        return [1, 2, 3, 4]
    return None


def extrahiere(text):
    seiten = [p for p in text.split("\f") if M3.search(p)]
    best = None
    for seite in seiten:
        zeilen = seite.splitlines()
        f = {"HT": [], "NT": []}
        for i, z in enumerate(zeilen):
            stufen = [(k, p) for k, p in (("HT", HT), ("NT", NT)) if p.search(z)]
            if not stufen:
                continue
            if ST.search(z) or len(stufen) == 2:
                # Kopfzeile mit mehreren Stufen: Zeiten der Folgezeilen nach Spaltenposition zuordnen
                koepfe = sorted([(m.start(), k) for k, p in (("HT", HT), ("NT", NT), ("ST", ST)) for m in p.finditer(z)])
                if len({k for _, k in koepfe}) >= 2:
                    for zz in zeilen[i + 1:i + 8]:
                        for pos, b in bereiche(zz):
                            k = min(koepfe, key=lambda kp: abs(kp[0] - pos))[1]
                            if k in f and b not in f[k]:
                                f[k].append(b)
                    continue
            k = stufen[0][0]
            gef = bereiche(z)
            j = i + 1
            while not gef and j < min(len(zeilen), i + 3) and not (HT.search(zeilen[j]) or NT.search(zeilen[j]) or ST.search(zeilen[j])):
                gef = bereiche(zeilen[j])
                j += 1
            for _, b in gef:
                if b not in f[k]:
                    f[k].append(b)
        if f["HT"] and (not best or len(f["HT"]) + len(f["NT"]) > len(best[0]["HT"]) + len(best[0]["NT"])):
            best = (f, seite)
    if not best:
        return {"sicher": False, "grund": "keine Zeitfenster erkannt"}
    f, seite = best
    q = quartale(seite)
    res = {"quartale": ",".join(map(str, q)) if q else None, **f}
    gr = []
    if not f["NT"]:
        gr.append("kein NT-Fenster")
    if not q:
        gr.append("Quartale unklar")
    if set(f["HT"]) & set(f["NT"]):
        gr.append("HT/NT überschneiden sich")
    res["sicher"] = not gr
    res["grund"] = ", ".join(gr)
    return res


if __name__ == "__main__":
    import csv, sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(ROOT / "scripts"))
    if sys.argv[1] == "test":
        soll = {}
        for r in csv.DictReader(open(ROOT / "data/2026/m3_zeitfenster.csv")):
            s = soll.setdefault(r["vnb_id"], {"q": set(), "HT": set(), "NT": set()})
            s["q"].add(int(r["quartal"]))
            if r["stufe"] in ("HT", "NT"):
                s[r["stufe"]].add(f"{r['von']}-{r['bis']}")
        ok = 0
        for r in csv.DictReader(open(ROOT / "data/2026/preisblatt.csv")):
            p = ROOT / ".cache/text" / f"{r['pdf_sha256']}.txt"
            o = ROOT / ".cache/text" / f"{r['pdf_sha256']}.ocr.txt"
            if not p.exists():
                print(r["vnb_id"], "kein Text")
                continue
            e = extrahiere((o if o.exists() else p).read_text())
            s = soll.get(r["vnb_id"], {"q": set(), "HT": set(), "NT": set()})
            treffer = (e.get("quartale") == ",".join(map(str, sorted(s["q"]))) and set(e.get("HT", [])) == s["HT"]
                       and set(e.get("NT", [])) == s["NT"])
            ok += treffer and e["sicher"]
            print(r["vnb_id"], "OK " if treffer else "ABW", "sicher" if e["sicher"] else "unsicher", e if not treffer else "",
                  "" if treffer else {k: sorted(v) for k, v in s.items()})
        print("korrekt & sicher:", ok)
