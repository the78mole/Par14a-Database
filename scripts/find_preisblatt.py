"""Sucht Preisblatt-PDFs mit §14a-Preisen auf der Webseite eines VNB.

Startet auf der gespeicherten Einstiegsseite (netzentgelt_seite_url), sonst auf der Startseite,
und folgt Links mit Stichworten wie Netzentgelte, Preisblatt, Veröffentlichungen (Breitensuche,
Same-Host). Gefundene PDFs werden geladen, nach §14a/Modul durchsucht und mit Jahr, Seiten und
SHA-256 nach .cache/kandidaten/<vnb_id>.json geschrieben, den Text legt es in .cache/text/ ab.

    python scripts/find_preisblatt.py <vnb_id> [<vnb_id> ...] [--pages 80] [--start URL]
"""
import argparse, csv, collections, hashlib, json, re, subprocess, tempfile
import urllib.parse as up
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Par14a-Database"}
STRONG = re.compile(r"netzentgelt|netznutzung|preisbl|entgelt|14a|steuerbar|veröffentlich|veroeffentlich|"
                    r"netzzugang|pflichtangabe|preise", re.I)
NAV = re.compile(r"netz|strom|download|service|marktpartner|lieferant|regulier|publikation|info", re.I)
PDFKEY = re.compile(r"preisbl|netzentgelt|netznutzung|entgelt|14a|steuerbar|modul|preise|netzentgelte", re.I)
NEG = re.compile(r"\bgas\b|erdgas|gasnetz|wasser|fernwärme|fernwaerme|wärme|karriere|presse|jobs?\b|"
                 r"einspeis|biogas|abwasser", re.I)


def is_pdf_link(h):
    return bool(re.search(r"\.pdfx?($|\?)", h, re.I)) or "download" in h.lower() or "/file" in h.lower()


def crawl(start, maxpages):
    host = up.urlparse(start).netloc.removeprefix("www.")
    s = requests.Session()
    s.headers.update(UA)
    seen, pdfs, pages = set(), {}, 0
    queue = [(10, 0, start, None)]
    while queue and pages < maxpages:
        queue.sort(key=lambda x: -x[0])
        _, depth, url, parent = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            r = s.get(url, timeout=20)
        except (requests.RequestException, ValueError):
            continue
        pages += 1
        ct = r.headers.get("content-type", "")
        if "pdf" in ct:
            pdfs.setdefault(r.url, {"linktext": "", "quelle_seite_url": parent})
            continue
        if "html" not in ct:
            continue
        soup = BeautifulSoup(r.content, "lxml")
        # PDF-Pfade, die nur in Skript-Daten stehen (z. B. Akkordeons, die per JS gefüllt werden)
        for m in re.finditer(r"""["'(]((?:https?:)?[\w/.%~:-]*?\.pdf(?:\?[^"'\s\\]*)?)["'\\]""", r.text.replace("\\/", "/"), re.I):
            h = up.urljoin(r.url, m.group(1))
            if PDFKEY.search(up.unquote(h)) and not NEG.search(up.unquote(h).rsplit("/", 1)[-1]):
                pdfs.setdefault(h, {"linktext": "", "quelle_seite_url": r.url})
        for a in soup.find_all("a", href=True):
            h = up.urljoin(r.url, a["href"].strip()).split("#")[0]
            if not h.startswith("http"):
                continue
            text = " ".join((a.get_text(" ", strip=True) + " " + (a.get("title") or "")).split())[:200]
            blob = text + " " + up.unquote(h)
            if is_pdf_link(h) and PDFKEY.search(blob):
                if not NEG.search(text):
                    pdfs.setdefault(h, {"linktext": text, "quelle_seite_url": r.url})
                continue
            if host not in up.urlparse(h).netloc or h in seen or depth >= 4 or NEG.search(blob):
                continue
            score = (5 if STRONG.search(blob) else 0) + (1 if NAV.search(blob) else 0)
            if score:
                queue.append((score - depth, depth + 1, h, r.url))
    return pdfs, pages


