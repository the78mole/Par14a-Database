"""Spiegelt die Preisblatt-PDFs aus dem S3-Bucket nach pdfs/<jahr>/<vnb_id>/<sha256>.pdf (gitignored).

Zugangsdaten kommen nur aus der Umgebung: S3_ENDPOINT, S3_REGION, S3_BUCKET, S3_KEY, S3_SECRET
(scripts/pdf_sync.sh lädt sie aus OpenBao). Ohne Zugangsdaten bzw. mit --offline wird der Bucket
übersprungen, dann zählt nur der lokale Bestand.

Mit --import DATEI|ORDNER ... werden lokale PDFs (z. B. aus ~/Downloads) per sha256 gegen
data/<jahr>/preisblatt.csv zugeordnet, unabhängig vom Dateinamen. Nicht zuordenbare Dateien
werden nur gemeldet.

Am Ende listet das Skript je Jahr die Blätter, die in der DB stehen, aber im Bucket bzw. lokal fehlen.

  uv run --with boto3 python scripts/pdf_sync.py [--jahr 2026 ...] [--import ~/Downloads] [--offline]
"""
import argparse, csv, hashlib, os, shutil, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "pdfs"
PREFIX = "preisblaetter"


def db_eintraege(jahr):
    """{(vnb_id, sha256)} aus data/<jahr>/preisblatt.csv"""
    p = ROOT / "data" / str(jahr) / "preisblatt.csv"
    with open(p, newline="", encoding="utf-8") as f:
        return {(r["vnb_id"], r["pdf_sha256"].strip().lower()) for r in csv.DictReader(f) if r["pdf_sha256"].strip()}


def ziel(jahr, vid, sha):
    return OUT / str(jahr) / vid / f"{sha}.pdf"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def s3_client():
    need = ["S3_ENDPOINT", "S3_BUCKET", "S3_KEY", "S3_SECRET"]
    if not all(os.environ.get(k) for k in need):
        return None, None
    import boto3
    s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"], region_name=os.environ.get("S3_REGION") or "garage",
                      aws_access_key_id=os.environ["S3_KEY"], aws_secret_access_key=os.environ["S3_SECRET"])
    return s3, os.environ["S3_BUCKET"]


def bucket_schluessel(s3, b, jahr):
    """{(vnb_id, sha256)} aus preisblaetter/<jahr>/<vnb_id>/<sha256>.pdf"""
    out = set()
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=b, Prefix=f"{PREFIX}/{jahr}/"):
        for o in page.get("Contents", []):
            teile = o["Key"].split("/")
            if len(teile) == 4 and teile[3].endswith(".pdf"):
                out.add((teile[2], teile[3][:-4].lower()))
    return out


def sync_bucket(s3, b, jahr, keys):
    neu, kaputt = 0, []
    for vid, sha in sorted(keys):
        p = ziel(jahr, vid, sha)
        if p.exists():
            continue
        data = s3.get_object(Bucket=b, Key=f"{PREFIX}/{jahr}/{vid}/{sha}.pdf")["Body"].read()
        if sha256(data) != sha:
            kaputt.append((vid, sha)); continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        neu += 1
    return neu, kaputt


def importiere(pfade, jahre, db):
    """Lokale PDFs per sha256 einsortieren; liefert (kopiert, unbekannt)."""
    nach_sha = defaultdict(list)
    for j in jahre:
        for vid, sha in db[j]:
            nach_sha[sha].append((j, vid))
    dateien = []
    for p in map(Path, pfade):
        dateien += sorted(p.rglob("*.pdf")) + sorted(p.rglob("*.PDF")) if p.is_dir() else [p]
    kopiert, unbekannt = [], []
    for f in dateien:
        sha = sha256(f.read_bytes())
        if sha not in nach_sha:
            unbekannt.append(f); continue
        for j, vid in nach_sha[sha]:
            p = ziel(j, vid, sha)
            if not p.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, p)
                kopiert.append((f, j, vid))
    return kopiert, unbekannt


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jahr", type=int, action="append", help="nur diese Jahre (Standard: alle in data/)")
    ap.add_argument("--import", dest="imp", nargs="+", default=[], metavar="PFAD", help="lokale PDFs/Ordner einsortieren")
    ap.add_argument("--offline", action="store_true", help="Bucket nicht abfragen")
    a = ap.parse_args()
    jahre = a.jahr or sorted(int(p.name) for p in (ROOT / "data").iterdir() if p.name.isdigit())
    db = {j: db_eintraege(j) for j in jahre}

    s3, b = (None, None) if a.offline else s3_client()
    if not a.offline and not s3:
        print("Keine S3-Zugangsdaten in der Umgebung, Bucket wird übersprungen.", file=sys.stderr)
    im_bucket = {}
    for j in jahre:
        if not s3:
            continue
        im_bucket[j] = bucket_schluessel(s3, b, j)
        neu, kaputt = sync_bucket(s3, b, j, im_bucket[j])
        print(f"{j}: {len(im_bucket[j])} im Bucket, {neu} neu geladen")
        for vid, sha in kaputt:
            print(f"  sha256 passt nicht: {j}/{vid}/{sha}.pdf")

    if a.imp:
        kopiert, unbekannt = importiere(a.imp, jahre, db)
        for f, j, vid in kopiert:
            print(f"importiert: {f} -> {j}/{vid}")
        for f in unbekannt:
            print(f"keinem Blatt zuzuordnen: {f}")

    for j in jahre:
        lokal = {(v, s) for v, s in db[j] if ziel(j, v, s).exists()}
        print(f"\n{j}: {len(db[j])} Blätter in der DB, {len(lokal)} lokal")
        if j in im_bucket:
            fehlt = sorted(db[j] - im_bucket[j], key=lambda x: int(x[0]) if x[0].isdigit() else x[0])
            print(f"  {len(fehlt)} fehlen im Bucket:")
            for vid, sha in fehlt:
                print(f"    {vid} {sha}{'  (lokal vorhanden)' if (vid, sha) in lokal else ''}")
        fehlt_lokal = sorted(db[j] - lokal, key=lambda x: int(x[0]) if x[0].isdigit() else x[0])
        if fehlt_lokal and j not in im_bucket:
            print(f"  {len(fehlt_lokal)} fehlen lokal:")
            for vid, sha in fehlt_lokal:
                print(f"    {vid} {sha}")


if __name__ == "__main__":
    main()
