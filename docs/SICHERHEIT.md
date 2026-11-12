# Sicherheit: Erwartungen, Bewertung und Prüfung

*An English summary follows the German text. The German version is authoritative.*

Diese Seite beschreibt, was Du von Par14a-Database an Sicherheit erwarten kannst, wie sich die
Release-Anhänge prüfen lassen, welche Bedrohungen betrachtet wurden und welche Regeln für
Abhängigkeiten, Analysebefunde und Geheimnisse gelten. Lücken meldest Du über
[SECURITY.md](../SECURITY.md). Akteure und Abläufe stehen in [ARCHITEKTUR.md](ARCHITEKTUR.md).

## 1. Was Du erwarten kannst und was nicht

- Jede Änderung an `main` läuft über einen Pull Request mit grüner CI (Ruff mit Bandit-Regeln,
  pytest), CodeQL, DCO-Prüfung und Abhängigkeitsprüfung.
- Jede Datenbank hat eine eindeutige Version, eine SHA-256-Prüfsumme und eine signierte
  Build-Provenance (Sigstore), siehe Abschnitt 2.
- Die Webseite ist statisch, setzt keine Cookies und sendet keine Eingaben.
- **Keine Gewähr für die Preise.** Maßgeblich ist immer das Preisblatt des Netzbetreibers.
- **Unterstützt wird nur der aktuelle Stand.** Die Anhänge der Releases `daten-<jahr>` werden bei
  jeder Datenänderung ersetzt; ältere Stände bekommen keine Korrekturen mehr, sobald ein neuer
  Stand veröffentlicht ist. Ein Jahr wird gepflegt, solange neue oder geänderte Preisblätter für
  dieses Jahr erscheinen, mindestens bis zum Ende des Geltungsjahres. Danach wird das Release
  nicht mehr aktualisiert; das wird in den Release-Notes vermerkt.

## 2. Release-Anhänge prüfen

```sh
gh release download daten-2026 -R the78mole/Par14a-Database
sha256sum -c par14a_2026.sqlite.sha256
gh attestation verify par14a_2026.sqlite -R the78mole/Par14a-Database
sqlite3 par14a_2026.sqlite "SELECT * FROM meta"
```

- `sha256sum -c` prüft die **Integrität** (Datei vollständig und unverändert).
- `gh attestation verify` (GitHub CLI ab 2.49) prüft die **Echtheit und den Urheber**: Die
  Provenance ist keyless mit Sigstore signiert; das kurzlebige Zertifikat ist an den Workflow
  `.github/workflows/release.yml` dieses Repositorys gebunden und steht im öffentlichen
  Transparenzlog Rekor. Die Ausgabe muss diesen Workflow und einen Commit auf `main` nennen.
- In `meta` stehen Version und Commit, aus dem die Datenbank gebaut wurde.

Es gibt keinen langlebigen Projektschlüssel; der Signaturschlüssel entsteht im Workflow-Lauf und
wird danach verworfen.

## 3. Sicherheitsbewertung und Bedrohungsmodell

Die veröffentlichten Ergebnisse sind Daten (SQLite, JSON) und eine statische Webseite. Die
wahrscheinlichsten und folgenreichsten Probleme sind daher nicht Speicherfehler oder Fernzugriff,
sondern falsche oder untergeschobene Daten und Angriffe über die Lieferkette.

| Bedrohung | Angriffsfläche | Gegenmaßnahme |
|---|---|---|
| Untergeschobene Werte oder Links | Issues und Pull Requests von Beitragenden | Werte aus Issues überträgt nur der Maintainer nach Prüfung gegen das PDF; Pull Requests nur mit Review und CI; Datenprüfung in `tests/test_daten.py` |
| Skript-Einschleusung auf der Webseite (XSS, CWE-79) | Texte und URLs aus `data/` | DOM-Methoden statt `innerHTML`, Links nur mit `http(s)://`, CodeQL für JavaScript |
| SQL-Einschleusung (CWE-89) | Spaltennamen aus CSV-Köpfen in `build_db.py` | Werte nur als Parameter, Spaltennamen werden als Bezeichner geprüft; Test dafür |
| Kommando-Einschleusung (CWE-78) | URLs und Dateinamen in den lokalen Skripten | `subprocess` nur mit Argumentliste, nie `shell=True` (Ruff-Regel S602) |
| Präparierte PDFs oder Webseiten | lokale Skripte des Maintainers | Verarbeitung nur lokal mit verbreiteten Werkzeugen (pdftotext, BeautifulSoup), Ergebnisse werden vor dem Eintragen geprüft |
| Manipulierte Lieferkette | Actions, Werkzeuge, Abhängigkeiten | Actions per Commit-SHA, Werkzeuge mit Hashes, Renovate, Abhängigkeitsprüfung, OpenSSF Scorecard |
| Fremder Code mit Schreibrechten | Pull Requests aus Forks | nur `pull_request` (ohne Secrets, Token nur lesend), kein `pull_request_target`; Schreibrechte nur in `release.yml`/`pages.yml` nach Merge |
| Unbefugte Änderung an `main` | Direkt-Push, Force-Push, Löschen | Ruleset „main schützen“ mit Pflicht-Checks |
| Manipulierte Release-Anhänge | Download der Datenbank | SHA-256 und Sigstore-Provenance (Abschnitt 2) |
| Abfluss von Zugangsdaten | Repository, Logs | Abschnitt 5, Secret Scanning mit Push Protection |

