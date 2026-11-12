# Sicherheitsrichtlinie

*An English summary follows the German text. The German version is authoritative.*

## Unterstützte Versionen

Par14a-Database wird von einer Person in der Freizeit gepflegt. Korrekturen gibt es nur für den
jeweils aktuellen Stand:

| Bestandteil | Unterstützt |
|---|---|
| `main` (Skripte, Webseite, Workflows) | ja |
| aktueller Anhang der Releases `daten-<jahr>` und die Webseite unter the78mole.github.io | ja |
| ältere Stände | nein, die Releases werden bei jeder Datenänderung ersetzt |

## Eine Lücke melden

Bitte **keine öffentlichen Issues oder Pull Requests** für Sicherheitslücken.

Melde sie vertraulich über
[„Report a vulnerability“](https://github.com/the78mole/Par14a-Database/security/advisories/new)
(GitHub Private Vulnerability Reporting). Hilfreich sind:

- betroffener Bestandteil (Skript, Webseite, Workflow, Release-Anhang) und Commit,
- Beschreibung und Auswirkung der Lücke,
- Schritte zum Nachvollziehen,
- falls bekannt, ein Vorschlag zur Behebung.

## Was Du erwarten kannst

- Eine Eingangsbestätigung innerhalb von **7 Tagen**.
- Eine erste Einschätzung innerhalb von **14 Tagen**.
- Eine Korrektur so schnell, wie es ein Ein-Personen-Projekt erlaubt, Ziel sind 60 Tage nach
  Eingang. Kritische und hohe Schweregrade gehen allen anderen Arbeiten vor.
- Nach der Korrektur wird das Advisory veröffentlicht, bei Bedarf mit CVE-Kennung über GitHub.
  Du wirst darin als Melder genannt, es sei denn, Du möchtest anonym bleiben.

Es gibt kein Bug-Bounty-Programm.

## Geltungsbereich

Gemeint sind der Code in diesem Repository (`scripts/`, `web/`, `.github/workflows/`), die
Webseite und die Release-Anhänge, etwa:

- Skript- oder HTML-Einschleusung auf der Webseite über Inhalte aus `data/`,
- Workflows, die Fremden Schreibrechte oder Zugriff auf Geheimnisse verschaffen,
- manipulierte oder unvollständig gebaute Release-Anhänge.

Nicht gemeint sind

- **falsche oder veraltete Preise**. Das ist ein Datenfehler und gehört in ein normales Issue oder
  über [„Neues Preisblatt einreichen“](https://github.com/the78mole/Par14a-Database/issues/new?template=preisblatt.yml);
- bereits öffentlich bekannte Advisories zu Abhängigkeiten (ohne eigene Angaben zur Ausnutzung
  hier, gern als normales Issue);
- Inhalte und Verfügbarkeit der Webseiten der Netzbetreiber, von vnbdigital.de oder der BNetzA.

---

## English summary

Only the current state of `main`, the current `daten-<year>` release assets and the website
receive fixes. Please do not report vulnerabilities publicly; use
[GitHub private vulnerability reporting](https://github.com/the78mole/Par14a-Database/security/advisories/new).
This is a one-person project: expect an acknowledgement within 7 days, a first assessment within
14 days and a fix within 60 days where possible. The advisory (with a CVE via GitHub where needed)
is published after the fix, crediting the reporter unless they prefer to stay anonymous. There is
no bug bounty. Wrong or outdated prices are data errors, not vulnerabilities: please open a normal
issue for them.
