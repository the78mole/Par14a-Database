"""Gibt die §14a-relevanten Seiten eines Kandidaten-PDFs kompakt aus (zum Auswerten).

Seiten ohne Textebene werden per OCR gelesen (Ergebnis wird gecacht). Mit --bild N,M werden
die Seiten als PNG nach .cache/img/ gerendert, um Tabellen direkt anzusehen.

    python scripts/zeige.py <vnb_id> <url-teilstring> [--alle-seiten] [--bild 3,4]
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / ".cache"
vid, needle = sys.argv[1], sys.argv[2]
d = json.loads((CACHE / "kandidaten" / f"{vid}.json").read_text())
url, p = next((u, p) for u, p in d["pdfs"].items() if needle in u and p.get("pdf_sha256"))
sha = p["pdf_sha256"]
pdf = CACHE / "pdf" / f"{sha}.pdf"
if "--bild" in sys.argv:
    (CACHE / "img").mkdir(exist_ok=True)
    for n in sys.argv[sys.argv.index("--bild") + 1].split(","):
        subprocess.run(["pdftoppm", "-r", "110", "-f", n, "-l", n, "-png", "-singlefile", str(pdf),
                        str(CACHE / "img" / f"{vid}_{sha[:8]}_{n}")])
        print(CACHE / "img" / f"{vid}_{sha[:8]}_{n}.png")
    sys.exit()
ocr = CACHE / "text" / f"{sha}.ocr.txt"
if not ocr.exists():
    pages = (CACHE / "text" / f"{sha}.txt").read_text().split("\f")
    for i in p.get("bildseiten", []):
        if i > 60:
            break
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["pdftoppm", "-r", "250", "-f", str(i), "-l", str(i), "-png", "-singlefile", str(pdf), f"{d}/p"])
            pages[i - 1] += "\n[OCR]\n" + subprocess.run(["tesseract", f"{d}/p.png", "-", "-l", "deu", "--psm", "6"],
                                                         capture_output=True, text=True).stdout
    ocr.write_text("\f".join(pages))
pages = ocr.read_text().split("\f")
REL = r"14\s?a|Modul|Tarifstufe|Netzentgeltreduzierung|Hochlast|Niedriglast|ohne\s+(Leistungsmessung|registrierende|Lastgang)|Standardlastprofil"
want = {i + 1 for i, t in enumerate(pages) if re.search(r"Hochlast|Niedriglast|Tarifzeit|Zeitfenster", t) or re.search(r"\d+,\d\d", t) and (
    re.search(r"Modul|Tarifstufe|Netzentgeltreduzierung|Hochlast|Niedriglast", t, re.I)
    or re.search(r"ohne\s+(Leistungsmessung|registrierende|Lastgang)|Standardlastprofil|SLP", t))}
if "--alle-seiten" in sys.argv:
    want = set(range(1, len(pages) + 1))
print("URL", url, "\nVON", p["quelle_seite_url"], "\nSHA", p["pdf_sha256"], "\nSEITEN", sorted(want))
for i in sorted(want):
    t = pages[i - 1]
    lines = [re.sub(r"\s{3,}", " | ", l.strip()) for l in t.splitlines() if l.strip()]
    print(f"\n===== S.{i} =====")
    # Fließtext ohne Zahlen weglassen, Tabellen und Überschriften behalten
    keep = [l for l in lines if re.search(r"\d", l) or len(l.split()) <= 8 or re.search(r"Modul|Quartal|Tarifstufe|gültig", l, re.I)]
    print("\n".join(keep))
