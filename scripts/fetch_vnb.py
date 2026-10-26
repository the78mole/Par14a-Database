# /// script
# requires-python = ">=3.9"
# dependencies = ["vnbdigital-client @ git+https://github.com/the78mole/vnbdigital-client"]
# ///
"""Holt alle Netzbetreiber aus vnbdigital.de und aktualisiert data/vnb.csv.

vnbdigital bietet keine Liste aller VNBs, deshalb werden die IDs durchprobiert.
Felder, die von Hand gepflegt werden (netzentgelt_seite_url, letzte_pruefung, bdew_code),
bleiben erhalten.

    uv run scripts/fetch_vnb.py [max_id]
"""
import csv, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from vnbdigital_client import VNBDigitalClient

CSV = Path(__file__).resolve().parent.parent / "data" / "vnb.csv"
FIELDS = ["vnb_id", "name", "bdew_code", "website", "plz", "ort", "spannungsebenen",
          "netzentgelt_seite_url", "letzte_pruefung", "quelle_stammdaten"]
QUERY = """query ($id: ID!) { vnb_vnb(id: $id) { ... on vnb_VNB {
  _id name types website postcode city } } }"""


def fetch(client, i):
    for _ in range(3):
        try:
            return client._execute(QUERY, {"id": str(i)}).get("vnb_vnb")
        except Exception:
            pass
    return None


def main(max_id=12000):
    client = VNBDigitalClient()
    with ThreadPoolExecutor(16) as ex:
        found = [v for v in ex.map(lambda i: fetch(client, i), range(1, max_id)) if v]
    old = {}
    if CSV.exists():
        with CSV.open(encoding="utf-8") as f:
            old = {r["vnb_id"]: r for r in csv.DictReader(f)}
    rows = []
    for v in found:
        r = old.get(v["_id"], {})
        r.update(vnb_id=v["_id"], name=v["name"], website=v.get("website") or "",
                 plz=v.get("postcode") or "", ort=v.get("city") or "",
                 spannungsebenen=",".join(v.get("types") or []), quelle_stammdaten="vnbdigital")
        rows.append({k: r.get(k, "") for k in FIELDS})
    rows.sort(key=lambda r: int(r["vnb_id"]))
    with CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} VNBs -> {CSV}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12000)
