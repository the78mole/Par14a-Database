"""Zeigt je VNB die besten Preisblatt-Kandidaten für ein Jahr aus .cache/kandidaten."""
import json, re, sys
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / ".cache" / "kandidaten"


def best(vid, jahr):
    d = json.loads((CACHE / f"{vid}.json").read_text())
    out = []
    for u, p in d["pdfs"].items():
        if not p.get("pdf_sha256"):
            continue
        name = re.sub(r"\.pdf.*", "", u.rsplit("/", 1)[-1]).lower()
        sc = 2 if p.get("seiten_14a") else (0 if p.get("bildseiten") else -9)
        sc += 4 if str(jahr) in name else 0
        sc += 2 if jahr in p.get("jahre", []) else 0
        sc -= 3 if any(str(y) in name for y in range(2020, 2030) if y != jahr) else 0
        sc += 1 if re.search(r"preisbl|entgelt|netznutz", name) else 0
        sc -= 3 if re.search(r"agb|bedingung|tab|schulung|messkonzept|faq|hinweis|vereinbarung", name) else 0
        out.append((sc, u, p))
    return d, sorted(out, key=lambda x: -x[0])


if __name__ == "__main__":
    jahr = int(sys.argv[1])
    for vid in sys.argv[2:]:
        d, c = best(vid, jahr)
        print(f"[{vid}] {d['name']}")
        for sc, u, p in c[:3]:
            print(f"   {sc:+d} {p['jahre']} S.{p['seiten_14a'][:6]} B{len(p.get('bildseiten', []))} {'vorl ' if p.get('vorlaeufig') else ''}{u}")
