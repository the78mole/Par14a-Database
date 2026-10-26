"""Schlägt §14a-Werte für einen VNB aus den gecrawlten PDFs vor (zur manuellen Prüfung).

Kernidee: Modul 1 und 2 hängen fest am Standard-Arbeitspreis AP (NS ohne Leistungsmessung):
  M1 = 67,23 € + 3.750 kWh × AP × 0,2   (= 67,23 + 7,5 × AP [ct/kWh])
  M2 = 0,4 × AP
Ein Zahlentripel (AP, M1, M2), das diese Formeln erfüllt, identifiziert das Preisblatt sicher.
HT/NT werden in den Korridoren AP < HT ≤ 2·AP und 0,1·AP ≤ NT ≤ 0,4·AP gesucht; die Zeitfenster
werden als Textausschnitt ausgegeben.

    python scripts/vorschlag.py <jahr> <vnb_id> [<vnb_id> ...]
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
NUM = re.compile(r"(?<![\d.,])-?\s?(\d{1,3}(?:\.\d{3})*,\d{2,4})(?![\d,])")
ZEIT = re.compile(r"\d{1,2}[:.]\d{2}\s*(?:Uhr)?\s*(?:-|–|bis)\s*\d{1,2}[:.]\d{2}|\d{1,2}\s*(?:-|–|bis)\s*\d{1,2}\s*(?:Uhr|h)\b")


def zahl(s):
    return float(s.replace(".", "").replace(",", "."))


def text_mit_ocr(p):
    sha = p["pdf_sha256"]
    ocr = CACHE / "text" / f"{sha}.ocr.txt"
    if ocr.exists():
        return ocr.read_text()
    pages = (CACHE / "text" / f"{sha}.txt").read_text().split("\f")
    bild = p.get("bildseiten", [])
    if bild and len(bild) <= 25:
        pdf = CACHE / "pdf" / f"{sha}.pdf"
        for i in bild:
            with tempfile.TemporaryDirectory() as d:
                subprocess.run(["pdftoppm", "-r", "250", "-f", str(i), "-l", str(i), "-png", "-singlefile", str(pdf), f"{d}/p"])
                pages[i - 1] += "\n[OCR]\n" + subprocess.run(
                    ["tesseract", f"{d}/p.png", "-", "-l", "deu", "--psm", "6"], capture_output=True, text=True).stdout
        ocr.write_text("\f".join(pages))
    return "\f".join(pages)


def kandidaten(vid, jahr):
    d = json.loads((CACHE / "kandidaten" / f"{vid}.json").read_text())
    out = []
    for u, p in d["pdfs"].items():
        if not p.get("pdf_sha256"):
            continue
        name = up_name = re.sub(r"\.pdf.*", "", u.rsplit("/", 1)[-1]).lower()
        andere = any(str(y) in name for y in range(2018, 2031) if y != jahr)
        sc = (4 if str(jahr) in name else 0) + (2 if jahr in p.get("jahre", []) else 0) - (3 if andere and str(jahr) not in name else 0)
        sc += 2 if p.get("seiten_14a") else 0
        sc -= 3 if re.search(r"agb|bedingung|tab_|schulung|messkonzept|faq|vereinbarung|anmeldung|formular|datenblatt", name) else 0
        out.append((sc, u, p))
    return d, sorted(out, key=lambda x: -x[0])


def analysiere(text, jahr):
    zeilen = text.splitlines()
    werte = {}
    for i, z in enumerate(zeilen):
        for m in NUM.finditer(z):
            werte.setdefault(zahl(m.group(1)), []).append(i)
    tripel = []
    for ap in [w for w in werte if 1.5 <= w <= 16]:
        m1 = round(67.23 + 7.5 * ap, 2)
        m1h = sorted([w for w in werte if abs(w - m1) <= 0.03], key=lambda w: abs(w - m1))
        m2h = [w for w in werte if abs(w - round(0.4 * ap, 2)) <= 0.011]
        if m1h:
            tripel.append((len(m2h) > 0, len(werte[ap]), ap, m1h[0], m2h[0] if m2h else None))
    if not tripel:
        return None
    tripel.sort(reverse=True)
    _, _, ap, m1, m2 = tripel[0]
    v = {"std_ap": ap, "m1": m1, "m2_ap": m2}
    brutto = {w for w in werte if any(abs(x * 1.19 - w) <= 0.011 for x in werte if x != w)}
    # Grundpreis: Zahlen auf Zeilen mit "Grundpreis"/"Grundbetrag" oder auf der AP-Zeile; PRICAT €/Tag × 365
    gp = []
    for i, z in enumerate(zeilen):
        if re.search(r"Grundpreis|Grundbetrag|Jahrespreis", z, re.I) or i in werte[ap]:
            for m in NUM.finditer(z):
                c = zahl(m.group(1))
                if 15 <= c <= 300 and c not in (ap, m1) and c not in brutto:
                    gp.append(c)
                elif re.search(r"€/Tag|EUR/Tag", z) and 0.04 <= c <= 0.9:
                    gp.append(round(c * 365, 2))
    v["std_gp"] = max(set(gp), key=gp.count) if gp else None

    def stufe(lo, hi, pat):
        c = [w for w in werte if lo <= w <= hi and w != ap and w not in brutto
             for i in werte[w] if re.search(pat, zeilen[i] + " " + zeilen[i - 1])
             and not re.search(r"Leistungspreis|€/kW|EUR/kW", zeilen[i])]
        return max(set(c), key=lambda w: (c.count(w), w)) if c else None
    v["ht"] = stufe(ap + 0.01, 2 * ap + 0.011, r"\bHT\b|Hochlast|Hochtarif|Haupttarif")
    v["nt"] = stufe(0.1 * ap - 0.011, 0.4 * ap + 0.011, r"\bNT\b|Niedriglast|Niedertarif|Niedrigtarif|Nebentarif")
    return v


def zeitfenster(text):
    zeilen = text.splitlines()
    idx = [i for i, z in enumerate(zeilen) if ZEIT.search(z) and not re.search(r"Montag|Mo\.?\s*-\s*Fr|Werktag|Arbeitszeit|Sperr", z)]
    # nur Blöcke in der Nähe von Modul 3/HT/NT
    nah = [i for i in idx if any(re.search(r"Modul 3|Hochlast|Niedriglast|Tarifstufe|HT|NT|Quartal|Hochtarif|Niedertarif", zeilen[j])
                                 for j in range(max(0, i - 12), min(len(zeilen), i + 6)))]
    keep = sorted({j for i in nah for j in range(max(0, i - 2), min(len(zeilen), i + 2))})
    return "\n".join(re.sub(r"\s{3,}", " | ", zeilen[j].strip()) for j in keep if zeilen[j].strip())[:2500]


def m3_seite(vid, url_teil):
    """Gibt die Seiten mit Modul-3-Angaben vollständig aus."""
    d = json.loads((CACHE / "kandidaten" / f"{vid}.json").read_text())
    u, p = next((u, p) for u, p in d["pdfs"].items() if url_teil in u and p.get("pdf_sha256"))
    for i, t in enumerate(text_mit_ocr(p).split("\f")):
        if re.search(r"Hochlast|Hochtarif|Niedriglast|Niedrigtarif|Modul 3|HT-Zeit", t):
            print(f"== [{vid}] S.{i + 1}")
            print("\n".join(re.sub(r"\s{3,}", " | ", z.strip()) for z in t.splitlines() if z.strip() and (
                re.search(r"\d", z) or len(z.split()) < 9)))


if __name__ == "__main__" and sys.argv[1] == "m3":
    for a in sys.argv[2:]:
        vid, _, teil = a.partition(":")
        m3_seite(vid, teil)
    sys.exit()

if __name__ == "__main__":
    jahr = int(sys.argv[1])
    for vid in sys.argv[2:]:
        try:
            d, cands = kandidaten(vid, jahr)
        except FileNotFoundError:
            print(f"### [{vid}] kein Crawl")
            continue
        treffer = None
        for sc, u, p in cands[:8]:
            name = u.rsplit("/", 1)[-1]
            if any(str(y) in name for y in range(jahr + 1, 2031)):
                continue
            if sc < 0 or (re.search(r"20(2[0-9]|3[0-9])", name) and str(jahr) not in name
                          and not re.search(rf"{jahr % 100:02d}0101|0101{jahr % 100:02d}", name)):
                continue
            t = text_mit_ocr(p)
            if not re.search(rf"{jahr}", t):
                continue
            v = analysiere(t, jahr)
            if v:
                treffer = (u, p, v, t)
                break
        print(f"### [{vid}] {d['name']}")
        if not treffer:
            print("   KEIN TREFFER; Kandidaten:", [u.rsplit('/', 1)[-1][:60] for _, u, _ in cands[:5]])
            continue
        u, p, v, t = treffer
        (CACHE / "vorschlag").mkdir(exist_ok=True)
        (CACHE / "vorschlag" / f"{vid}_{jahr}.json").write_text(json.dumps(
            {"vnb_id": vid, "jahr": jahr, "url": u, "quelle": p.get("quelle_seite_url") or "", "sha": p["pdf_sha256"],
             "vorlaeufig": bool(re.search(r"vorläufig|voraussichtlich|indikativ", u + t[:3000], re.I)), **v}))
        print("   URL", u)
        print("   VON", p.get("quelle_seite_url"))
        print("   VORSCHLAG", json.dumps(v), "vorl" if re.search(r"vorläufig|voraussichtlich|indikativ", t, re.I) else "")
        q = re.findall(r"(?:Quartal|Q\s?[1-4])[^\n]{0,120}", t)
        print("   ZEITEN:\n      " + zeitfenster(t).replace("\n", "\n      "))
