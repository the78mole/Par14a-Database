"""Baut die Webseite nach dist/web: web/* plus daten/<jahr>.json, daten/jahre.json und daten/badge.json aus data/."""
import csv, json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZAHLEN = ["std_grundpreis_eur_a", "std_arbeitspreis_ct_kwh", "m1_reduzierung_eur_a", "m2_grundpreis_eur_a",
          "m2_arbeitspreis_ct_kwh", "m3_ht_ct_kwh", "m3_st_ct_kwh", "m3_nt_ct_kwh"]
TEXTE = ["gueltig_ab", "status", "preisblatt_url", "quelle_seite_url", "seite", "m3_quartale_aktiv",
         "abgerufen_am", "hinweise"]


def read(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def jahr_json(jahr, vnbs, rollout):
    pbs = {r["vnb_id"]: r for r in read(ROOT / "data" / jahr / "preisblatt.csv") if r["jahr"] == jahr}
    zf = {}
    for r in read(ROOT / "data" / jahr / "m3_zeitfenster.csv"):
        if r["jahr"] == jahr:
            zf.setdefault(r["vnb_id"], {})[r["quartal"]] = {s: [x for x in r[s].split("|") if x] for s in ("ht", "nt")}
    out = []
    for v in vnbs:
        e = {k: v[k] for k in ("vnb_id", "name", "plz", "ort", "website", "netzentgelt_seite_url") if v[k]}
        pb = pbs.get(v["vnb_id"])
        if pb:
            e["pb"] = {k: pb[k] for k in TEXTE if pb[k]}
            e["pb"].update({k: float(pb[k]) for k in ZAHLEN if pb[k]})
            if v["vnb_id"] in zf:
                e["pb"]["zf"] = zf[v["vnb_id"]]
        ro = rollout.get(v["vnb_id"])
        if ro:
            e["ro"] = {k: ro[k] for k in ("stichtag", "msb_name", "hinweise", "quelle_url") if ro[k]}
            e["ro"].update({k: float(ro[k]) for k in ("quote_pflicht", "quote_mit_optional") if ro[k]})
            if ro["kooperation"]:
                e["ro"]["kooperation"] = True
        out.append(e)
    return out


def main(ziel):
    shutil.rmtree(ziel, ignore_errors=True)
    shutil.copytree(ROOT / "web", ziel)
    (ziel / "daten").mkdir()
    vnbs = read(ROOT / "data" / "vnb.csv")
    rollout = {r["vnb_id"]: r for r in read(ROOT / "data" / "rollout_quote.csv")}
    jahre = sorted((p.name for p in (ROOT / "data").iterdir() if p.is_dir() and p.name.isdigit()), reverse=True)
    for j in jahre:
        daten = jahr_json(j, vnbs, rollout)
        (ziel / "daten" / f"{j}.json").write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")),
                                                  encoding="utf-8")
        print(f"{j}.json: {sum('pb' in e for e in daten)} von {len(daten)} VNB mit Preisblatt")
    (ziel / "daten" / "jahre.json").write_text(json.dumps(jahre), encoding="utf-8")
    # shields.io-Endpoint für das README-Badge, aktuellstes Jahr
    daten = json.loads((ziel / "daten" / f"{jahre[0]}.json").read_text(encoding="utf-8"))
    n = sum("pb" in e for e in daten)
    (ziel / "daten" / "badge.json").write_text(json.dumps(
        {"schemaVersion": 1, "label": f"VNB erfasst {jahre[0]}", "message": f"{n} / {len(daten)}",
         "color": "brightgreen" if n == len(daten) else "blue"}, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "web")
