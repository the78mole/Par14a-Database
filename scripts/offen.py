"""Listet VNB-IDs mit Vorschlag (.cache/vorschlag), die noch nicht in data/<jahr>/preisblatt.csv stehen."""
import csv, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
jahr = sys.argv[1]
done = {r["vnb_id"] for r in csv.DictReader(open(ROOT / "data" / jahr / "preisblatt.csv"))}
ids = sorted({p.name.split("_")[0] for p in (ROOT / ".cache" / "vorschlag").glob(f"*_{jahr}.json")} - done, key=int)
print(" ".join(ids[:int(sys.argv[2])] if len(sys.argv) > 2 else ids))