Nicht im Modell: Angriffe auf GitHub, Sigstore oder die Webseiten der Netzbetreiber selbst.

## 4. Regeln für Abhängigkeiten und Analysebefunde

**Auswahl und Bezug von Abhängigkeiten.** Datenbank und Webseite brauchen nur die
Python-Standardbibliothek. Neue Abhängigkeiten kommen nur hinzu, wenn sie verbreitet, gepflegt
und unter einer freien Lizenz sind. Sie werden über PyPI bzw. GitHub bezogen und so erfasst:

| Art | Datei | Pinning |
|---|---|---|
| Werkzeuge für Lint und Tests | `requirements-dev.in` → `requirements-dev.txt` (`uv pip compile --generate-hashes`) | Version und Hash |
| Hilfsskripte des Maintainers | `requirements.txt` | nicht gepinnt, laufen nur lokal |
| GitHub Actions | `.github/workflows/*.yml` | Commit-SHA |

Renovate ([renovate.json](../renovate.json)) und der Dependency Graph von GitHub verfolgen alle
Abhängigkeiten; bekannte Schwachstellen (OSV, GitHub Advisories) bekommen sofort eigene Pull
Requests.

**Schwellen für Schwachstellen und Lizenzen (SCA).** Der Workflow
[dependency-review.yml](../.github/workflows/dependency-review.yml) blockiert jeden Pull Request,
der eine Abhängigkeit mit einer bekannten Schwachstelle ab Schweregrad *moderate* oder mit einer
nicht freien Lizenz einführt. Bestehende Befunde werden behoben: *critical* und *high* innerhalb
von 14 Tagen, *moderate* innerhalb von 60 Tagen, *low* mit dem nächsten regulären Update. Vor
einer Veröffentlichung darf kein offener Befund ab *moderate* bestehen, der die veröffentlichten
Ergebnisse betrifft. Betrifft eine Schwachstelle das Projekt nachweislich nicht (z. B. ein
Werkzeug, das nur in der CI läuft und die Ergebnisse nicht berührt), wird das mit Begründung im
Dependabot- bzw. Renovate-Eintrag oder einem Advisory festgehalten.

**Schwellen für statische Analyse (SAST).** CodeQL (security-extended) und Ruff (Pyflakes,
Bugbear, Bandit) laufen bei jedem Pull Request. Der Pull Request wird blockiert bei jedem
Ruff-Befund und bei CodeQL-Befunden ab Schweregrad *medium* bzw. jedem Fehler. Bestehende Befunde:
*critical*/*high* innerhalb von 14 Tagen, *medium* innerhalb von 60 Tagen beheben. Ein Befund darf
nur als nicht ausnutzbar unterdrückt werden, mit Begründung direkt an der Stelle
(`# noqa: <Regel>  Grund`) bzw. als „Dismiss“ mit Kommentar im Code Scanning.

## 5. Umgang mit Geheimnissen

- **Keine Geheimnisse im Repository.** Das Repository hat keine Repository-Secrets; die Workflows
  nutzen nur den kurzlebigen `GITHUB_TOKEN` mit Rechten je Job. Secret Scanning mit Push
  Protection ist eingeschaltet (Settings → Code security); `.env` und `.envrc` sind in `.gitignore`.
- **Zugangsdaten des privaten PDF-Archivs** (S3) liegen ausschließlich in einem Secret-Store des
  Maintainers. Skripte bekommen sie nur als Umgebungsvariablen für die Dauer des Aufrufs
  (`scripts/pdf_sync.sh`); sie werden nie in Dateien, Logs oder Ausgaben geschrieben. Der Schlüssel
  hat nur Rechte auf diesen einen Bucket.
- **Zugriff** hat nur der Maintainer ([GOVERNANCE.md](../GOVERNANCE.md#zugriff-auf-sensible-ressourcen)).
- **Rotation:** sofort bei Verdacht auf Offenlegung, beim Verlust eines Geräts mit Zugriff und
  wenn eine Person mit Zugriff ausscheidet; sonst mindestens einmal im Jahr.

---

## English summary

**Expectations:** every change to `main` goes through a pull request with CI (Ruff incl. Bandit
rules, pytest), CodeQL, DCO and dependency review. Each database has a unique version, a SHA-256
checksum and signed build provenance. No warranty for prices; only the current state of each
`daten-<year>` release is supported, at least until the end of that year.

**Verification:** `sha256sum -c par14a_<year>.sqlite.sha256` and
`gh attestation verify par14a_<year>.sqlite -R the78mole/Par14a-Database` (keyless Sigstore,
bound to `release.yml`).

**Threat model:** injected data or links via contributions, XSS on the website, SQL and command
injection in the scripts, crafted PDFs, supply-chain attacks, untrusted fork code, unauthorised
changes to `main`, tampered release assets and leaked credentials, each with its countermeasure in
section 3.

**Policies:** dependencies are pinned (hashes, commit SHAs) and tracked by Renovate; pull requests
introducing vulnerabilities of severity moderate or higher or non-free licenses are blocked;
critical/high findings (SCA and SAST) are fixed within 14 days, medium/moderate within 60 days;
suppressions need a documented reason. Secrets are never stored in the repository, are passed to
scripts only as environment variables, are accessible only to the maintainer and are rotated on
suspicion of exposure, device loss or personnel change, and at least yearly.
