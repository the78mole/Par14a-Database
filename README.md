# Par14a-Database

[![Webseite](https://github.com/the78mole/Par14a-Database/actions/workflows/pages.yml/badge.svg)](https://the78mole.github.io/Par14a-Database/)
[![Datenbanken](https://github.com/the78mole/Par14a-Database/actions/workflows/release.yml/badge.svg)](https://github.com/the78mole/Par14a-Database/actions/workflows/release.yml)
[![CI](https://github.com/the78mole/Par14a-Database/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/the78mole/Par14a-Database/actions/workflows/ci.yml)
[![CodeQL](https://github.com/the78mole/Par14a-Database/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/the78mole/Par14a-Database/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/the78mole/Par14a-Database/badge)](https://scorecard.dev/viewer/?uri=github.com/the78mole/Par14a-Database)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/16612/badge)](https://www.bestpractices.dev/projects/16612)
[![Security Policy](https://img.shields.io/badge/Security-Policy-brightgreen?logo=github)](SECURITY.md)
[![Release](https://img.shields.io/github/v/release/the78mole/Par14a-Database?label=SQLite)](https://github.com/the78mole/Par14a-Database/releases/latest)
[![Erfasst](https://img.shields.io/endpoint?url=https://the78mole.github.io/Par14a-Database/daten/badge.json)](STATUS.md)
[![Letzte Änderung](https://img.shields.io/github/last-commit/the78mole/Par14a-Database?label=letzte%20%C3%84nderung)](https://github.com/the78mole/Par14a-Database/commits/main)
[![Online abfragen](https://img.shields.io/badge/online-abfragen-2457a6)](https://the78mole.github.io/Par14a-Database/)

Aktueller Fortschritt der Erfassung: [STATUS.md](STATUS.md)

Datenbank der §14a-EnWG-Netzentgelte (Modul 1, 2, 3) für steuerbare Verbrauchseinrichtungen aller deutschen Verteilnetzbetreiber, je Jahr als SQLite-Release.

*English: a database of the reduced grid fees under §14a EnWG (modules 1, 2 and 3) for controllable consumer devices (heat pumps, wallboxes, …) of all German distribution system operators, as one SQLite database per year. See the [English summary](#english-summary) below.*

## Download

Die fertigen Datenbanken liegen in den Releases, je Jahr ein Release `daten-<jahr>` mit `par14a_<jahr>.sqlite`. Sie werden bei jeder Änderung in `data/` automatisch neu gebaut. Jeder Stand hat eine eindeutige Version aus Commit-Datum und Commit (z. B. `2026-11-12+837ea02`); sie steht in der Tabelle `meta` der Datenbank und in den Release-Notes, zusammen mit den letzten Änderungen an den Daten.

## Webseite

Online: **https://the78mole.github.io/Par14a-Database/**

Unter `web/` liegt eine kleine statische Abfrageseite (Suche nach Netzbetreiber, PLZ oder Ort, Jahr wählbar, Modul 1/2/3 mit Zeitfenstern und Links aufs Preisblatt). Sie wird bei jeder Änderung in `data/` per GitHub Actions auf GitHub Pages veröffentlicht (Einstellung *Settings → Pages → Source: GitHub Actions*). Lokal ansehen:

```sh
python scripts/build_web.py && python -m http.server -d dist/web
```

## Preisblatt einreichen

Preisblätter für VNBs, die noch nicht in der Datenbank enthalten sind, oder neuere Fassungen bereits erfasster VNBs können über das Issue-Formular **[Neues Preisblatt einreichen](https://github.com/the78mole/Par14a-Database/issues/new?template=preisblatt.yml)** eingereicht werden. Anzugeben sind VNB, Geltungsjahr, Status, die Download-URL des PDFs und die Seite, auf der es verlinkt ist. Das PDF selbst bitte per Drag & Drop als Anhang ins Issue ziehen. Die Preise für Modul 1, 2 und 3 sind optional, sonst werden sie aus dem PDF ausgelesen.

## Mitmachen und Fehler melden

Falsche Werte, Fehler in Skripten oder auf der Webseite bitte als [Issue](https://github.com/the78mole/Par14a-Database/issues) melden. Wie Pull Requests ablaufen und welche Anforderungen gelten (Tests, Ruff), steht in [CONTRIBUTING.md](CONTRIBUTING.md). Sicherheitslücken bitte vertraulich melden, siehe [SECURITY.md](SECURITY.md).

## Aufbau

| Pfad | Inhalt |
|---|---|
| `schema.sql` | Tabellen `vnb`, `preisblatt`, `m3_zeitfenster`, `rollout_quote` |
| `data/vnb.csv` | Stammdaten aller VNBs aus [vnbdigital.de](https://www.vnbdigital.de), plus Einstiegsseite für Netzentgelte und Datum der letzten Prüfung |
| `data/<jahr>/preisblatt.csv` | Preise je VNB und Jahr, mit PDF-URL und verlinkender Seite |
| `data/<jahr>/m3_zeitfenster.csv` | Modul-3-Zeitfenster: eine Zeile je VNB, Jahr und Quartal; `ht` und `nt` als `von-bis`-Liste mit `\|` getrennt (z. B. `07:00-09:00\|17:00-19:00`), ST ist die übrige Zeit. In der SQLite-Tabelle `m3_zeitfenster` steht jedes Fenster als eigene Zeile (`stufe`, `von`, `bis`). |
| `data/rollout_quote.csv` | Smart-Meter-Roll-out-Quote (Ausstattung mit intelligenten Messsystemen) des grundzuständigen Messstellenbetreibers je VNB, aus der [BNetzA-Liste](https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/NetzzugangMesswesen/Mess-undZaehlwesen/iMSys/artikel.html), in Prozent mit Stichtag. Steht in jeder Jahres-Datenbank. |
| `scripts/rollout_quote.py`, `data/rollout_zuordnung.csv` | liest die BNetzA-xlsx ein; Zuordnung über den Namen, abweichende Schreibweisen in der Zuordnungsdatei |
| `scripts/fetch_vnb.py` | aktualisiert `data/vnb.csv` aus vnbdigital (nutzt [vnbdigital-client](https://github.com/the78mole/vnbdigital-client)) |
| `scripts/find_preisblatt.py` | sucht auf der VNB-Webseite nach Preisblatt-PDFs, zuerst auf der gespeicherten Einstiegsseite |
| `scripts/pruefe_aenderungen.py` | lädt alle erfassten Preisblatt-URLs neu und vergleicht den SHA-256 (geänderte oder verschwundene Blätter finden) |
| `scripts/build_db.py` | baut `dist/par14a_<jahr>.sqlite`, mit Version und Commit in der Tabelle `meta` |
| `scripts/pdf_sync.py`, `scripts/pdf_sync.sh` | spiegelt die PDFs aus dem S3-Bucket nach `pdfs/<jahr>/<vnb_id>/<sha256>.pdf` (gitignored), sortiert lokale PDFs mit `--import` per sha256 ein und listet Blätter, die im Bucket fehlen |
| `web/index.html`, `scripts/build_web.py` | Abfrageseite; das Skript baut sie mit `daten/<jahr>.json` nach `dist/web` |
| `tests/` | Plausibilitätsprüfung der Daten und Tests der Build-Skripte (pytest) |

Alle Preise sind netto, wie im Preisblatt. `status` ist `endgueltig`, `vorlaeufig` oder `nicht_gefunden`.

## Neues Jahr ergänzen

1. `data/<jahr>/` anlegen.
2. Für jeden VNB zuerst `netzentgelt_seite_url` prüfen, dort steht meist das neue Preisblatt. Danach `letzte_pruefung` setzen.
3. Werte in `data/<jahr>/preisblatt.csv` eintragen, `pdf_sha256` zeigt, ob sich ein PDF unter gleicher URL geändert hat.

VNB, deren Preisblätter nur hinter Bot-Schutz oder Cloudflare-Prüfung erreichbar sind: [ZUGANGSBARRIEREN.md](ZUGANGSBARRIEREN.md).
Noch nicht erfasste VNB 2026 mit Grund: [OFFEN_2026.md](OFFEN_2026.md).

## Entwicklung

Python 3.12 oder neuer. Datenbank und Webseite brauchen nur die Standardbibliothek, die übrigen Skripte nennen ihre Pakete selbst (requests, beautifulsoup4, openpyxl, boto3). Lint und Tests:

```sh
python -m pip install --require-hashes -r requirements-dev.txt   # pytest und ruff, mit Hashes gepinnt
ruff check scripts tests
python -m pytest
```

Die Tests prüfen die CSV-Dateien in `data/` (Spalten wie in `schema.sql`, bekannte VNB, Status, Datumsformate, URLs, SHA-256, HT ≥ ST ≥ NT, Zeitfenster ohne Überschneidung) und bauen SQLite und Webseite einmal komplett. Die CI führt sie für jeden Pull Request aus, dazu CodeQL und OpenSSF Scorecard.

## Lizenz

- **Daten** (`data/`, SQLite-Releases, JSON der Webseite): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de), siehe [DATA_LICENSE](DATA_LICENSE). Namensnennung: „Par14a-Database (the78mole), CC BY 4.0“.
- **Code** (`scripts/`, `web/`, Workflows): [MIT](LICENSE).

Quellen: Preisblätter der Verteilnetzbetreiber (Veröffentlichung nach EnWG, maßgeblich ist immer das Original-PDF), VNB-Stammdaten von [vnbdigital.de](https://www.vnbdigital.de), Roll-out-Quote von der [Bundesnetzagentur](https://www.bundesnetzagentur.de). Die PDFs selbst werden nicht verteilt. Alle Angaben ohne Gewähr.

## English summary

Par14a-Database collects the grid fees for controllable consumer devices under §14a of the German Energy Industry Act (EnWG) from the price sheets of all German distribution system operators: module 1 (flat reduction), module 2 (reduced energy price on a separate meter) and module 3 (time-of-use fees with HT/ST/NT windows per quarter). One SQLite database per year is published as release `daten-<year>`, and a small search page is available at https://the78mole.github.io/Par14a-Database/. Prices are net, as in the price sheets; the original PDF is always authoritative.

- Report wrong values or bugs as a [GitHub issue](https://github.com/the78mole/Par14a-Database/issues) (English is welcome), submit price sheets with the [issue form](https://github.com/the78mole/Par14a-Database/issues/new?template=preisblatt.yml).
- Contributing and test requirements: [CONTRIBUTING.md](CONTRIBUTING.md). Security reports: [SECURITY.md](SECURITY.md).
- Build and test: `python scripts/build_db.py`, `python scripts/build_web.py`, `python -m pytest`.
- Code is MIT licensed, data is CC BY 4.0.
