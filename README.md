# Par14a-Database

Aktueller Fortschritt der Erfassung: [STATUS.md](STATUS.md)

Datenbank der §14a-EnWG-Netzentgelte (Modul 1, 2, 3) für steuerbare Verbrauchseinrichtungen aller deutschen Verteilnetzbetreiber, je Jahr als SQLite-Release.

## Download

Die fertigen Datenbanken liegen in den Releases, je Jahr ein Release `daten-<jahr>` mit `par14a_<jahr>.sqlite`. Sie werden bei jeder Änderung in `data/` automatisch neu gebaut.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `schema.sql` | Tabellen `vnb`, `preisblatt`, `m3_zeitfenster` |
| `data/vnb.csv` | Stammdaten aller VNBs aus [vnbdigital.de](https://www.vnbdigital.de), plus Einstiegsseite für Netzentgelte und Datum der letzten Prüfung |
| `data/<jahr>/preisblatt.csv` | Preise je VNB und Jahr, mit PDF-URL und verlinkender Seite |
| `data/<jahr>/m3_zeitfenster.csv` | Modul-3-Zeitfenster: eine Zeile je VNB, Jahr und Quartal; `ht` und `nt` als `von-bis`-Liste mit `\|` getrennt (z. B. `07:00-09:00\|17:00-19:00`), ST ist die übrige Zeit. In der SQLite-Tabelle `m3_zeitfenster` steht jedes Fenster als eigene Zeile (`stufe`, `von`, `bis`). |
| `scripts/fetch_vnb.py` | aktualisiert `data/vnb.csv` aus vnbdigital (nutzt [vnbdigital-client](https://github.com/the78mole/vnbdigital-client)) |
| `scripts/find_preisblatt.py` | sucht auf der VNB-Webseite nach Preisblatt-PDFs, zuerst auf der gespeicherten Einstiegsseite |
| `scripts/build_db.py` | baut `dist/par14a_<jahr>.sqlite` |

Alle Preise sind netto, wie im Preisblatt. `status` ist `endgueltig`, `vorlaeufig` oder `nicht_gefunden`.

## Neues Jahr ergänzen

1. `data/<jahr>/` anlegen.
2. Für jeden VNB zuerst `netzentgelt_seite_url` prüfen, dort steht meist das neue Preisblatt. Danach `letzte_pruefung` setzen.
3. Werte in `data/<jahr>/preisblatt.csv` eintragen, `pdf_sha256` zeigt, ob sich ein PDF unter gleicher URL geändert hat.
