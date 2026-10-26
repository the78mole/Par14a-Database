"""Trägt ausgelesene Preisblatt-Werte ein (upsert in data/<jahr>/*.csv und data/vnb.csv).

Eingabe: JSON-Liste auf stdin, je Eintrag z. B.
  {"vnb_id": "27", "jahr": 2026, "url": "<teil der PDF-URL>", "status": "endgueltig",
   "gueltig_ab": "2026-01-01", "seite": "8,14,16,18",
   "std_gp": 73.00, "std_ap": 4.09, "m1": 97.90, "m2_gp": 0, "m2_ap": 1.64,
   "m3": {"ht": 8.09, "st": 4.09, "nt": 0.41,
          "fenster": {"1,2,3,4": {"HT": ["17:00-21:00"], "NT": ["10:00-15:00"]}}},
   "hinweise": "..."}
URL, Quellseite und SHA-256 kommen aus .cache/kandidaten/<vnb_id>.json; "url" darf auch eine
vollständige URL sein, die nicht im Cache steht (dann "quelle" angeben).
"""
import csv, datetime, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PB = ["vnb_id", "jahr", "gueltig_ab", "status", "preisblatt_url", "quelle_seite_url", "seite", "pdf_sha256",
      "std_grundpreis_eur_a", "std_arbeitspreis_ct_kwh", "m1_reduzierung_eur_a", "m2_grundpreis_eur_a",
      "m2_arbeitspreis_ct_kwh", "m3_ht_ct_kwh", "m3_st_ct_kwh", "m3_nt_ct_kwh", "m3_quartale_aktiv",
      "abgerufen_am", "hinweise"]
ZF = ["vnb_id", "jahr", "quartal", "ht", "nt"]


def read(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(rows)


def zf_lesen(path):
    """m3_zeitfenster.csv (eine Zeile je VNB, Jahr und Quartal; ht/nt als "von-bis|von-bis") in
    Einzelfenster {vnb_id, jahr, quartal, stufe, von, bis} auflösen, wie in der SQLite-Tabelle."""
    out = []
    for r in read(path):
        for stufe in ("HT", "NT"):
            for span in filter(None, r[stufe.lower()].split("|")):
                von, bis = span.split("-")
                out.append({"vnb_id": r["vnb_id"], "jahr": r["jahr"], "quartal": r["quartal"], "stufe": stufe,
                            "von": von, "bis": bis})
    return out


def zf_schreiben(path, fenster):
    """Einzelfenster zu einer Zeile je VNB, Jahr und Quartal zusammenfassen (ST ist die Restzeit)."""
    zeilen = {}
    for f in sorted(fenster, key=lambda r: (int(r["vnb_id"]), int(r["quartal"]), r["stufe"], r["von"])):
        z = zeilen.setdefault((f["vnb_id"], str(f["jahr"]), str(f["quartal"])), {"HT": [], "NT": []})
        z[f["stufe"]].append(f"{f['von']}-{f['bis']}")
    write(path, ZF, [{"vnb_id": v, "jahr": j, "quartal": q, "ht": "|".join(z["HT"]), "nt": "|".join(z["NT"])}
                     for (v, j, q), z in zeilen.items()])


def num(v):
    return "" if v is None else f"{v:.3f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def main():
    heute = datetime.date.today().isoformat()
    vnb_path = ROOT / "data" / "vnb.csv"
    vnbs = read(vnb_path)
    vnb_by_id = {v["vnb_id"]: v for v in vnbs}
    for e in json.load(sys.stdin):
        vid, jahr = str(e["vnb_id"]), int(e["jahr"])
        pb_path, zf_path = ROOT / "data" / str(jahr) / "preisblatt.csv", ROOT / "data" / str(jahr) / "m3_zeitfenster.csv"
        url, quelle, sha = e.get("url", ""), e.get("quelle", ""), e.get("sha", "")
        kf = ROOT / ".cache" / "kandidaten" / f"{vid}.json"
        if url and kf.exists():
            for u, p in json.loads(kf.read_text())["pdfs"].items():
                if url in u:
                    url, quelle, sha = u, quelle or p.get("quelle_seite_url") or "", p.get("pdf_sha256", "")
                    break
        m3 = e.get("m3") or {}
        fenster = m3.get("fenster", {})
        quartale = sorted({int(q) for qs, st in fenster.items() if st.get("HT") or st.get("NT") for q in qs.split(",")})
        row = {"vnb_id": vid, "jahr": jahr, "gueltig_ab": e.get("gueltig_ab", f"{jahr}-01-01"),
               "status": e.get("status", "endgueltig"), "preisblatt_url": url, "quelle_seite_url": quelle,
               "seite": e.get("seite", ""), "pdf_sha256": sha,
               "std_grundpreis_eur_a": num(e.get("std_gp")), "std_arbeitspreis_ct_kwh": num(e.get("std_ap")),
               "m1_reduzierung_eur_a": num(e.get("m1")), "m2_grundpreis_eur_a": num(e.get("m2_gp")),
               "m2_arbeitspreis_ct_kwh": num(e.get("m2_ap")), "m3_ht_ct_kwh": num(m3.get("ht")),
               "m3_st_ct_kwh": num(m3.get("st")), "m3_nt_ct_kwh": num(m3.get("nt")),
               "m3_quartale_aktiv": ",".join(map(str, quartale)), "abgerufen_am": heute,
               "hinweise": e.get("hinweise", "")}
        rows = [r for r in read(pb_path) if not (r["vnb_id"] == vid and r["jahr"] == str(jahr))] + [row]
        rows.sort(key=lambda r: int(r["vnb_id"]))
        write(pb_path, PB, rows)
        zrows = [r for r in zf_lesen(zf_path) if not (r["vnb_id"] == vid and r["jahr"] == str(jahr))]
        for qs, stufen in fenster.items():
            for q in qs.split(","):
                for stufe, spans in stufen.items():
                    for span in spans:
                        von, bis = span.split("-")
                        zrows.append({"vnb_id": vid, "jahr": jahr, "quartal": int(q), "stufe": stufe,
                                      "von": von, "bis": "24:00" if bis == "00:00" else bis})
        zf_schreiben(zf_path, zrows)
        v = vnb_by_id[vid]
        if e.get("einstieg") or (quelle and not v.get("netzentgelt_seite_url")):
            v["netzentgelt_seite_url"] = e.get("einstieg") or quelle
        v["letzte_pruefung"] = heute
        print(f"[{vid}] {v['name']} {jahr}: {row['status']} M1={row['m1_reduzierung_eur_a']} "
              f"M2={row['m2_arbeitspreis_ct_kwh']} M3={row['m3_ht_ct_kwh']}/{row['m3_st_ct_kwh']}/{row['m3_nt_ct_kwh']} "
              f"Q={row['m3_quartale_aktiv']}")
    write(vnb_path, list(vnbs[0].keys()), vnbs)


if __name__ == "__main__":
    main()
