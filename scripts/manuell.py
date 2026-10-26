"""Legt einen Vorschlag (.cache/vorschlag) für ein manuell gelesenes Preisblatt an, Werte folgen per uebernehmen.py.

    python scripts/manuell.py <jahr> <vnb_id>:<url-teil> [...]
"""
import json, sys
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / ".cache"
jahr = int(sys.argv[1])
for a in sys.argv[2:]:
    vid, _, teil = a.partition(":")
    d = json.loads((CACHE / "kandidaten" / f"{vid}.json").read_text())
    u, p = next((u, p) for u, p in d["pdfs"].items() if teil in u and p.get("pdf_sha256"))
    (CACHE / "vorschlag" / f"{vid}_{jahr}.json").write_text(json.dumps(
        {"vnb_id": vid, "jahr": jahr, "url": u, "quelle": p.get("quelle_seite_url") or "", "sha": p["pdf_sha256"],
         "std_ap": None, "m1": None, "m2_ap": None, "std_gp": None, "ht": None, "nt": None}))
    print(vid, u)
