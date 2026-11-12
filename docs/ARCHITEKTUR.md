# Aufbau und Abläufe

*An English summary follows the German text. The German version is authoritative.*

Diese Seite beschreibt, wer und was im Projekt handelt, wie die Daten vom Preisblatt bis in die
Datenbank kommen und welche Schnittstellen die veröffentlichten Ergebnisse haben.

## 1. Akteure

| Akteur | Handelt wo | Vertrauen |
|---|---|---|
| Maintainer | lokal auf eigenem Rechner (Skripte), im Repository (Pull Requests, Merge) | vertrauenswürdig |
| Beitragende | Issues (Formular „Neues Preisblatt einreichen“), Pull Requests aus Forks | nicht vertrauenswürdig, alles wird geprüft |
| Netzbetreiber-Webseiten, vnbdigital.de, BNetzA | Quellen der Preisblätter, Stammdaten und Roll-out-Quoten | nicht vertrauenswürdig (externe Eingaben) |
| GitHub Actions | CI, CodeQL, Scorecard, Bau und Veröffentlichung | vertrauenswürdig, Rechte je Job |
| Renovate | Pull Requests für Aktualisierungen | wie Beitragende, nur grüne Minor/Patch-Updates der Actions werden automatisch gemergt |
| Nutzer | laden Releases, nutzen die Webseite | — |

## 2. Abläufe

```text
Preisblatt-PDF (VNB-Webseite)
   │  find_preisblatt.py / pruefe_aenderungen.py  (Maintainer, lokal: Suche, Download, SHA-256)
   ▼
Werte auslesen und prüfen  (vorschlag.py, fenster.py, zeige.py, ausschnitt.py; Kontrolle durch den Maintainer)
   │  eintrag.py / uebernehmen.py
   ▼
data/vnb.csv, data/<jahr>/preisblatt.csv, data/<jahr>/m3_zeitfenster.csv  (Git, Pull Request)
   │  CI: Ruff, pytest (Datenprüfung), CodeQL, DCO, Abhängigkeitsprüfung
   ▼  Merge auf main
release.yml: build_db.py → par14a_<jahr>.sqlite (+ .sha256, Provenance) → Release daten-<jahr>
pages.yml:   build_web.py → dist/web (index.html + daten/<jahr>.json) → GitHub Pages
```

- **Erfassen:** Der Maintainer sucht neue oder geänderte Preisblätter, lädt die PDFs über HTTPS,
  liest die Werte halbautomatisch aus und prüft sie gegen das PDF. Die PDFs selbst werden nicht
  im Repository verteilt, sondern nur ihr SHA-256 und ihre URL; eine Kopie liegt im privaten
  Archiv des Maintainers.
- **Einreichen:** Beitragende melden Preisblätter über das Issue-Formular. Der Maintainer
  überträgt geprüfte Werte selbst; Daten aus Issues gelangen nie automatisch in `data/`.
- **Prüfen:** Jeder Pull Request durchläuft die CI (siehe [CONTRIBUTING.md](../CONTRIBUTING.md)).
- **Veröffentlichen:** Nach dem Merge bauen die Workflows Datenbanken und Webseite neu.

## 3. Externe Schnittstellen der Ergebnisse

| Ergebnis | Schnittstelle |
|---|---|
| `par14a_<jahr>.sqlite` | SQLite-Datenbank mit den Tabellen aus [schema.sql](../schema.sql): `vnb`, `preisblatt`, `m3_zeitfenster`, `rollout_quote`, `meta` (Version, Commit, Lizenz) |
| `par14a_<jahr>.sqlite.sha256` | Prüfsumme im Format von `sha256sum` |
| Webseite | statisches HTML/JavaScript ohne Server-Logik; liest `daten/jahre.json` und `daten/<jahr>.json`, keine Cookies, keine Eingaben werden gesendet |
| `daten/badge.json` | shields.io-Endpoint für das README-Badge |
| CSV-Dateien in `data/` | Format im [README](../README.md#aufbau) |

Die Skripte in `scripts/` sind Werkzeuge des Maintainers und keine veröffentlichte Schnittstelle.

---

## English summary

Actors: the maintainer (runs the scripts locally, merges pull requests), contributors (issue form,
pull requests; untrusted), external sources (DSO websites, vnbdigital.de, BNetzA; untrusted),
GitHub Actions (CI and publishing with per-job permissions) and Renovate. Price sheets are found
and downloaded over HTTPS, values are extracted semi-automatically and checked by the maintainer,
stored as CSV in Git and reviewed by CI on every pull request. After merging, `release.yml` builds
one SQLite database per year (with SHA-256 and signed provenance) and `pages.yml` builds the static
website. External interfaces: the SQLite schema in `schema.sql`, the checksum file, the static
website with its JSON files, and the CSV format documented in the README.
