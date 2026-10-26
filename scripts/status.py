"""Schreibt STATUS.md: Fortschritt der Erfassung je Jahr (erfasst/fehlend, Kategorien, zuletzt ergänzt).

    python scripts/status.py <jahr> [--crawl .cache/recrawl.log]
"""
import argparse, csv, datetime, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
BOTSCHUTZ = {"535", "1000", "1064", "1068", "7137", "7332", "7510", "7750"}

ap = argparse.ArgumentParser()
ap.add_argument("jahr")
ap.add_argument("--crawl")
ap.add_argument("--crawl-gesamt", type=int)
a = ap.parse_args()

vnb = {r["vnb_id"]: r for r in csv.DictReader(open(ROOT / "data" / "vnb.csv", encoding="utf-8"))}
pb = list(csv.DictReader(open(ROOT / "data" / a.jahr / "preisblatt.csv", encoding="utf-8")))
erfasst = {r["vnb_id"] for r in pb}
fehlend = [i for i in vnb if i not in erfasst]


def kategorie(i):
    if i in BOTSCHUTZ:
        return "Bot-Schutz (HTTP 403), nur manuell"
    k = CACHE / "kandidaten" / f"{i}.json"
    if not k.exists():
        return "noch nicht gecrawlt"
    pdfs = json.loads(k.read_text())["pdfs"].values()
    if not any(p.get("seiten_14a") for p in pdfs):
        return "kein §14a-Preisblatt auf der Webseite gefunden"
    if not any(p.get("seiten_14a") and a.jahr in json.dumps(p.get("jahre", [])) for p in pdfs):
        return f"§14a-PDF vorhanden, aber nicht eindeutig {a.jahr}"
    return "§14a-PDF vorhanden, manuelle Prüfung offen"


kat = {}
for i in fehlend:
    kat.setdefault(kategorie(i), []).append(i)

st = {}
for r in pb:
    st[r["status"]] = st.get(r["status"], 0) + 1
m3 = sum(1 for r in pb if r["m3_quartale_aktiv"])
neu = sorted(pb, key=lambda r: r["abgerufen_am"], reverse=True)

z = [f"# Status der §14a-Preisdatenbank {a.jahr}", "",
     f"Stand: {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC (wird nach jedem Arbeitsschritt aktualisiert)", "",
     f"**{len(erfasst)} von {len(vnb)} VNB erfasst ({100 * len(erfasst) / len(vnb):.0f} %)**, {len(fehlend)} fehlen noch.", "",
     "| Erfasst | Anzahl |", "|---|---:|"]
z += [f"| {k} | {v} |" for k, v in sorted(st.items())]
z += [f"| davon mit Modul-3-Zeitfenstern | {m3} |", ""]
if a.crawl and Path(a.crawl).exists():
    fertig = sum(1 for l in open(a.crawl, encoding="utf-8") if re.match(r"\[\d+\]", l))
    ges = a.crawl_gesamt or len(fehlend)
    z += ["## Laufender Crawl", "", f"Tieferer Neu-Crawl der fehlenden VNB (bis 250 Seiten je Webseite): {fertig} von {ges} fertig.", ""]
z += ["## Fehlende VNB nach Grund", "", "| Grund | Anzahl |", "|---|---:|"]
z += [f"| {k} | {len(v)} |" for k, v in sorted(kat.items(), key=lambda kv: -len(kv[1]))]
z += ["", "<details><summary>Liste der fehlenden VNB</summary>", ""]
for k, v in sorted(kat.items(), key=lambda kv: -len(kv[1])):
    z += [f"**{k}**", ""] + [f"- {i} {vnb[i]['name']}" for i in sorted(v, key=int)] + [""]
z += ["</details>", ""]
(ROOT / "STATUS.md").write_text("\n".join(z), encoding="utf-8")
print("\n".join(z[:12]))
