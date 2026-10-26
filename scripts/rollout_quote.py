"""Liest die BNetzA-Tabelle der iMSys-Roll-out-Quoten (xlsx) und schreibt data/rollout_quote.csv.

Aufruf: python scripts/rollout_quote.py <datei.xlsx> <stichtag JJJJ-MM-TT> <download-url>
Zuordnung zum VNB über den normalisierten Namen des grundzuständigen Messstellenbetreibers (gMSB),
abweichende Schreibweisen stehen in data/rollout_zuordnung.csv. Braucht openpyxl (nur lokal, nicht in CI).
"""
import csv, re, sys
from datetime import date
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
SEITE = ("https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/NetzzugangMesswesen/"
         "Mess-undZaehlwesen/iMSys/artikel.html")
FELDER = ["vnb_id", "stichtag", "msb_name", "quote_pflicht", "quote_mit_optional", "kooperation", "hinweise",
          "quelle_url", "abgerufen_am"]


def norm(s):
    s = s.lower().replace("*", "")
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    s = re.sub(r"\b(gmbh|co|kg|ag|eg|mbh|ohg|ku|aoer|se|und)\b", " ", s)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def quote(x):
    return "" if x is None or isinstance(x, str) else f"{x * 100:.2f}"


def datenstand(text):
    m = re.search(r"(\d\d)\.(\d\d)\.(\d{4})", text or "")
    return f"{m[3]}-{m[2]}-{m[1]}" if m else None


def main(xlsx, stichtag, url):
    msb = {}
    for r in openpyxl.load_workbook(xlsx, data_only=True).active.iter_rows(min_row=6, values_only=True):
        if r[0] and r[2] is not None and not str(r[0]).startswith("(*)"):
            msb[" ".join(str(r[0]).split())] = r
    by_norm = {}
    for name in msb:
        by_norm.setdefault(norm(name), []).append(name)
    with (ROOT / "data" / "rollout_zuordnung.csv").open(newline="", encoding="utf-8") as f:
        manuell = {r["vnb_id"]: " ".join(r["msb_name"].split()) for r in csv.DictReader(f)}
    with (ROOT / "data" / "vnb.csv").open(newline="", encoding="utf-8") as f:
        vnbs = list(csv.DictReader(f))
    out, fehlt = [], []
    for v in vnbs:
        name = manuell.get(v["vnb_id"]) or next(iter(by_norm.get(norm(v["name"]), [])), None)
        if name not in msb:
            fehlt.append(v)
            continue
        r = msb[name]
        hinweise = []
        if isinstance(r[2], str):
            hinweise.append(f"BNetzA: {r[2]}")
        ds = datenstand(r[5])
        out.append({"vnb_id": v["vnb_id"], "stichtag": ds or stichtag, "msb_name": name.rstrip("*").strip(),
                    "quote_pflicht": quote(r[2]), "quote_mit_optional": quote(r[4]),
                    "kooperation": "1" if name.endswith("*") else "",
                    "hinweise": "; ".join(hinweise + ([r[5].strip()] if ds else [])),
                    "quelle_url": url, "abgerufen_am": date.today().isoformat()})
    with (ROOT / "data" / "rollout_quote.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FELDER)
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} von {len(vnbs)} VNB zugeordnet, {len(fehlt)} ohne Treffer:")
    for v in fehlt:
        print(f"  {v['vnb_id']} {v['name']}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
