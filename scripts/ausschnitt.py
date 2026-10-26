"""Schneidet den Modul-3-Bereich (Preise + Zeitfenster) aus dem vorgeschlagenen Preisblatt aus und
setzt mehrere VNBs mit Beschriftung zu einem Prüfbild zusammen (zur visuellen Kontrolle).

    python scripts/ausschnitt.py <jahr> <ausgabe.png> <vnb_id> [<vnb_id> ...]
"""
import html, json, re, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
DPI = 100
KEY = re.compile(r"^(Modul|Hochlast|Niedriglast|Hochtarif|Niedrigtarif|Niedertarif|Zeitfenster|Tarifstufe|Tarifzeit|HT|NT|Quartal)", re.I)
ZEIT = re.compile(r"^\d{1,2}[:.]\d{2}")
WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')


def seiten_woerter(pdf):
    out = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True).stdout
    seiten = []
    for p in out.split("<page ")[1:]:
        h = float(re.search(r'height="([\d.]+)"', p).group(1))
        w = float(re.search(r'width="([\d.]+)"', p).group(1))
        seiten.append((w, h, [(float(a), float(b), float(c), float(d), html.unescape(t)) for a, b, c, d, t in WORD.findall(p)]))
    return seiten


def bereiche(pdf, bildseiten, ocr=None):
    """Liefert [(seite, y0, y1, h, x0, x1)]; ganze Seite für Bildseiten mit M3-Begriffen im OCR-Text."""
    res = []
    ocr_seiten = ocr.read_text().split("\f") if ocr and ocr.exists() else []
    bild_ohne_ocr = []
    for n, (w, h, ws) in enumerate(seiten_woerter(pdf), 1):
        txt = " ".join(t for *_, t in ws)
        if n in bildseiten:
            if not ocr_seiten:
                bild_ohne_ocr.append((n, 0, h, h, 0, 1))
                continue
            if n <= len(ocr_seiten) and not re.search(r"Modul\s*3|Hochlast|Niedriglast|Hochtarif|Niedrigtarif|Niedertarif|Tarifstufe", ocr_seiten[n - 1], re.I):
                continue
            res.append((n, 0, h, h, 0, 1))
            continue
        if not re.search(r"Modul\s*3|zeitvariabl|Hochlast|Niedriglast|Hochtarif|Niedrigtarif", txt, re.I):
            continue
        zeiten = [y for _, y, _, _, t in ws if ZEIT.match(t)]
        keys = [y for _, y, _, _, t in ws if KEY.match(t)]
        if not zeiten:
            continue
        # Zeitwerte, die nahe an M3-Schlüsselwörtern liegen
        zeiten = [y for y in zeiten if any(abs(y - k) < 250 for k in keys)]
        if not zeiten:
            continue
        y0 = min([y for y in keys if min(zeiten) - 250 < y <= min(zeiten)] or [min(zeiten)]) - 25
        y1 = max(zeiten) + 90
        xs = [(a, c) for a, b, c, _, _ in ws if y0 <= b <= y1]
        x0, x1 = min(a for a, _ in xs) - 10, max(c for _, c in xs) + 10
        res.append((n, max(0, y0), min(h, y1), h, max(0, x0) / w, min(w, x1) / w))
    return res or bild_ohne_ocr


def render(pdf, n, y0, y1, h, fx0, fx1):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-r", str(DPI), "-f", str(n), "-l", str(n), "-png", "-singlefile", str(pdf), f"{d}/p"], check=True)
        im = Image.open(f"{d}/p.png")
        im.load()
    s = im.height / h
    return im.crop((int(fx0 * im.width), int(y0 * s), int(fx1 * im.width), int(y1 * s)))


def main():
    jahr, ziel, ids = int(sys.argv[1]), sys.argv[2], sys.argv[3:]
    teile = []
    font = ImageFont.load_default(size=18)
    for vid in ids:
        v = json.loads((CACHE / "vorschlag" / f"{vid}_{jahr}.json").read_text())
        k = json.loads((CACHE / "kandidaten" / f"{vid}.json").read_text())
        p = k["pdfs"][v["url"]]
        pdf = CACHE / "pdf" / f"{v['sha']}.pdf"
        txt = (CACHE / "text" / f"{v['sha']}.txt").read_text()[:4000]
        gab = re.search(r"(?:gültig|Gültig|GÜLTIG)\s*(?:ab|vom)?\s*(?:dem\s*)?(\d{1,2}\.\s*\w+\.?\s*\d{4})", txt)
        vorl = "VORL? " if re.search(r"vorläufig|voraussichtlich", txt, re.I) else ""
        label = f"{vorl}{gab.group(1) if gab else ''} [{vid}] AP {v['std_ap']} M1 {v['m1']} M2 {v.get('m2_ap')} HT {v.get('ht')} NT {v.get('nt')} GP {v.get('std_gp')}"
        crops = [render(pdf, *b) for b in bereiche(pdf, set(p.get("bildseiten", [])), CACHE / "text" / f"{v['sha']}.ocr.txt")][:2]
        kopf = Image.new("RGB", (1000, 30), "white")
        ImageDraw.Draw(kopf).text((5, 4), label, fill=0, font=font)
        teile += [kopf] + crops + [Image.new("RGB", (1000, 6), "black")]
    # in Bilder von höchstens ~1700 px Höhe aufteilen (bleiben beim Ansehen lesbar)
    seiten, akt = [], []
    for t in teile:
        if t.height > 1700:
            t = t.resize((int(t.width * 1700 / t.height), 1700))
        if akt and t.height == 30 and sum(x.height for x in akt) + 300 > 1700:
            seiten.append(akt)
            akt = []
        elif akt and sum(x.height for x in akt) + t.height > 1700:
            seiten.append(akt)
            akt = []
        akt.append(t)
    seiten.append(akt)
    for i, s in enumerate(seiten, 1):
        bild = Image.new("RGB", (max(t.width for t in s), sum(t.height for t in s)), "white")
        y = 0
        for t in s:
            bild.paste(t, (0, y))
            y += t.height
        name = ziel.replace(".png", f"_{i}.png")
        bild.save(name)
        print(name, bild.size)

if __name__ == "__main__":
    main()
