"""Übernimmt geprüfte Vorschläge (.cache/vorschlag) mit Zeitfenster-Notation in die Daten.

Eine Zeile je VNB auf stdin:
  <vnb_id> q=1,4 HT=17:00-19:00 NT=00:00-06:00,22:00-24:00 [ht=7.1] [nt=1.2] [gp=90] [ap=..] [m1=..] [m2=..] [! Hinweis]
q=0 bedeutet: keine Zeitfenster gefunden. Ohne q werden alle Quartale angenommen (mit Hinweis).
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
jahr = int(sys.argv[1])
eintraege = []
for zeile in sys.stdin:
    zeile = zeile.strip()
    if not zeile or zeile.startswith("#"):
        continue
    teil, _, hinweis = zeile.partition("!")
    tok = teil.split()
    vid = tok[0]
    v = json.loads((ROOT / ".cache" / "vorschlag" / f"{vid}_{jahr}.json").read_text())
    kv = dict(t.split("=", 1) for t in tok[1:])
    for k_kurz, k in (("ht", "ht"), ("nt", "nt"), ("gp", "std_gp"), ("ap", "std_ap"), ("m1", "m1"), ("m2", "m2_ap")):
        if k_kurz in kv:
            v[k] = None if kv[k_kurz] == "-" else float(kv[k_kurz])
    hinweise = [hinweis.strip()] if hinweis.strip() else []
    q = kv.get("q")
    if q is None:
        q = "1,2,3,4"
        hinweise.append("Zeitfenster ohne Quartalsangabe, als ganzjährig erfasst")
    fenster = {}
    if q != "0" and ("HT" in kv or "NT" in kv):
        fenster[q] = {s: kv[s].split(",") for s in ("HT", "NT") if s in kv}
    m2_ok = v.get("m2_ap") is not None and abs(v["m2_ap"] - 0.4 * v["std_ap"]) <= 0.011
    if not m2_ok and "m2" not in kv:
        hinweise.append("M2 nicht als 40 % des AP bestätigt")
    eintraege.append({
        "vnb_id": vid, "jahr": jahr, "url": v["url"], "quelle": v["quelle"], "sha": v["sha"],
        "status": kv.get("status") or ("vorlaeufig" if re.search(r"vorl|voraus", v["url"], re.I)
                                       and not re.search(r"endg|final", v["url"], re.I) else "endgueltig"),
        "std_gp": v.get("std_gp"), "std_ap": v["std_ap"], "m1": v["m1"], "m2_gp": 0 if v.get("m2_ap") else None,
        "m2_ap": v.get("m2_ap"),
        "m3": {"ht": v.get("ht"), "st": v["std_ap"] if v.get("ht") else None, "nt": v.get("nt"), "fenster": fenster},
        "hinweise": "; ".join(hinweise + ["halbautomatisch ausgelesen"])})
subprocess.run([sys.executable, str(ROOT / "scripts" / "eintrag.py")], input=json.dumps(eintraege), text=True, check=True)
