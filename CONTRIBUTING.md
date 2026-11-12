# Beiträge zu Par14a-Database

Beiträge sind willkommen: neue oder korrigierte Preisblätter, Fehlermeldungen und Code.

*An English summary follows the German text. The German version is authoritative.*

## Preisblätter und Datenfehler

- **Neues oder geändertes Preisblatt:** über das Formular
  [„Neues Preisblatt einreichen“](https://github.com/the78mole/Par14a-Database/issues/new?template=preisblatt.yml).
  Wichtig sind die Download-URL des PDFs und die Seite, auf der es verlinkt ist. Maßgeblich ist
  immer das Original-PDF des Netzbetreibers.
- **Falscher Wert, Fehler im Skript oder auf der Webseite:** als
  [Issue](https://github.com/the78mole/Par14a-Database/issues/new). Bitte VNB, Jahr und Feld bzw.
  die Schritte zum Nachvollziehen angeben. Der aktuelle Stand steht in [STATUS.md](STATUS.md).
- **Sicherheitslücken** bitte nicht öffentlich, sondern wie in [SECURITY.md](SECURITY.md)
  beschrieben melden.

## Pull Requests

1. Fork anlegen, Branch erstellen, Änderung committen.
2. Vor dem Pull Request lokal prüfen:

   ```sh
   python -m pip install --require-hashes -r requirements-dev.txt
   ruff check scripts tests
   python -m pytest
   ```

   Die CI ([ci.yml](.github/workflows/ci.yml)) führt dieselben Prüfungen für jeden Pull Request aus,
   dazu CodeQL, die DCO-Prüfung und die Abhängigkeitsprüfung. Ein Pull Request wird erst gemergt,
   wenn alles grün ist. Wann welche Prüfung läuft: `ci.yml`, `codeql.yml`, `dco.yml` und
   `dependency-review.yml` bei jedem Pull Request und Push auf `main`, CodeQL und Scorecard
   zusätzlich wöchentlich.
3. Pull Request gegen `main` öffnen und kurz beschreiben, was sich ändert und wie es geprüft wurde.

### Signed-off-by (DCO)

Jeder Commit trägt eine Zeile `Signed-off-by: Name <E-Mail>`. Damit bestätigst Du das
[Developer Certificate of Origin](https://developercertificate.org/): dass Du den Beitrag selbst
geschrieben hast oder das Recht hast, ihn unter der Lizenz des Projekts einzureichen. Git fügt die
Zeile mit `git commit -s` an. Der Check *DCO (Signed-off-by)* lehnt Pull Requests ohne diese Zeile
ab. Vergessen? `git commit --amend -s` bzw. `git rebase --signoff main` und neu pushen.

### Anforderungen an Beiträge

- **Daten:** Werte netto wie im Preisblatt, mit `preisblatt_url`, `quelle_seite_url`,
  `pdf_sha256` und `abgerufen_am`. Format der Dateien siehe [README](README.md#aufbau).
  `tests/test_daten.py` prüft Form und Stimmigkeit (Status, Datumsformat, Zeitfenster ohne
  Überschneidung, HT ≥ ST ≥ NT usw.).
- **Code:** Python 3.12 oder neuer, nur Standardbibliothek für `build_db.py` und `build_web.py`.
  Ruff mit den Regeln aus [pyproject.toml](pyproject.toml) (Pyflakes, Bugbear, Bandit-Sicherheitsregeln)
  muss ohne Befund durchlaufen. Ausnahmen stehen als `# noqa: <Regel>` mit kurzem Grund an der
  Stelle. Die Webseite setzt Inhalte nur über DOM-Methoden (`textContent`, `append`), nie über
  `innerHTML`, und lässt Links nur mit `http(s)://` zu.
- **Tests:** Neue Funktionen und Fehlerkorrekturen brauchen automatisierte Tests im selben Pull
  Request, für eine Korrektur einen Regressionstest, der ohne die Korrektur fehlschlägt. Neue
  Plausibilitätsregeln für die Daten kommen nach `tests/test_daten.py`. Ausnahmen (reine Doku,
  reine Datenpflege, die von den vorhandenen Tests abgedeckt ist) werden im Pull Request begründet.
- **Abhängigkeiten:** neue nur, wenn nötig, verbreitet, gepflegt und frei lizenziert; Regeln in
  [docs/SICHERHEIT.md](docs/SICHERHEIT.md#4-regeln-für-abhängigkeiten-und-analysebefunde).
- **Sprache:** Doku, Kommentare und Commit-Texte auf Deutsch; Issues und Pull Requests auf Englisch
  sind ebenso willkommen.

### Lizenz der Beiträge

Mit einem Beitrag erklärst Du Dich einverstanden, dass er unter der Lizenz des jeweiligen Teils
steht: Code unter [MIT](LICENSE), Daten unter [CC BY 4.0](DATA_LICENSE). Du sicherst zu, dass Du
das Recht dazu hast und Inhalte Dritter mit Herkunft kenntlich machst.

---

## English summary

Contributions are welcome. Submit new or updated price sheets with the
[issue form](https://github.com/the78mole/Par14a-Database/issues/new?template=preisblatt.yml) and
report wrong values or bugs as a normal [issue](https://github.com/the78mole/Par14a-Database/issues/new)
(English is fine). Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

For pull requests, run `ruff check scripts tests` and `python -m pytest` (tools pinned with hashes
in `requirements-dev.txt`); CI runs the same checks plus CodeQL. New functionality and bug fixes
must come with automated tests in the same pull request (a regression test for every fix). Every commit needs a
`Signed-off-by` line (`git commit -s`, Developer Certificate of Origin), checked by CI. Data
follows the documented CSV format with net prices and source URLs. Code is licensed under MIT, data
under CC BY 4.0; by contributing you agree that your contribution is licensed accordingly.