def analyse(url):
    try:
        r = requests.get(url, headers=UA, timeout=60)
    except (requests.RequestException, ValueError) as e:
        return {"fehler": str(e)}
    if not r.content.startswith(b"%PDF") and "html" in r.headers.get("content-type", ""):
        # Download-Zwischenseiten (z. B. WordPress Download Monitor): dort verlinktes PDF nehmen
        soup = BeautifulSoup(r.content, "lxml")
        for a in soup.find_all("a", href=True):
            h = up.urljoin(r.url, a["href"])
            if re.search(r"\.pdf|dlm|download", h, re.I) and h != url:
                try:
                    r2 = requests.get(h, headers=UA, timeout=60)
                except (requests.RequestException, ValueError):
                    continue
                if r2.content.startswith(b"%PDF"):
                    r = r2
                    break
    if not r.content.startswith(b"%PDF"):
        return {"fehler": "kein PDF"}
    sha = hashlib.sha256(r.content).hexdigest()
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(r.content)
        f.flush()
        text = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True).stdout
    (CACHE / "text").mkdir(parents=True, exist_ok=True)
    (CACHE / "text" / f"{sha}.txt").write_text(text, encoding="utf-8")
    pages = text.split("\f")
    hit = [i + 1 for i, p in enumerate(pages) if re.search(r"14\s?a", p) and re.search(r"Modul", p, re.I)]
    jahre = sorted({int(y) for y in re.findall(r"(?:ab|zum|Stand:?|vom)\s*(?:dem\s*)?(?:01\.\s?01\.|1\.\s?1\.|1\. Januar )\s?(20\d\d)", text)})
    (CACHE / "pdf").mkdir(parents=True, exist_ok=True)
    (CACHE / "pdf" / f"{sha}.pdf").write_bytes(r.content)
    bild = [i + 1 for i, p in enumerate(pages[:-1]) if len(p.strip()) < 300]
    return {"pdf_sha256": sha, "seiten_14a": hit, "bildseiten": bild, "jahre": jahre,
            "vorlaeufig": bool(re.search(r"vorläufig|vorlaeufig", text, re.I)), "seiten": len(pages)}


def run(vnb, maxpages, start=None):
    start = start or vnb.get("netzentgelt_seite_url") or vnb["website"]
    pdfs, pages = crawl(start, maxpages)
    with ThreadPoolExecutor(6) as ex:
        for u, info in zip(pdfs, ex.map(analyse, pdfs)):
            pdfs[u].update(info)
    out = {"vnb_id": vnb["vnb_id"], "name": vnb["name"], "start": start, "seiten_gecrawlt": pages,
           "pdfs": dict(sorted(pdfs.items(), key=lambda kv: -len(kv[1].get("seiten_14a") or [])))}
    (CACHE / "kandidaten").mkdir(parents=True, exist_ok=True)
    (CACHE / "kandidaten" / f"{vnb['vnb_id']}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    treffer = [(u, p) for u, p in out["pdfs"].items() if p.get("seiten_14a")]
    print(f"[{vnb['vnb_id']}] {vnb['name']}: {pages} Seiten, {len(pdfs)} PDFs, {len(treffer)} mit §14a")
    for u, p in treffer[:6]:
        print(f"    {p['jahre']} S.{p['seiten_14a']} {'vorl. ' if p['vorlaeufig'] else ''}{u}\n        <- {p['quelle_seite_url']}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--pages", type=int, default=80)
    ap.add_argument("--start")
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args()
    with (ROOT / "data" / "vnb.csv").open(encoding="utf-8") as f:
        vnbs = {r["vnb_id"]: r for r in csv.DictReader(f)}
    with ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(lambda i: run(vnbs[i], a.pages, a.start), a.ids))
