"""Prüft, ob sich die erfassten Preisblätter geändert haben: lädt jede preisblatt_url aus
data/<jahr>/preisblatt.csv neu und vergleicht den SHA-256 mit pdf_sha256.

    python scripts/pruefe_aenderungen.py 2026 2027 [--jobs 12] > aenderungen.tsv

Ausgabe (TSV): jahr, vnb_id, ergebnis (gleich|geaendert|http_<code>|kein_pdf|fehler), neuer sha256, url.
Geänderte PDFs landen wie beim Crawl in .cache/pdf/ und .cache/text/. VNB mit Bot-Schutz werden nicht
umgangen, sie erscheinen einfach als http_403.
"""
import argparse, csv, hashlib, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Par14a-Database"}


def pruefe(row):
    url, alt = row["preisblatt_url"], row["pdf_sha256"]
    try:
        r = requests.get(url, headers=UA, timeout=60)
    except (requests.RequestException, ValueError) as e:
        return "fehler", "", type(e).__name__
    if r.status_code != 200:
        return f"http_{r.status_code}", "", ""
    if not r.content.startswith(b"%PDF"):
        return "kein_pdf", "", r.headers.get("content-type", "")
    sha = hashlib.sha256(r.content).hexdigest()
    if sha == alt:
        return "gleich", sha, ""
    (CACHE / "pdf").mkdir(parents=True, exist_ok=True)
    (CACHE / "text").mkdir(parents=True, exist_ok=True)
    pdf = CACHE / "pdf" / f"{sha}.pdf"
    pdf.write_bytes(r.content)
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    (CACHE / "text" / f"{sha}.txt").write_text(text, encoding="utf-8")
    return "geaendert", sha, ""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("jahre", nargs="+")
    ap.add_argument("--jobs", type=int, default=12)
    a = ap.parse_args()
    rows = [r for j in a.jahre for r in csv.DictReader(open(ROOT / "data" / j / "preisblatt.csv", encoding="utf-8"))
            if r["preisblatt_url"].startswith("http")]
    w = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
    w.writerow(["jahr", "vnb_id", "ergebnis", "sha256_neu", "info", "url"])
    with ThreadPoolExecutor(a.jobs) as ex:
        for r, (erg, sha, info) in zip(rows, ex.map(pruefe, rows)):
            w.writerow([r["jahr"], r["vnb_id"], erg, sha, info, r["preisblatt_url"]])
            sys.stdout.flush()
