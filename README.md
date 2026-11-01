# Par14a-Database

[![Webseite](https://github.com/the78mole/Par14a-Database/actions/workflows/pages.yml/badge.svg)](https://the78mole.github.io/Par14a-Database/)
[![Datenbanken](https://github.com/the78mole/Par14a-Database/actions/workflows/release.yml/badge.svg)](https://github.com/the78mole/Par14a-Database/actions/workflows/release.yml)
[![Release](https://img.shields.io/github/v/release/the78mole/Par14a-Database?label=SQLite)](https://github.com/the78mole/Par14a-Database/releases/latest)
[![Erfasst](https://img.shields.io/endpoint?url=https://the78mole.github.io/Par14a-Database/daten/badge.json)](STATUS.md)
[![Letzte Änderung](https://img.shields.io/github/last-commit/the78mole/Par14a-Database?label=letzte%20%C3%84nderung)](https://github.com/the78mole/Par14a-Database/commits/main)
[![Online abfragen](https://img.shields.io/badge/online-abfragen-2457a6)](https://the78mole.github.io/Par14a-Database/)

Aktueller Fortschritt der Erfassung: [STATUS.md](STATUS.md)

Datenbank der §14a-EnWG-Netzentgelte (Modul 1, 2, 3) für steuerbare Verbrauchseinrichtungen aller deutschen Verteilnetzbetreiber, je Jahr als SQLite-Release.

## Download

Die fertigen Datenbanken liegen in den Releases, je Jahr ein Release `daten-<jahr>` mit `par14a_<jahr>.sqlite`. Sie werden bei jeder Änderung in `data/` automatisch neu gebaut.

## Webseite

Online: **https://the78mole.github.io/Par14a-Database/**

Unter `web/` liegt eine kleine statische Abfrageseite (Suche nach Netzbetreiber, PLZ oder Ort, Jahr wählbar, Modul 1/2/3 mit Zeitfenstern und Links aufs Preisblatt). Sie wird bei jeder Änderung in `data/` per GitHub Actions auf GitHub Pages veröffentlicht (Einstellung *Settings → Pages → Source: GitHub Actions*). Lokal ansehen:

```sh
python scripts/build_web.py && python -m http.server -d dist/web
```

## Preisblatt einreichen

Preisblätter für VNBs, die noch nicht in der Datenbank enthalten sind, oder neuere Fassungen bereits erfasster VNBs können über das Issue-Formular **[Neues Preisblatt einreichen](https://github.com/the78mole/Par14a-Database/issues/new?template=preisblatt.yml)** eingereicht werden. Anzugeben sind VNB, Geltungsjahr, Status, die Download-URL des PDFs und die Seite, auf der es verlinkt ist. Das PDF selbst bitte per Drag & Drop als Anhang ins Issue ziehen. Die Preise für Modul 1, 2 und 3 sind optional, sonst werden sie aus dem PDF ausgelesen.

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
| `scripts/build_db.py` | baut `dist/par14a_<jahr>.sqlite` |
| `web/index.html`, `scripts/build_web.py` | Abfrageseite; das Skript baut sie mit `daten/<jahr>.json` nach `dist/web` |

Alle Preise sind netto, wie im Preisblatt. `status` ist `endgueltig`, `vorlaeufig` oder `nicht_gefunden`.

## Neues Jahr ergänzen

1. `data/<jahr>/` anlegen.
2. Für jeden VNB zuerst `netzentgelt_seite_url` prüfen, dort steht meist das neue Preisblatt. Danach `letzte_pruefung` setzen.
3. Werte in `data/<jahr>/preisblatt.csv` eintragen, `pdf_sha256` zeigt, ob sich ein PDF unter gleicher URL geändert hat.

VNB, deren Preisblätter nur hinter Bot-Schutz oder Cloudflare-Prüfung erreichbar sind: [ZUGANGSBARRIEREN.md](ZUGANGSBARRIEREN.md).
Noch nicht erfasste VNB 2026 mit Grund: [OFFEN_2026.md](OFFEN_2026.md).

## Lizenz

- **Daten** (`data/`, SQLite-Releases, JSON der Webseite): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de), siehe [DATA_LICENSE](DATA_LICENSE). Namensnennung: „Par14a-Database (the78mole), CC BY 4.0“.
- **Code** (`scripts/`, `web/`, Workflows): [MIT](LICENSE).

Quellen: Preisblätter der Verteilnetzbetreiber (Veröffentlichung nach EnWG, maßgeblich ist immer das Original-PDF), VNB-Stammdaten von [vnbdigital.de](https://www.vnbdigital.de), Roll-out-Quote von der [Bundesnetzagentur](https://www.bundesnetzagentur.de). Die PDFs selbst werden nicht verteilt. Alle Angaben ohne Gewähr.
