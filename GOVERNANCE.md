# Projektsteuerung (Governance)

*An English summary follows the German text. The German version is authoritative.*

Par14a-Database ist ein Ein-Personen-Projekt mit offenem Code und offenen Daten. Diese Datei
beschreibt, wer was entscheidet, wer Zugriff auf welche sensiblen Ressourcen hat und wie neue
Rechte vergeben werden.

## Rollen und Verantwortlichkeiten

| Rolle | Wer | Aufgaben und Rechte |
|---|---|---|
| Projektinhaber und Maintainer | Daniel Glaser ([@the78mole](https://github.com/the78mole)) | Entscheidet über Ziele, Datenmodell, Lizenz und Releases; prüft und merged Pull Requests; pflegt die Daten; verwaltet Repository-Einstellungen, Rulesets und das private PDF-Archiv; bearbeitet Sicherheitsmeldungen ([SECURITY.md](SECURITY.md)). |
| Beitragende | alle, die Issues, Preisblätter oder Pull Requests einreichen | Schlagen Änderungen vor, siehe [CONTRIBUTING.md](CONTRIBUTING.md). Kein Schreibrecht auf das Repository. |
| Automatisierte Helfer | GitHub Actions, Renovate, KI-Assistenten (Claude Code) | Bauen, prüfen und veröffentlichen; Renovate aktualisiert Abhängigkeiten. Von Assistenten erstellte Änderungen laufen wie jede andere über einen Pull Request, den der Maintainer prüft und merged. |

## Zugriff auf sensible Ressourcen

| Ressource | Zugriff |
|---|---|
| Repository `the78mole/Par14a-Database` (Admin, Schreiben, Einstellungen, Rulesets) | nur der Maintainer |
| Releases `daten-<jahr>` und GitHub Pages | nur die Workflows `release.yml` und `pages.yml` mit dem `GITHUB_TOKEN` des Laufs |
| Security Advisories (private Meldungen) | nur der Maintainer |
| Privates PDF-Archiv (S3) und dessen Zugangsdaten | nur der Maintainer, siehe [docs/SICHERHEIT.md](docs/SICHERHEIT.md#5-umgang-mit-geheimnissen) |

Das Repository hat keine Repository-Secrets; kein Workflow braucht mehr als den `GITHUB_TOKEN`.

## Vergabe erweiterter Rechte

Schreib- oder Admin-Rechte auf das Repository oder Zugang zu den Zugangsdaten des PDF-Archivs
bekommt nur, wen der Maintainer vorher geprüft hat:

1. Die Person hat über mehrere Monate nachvollziehbar gute Beiträge geleistet (Pull Requests,
   Reviews oder Datenpflege) und ist dem Maintainer persönlich oder über ihre öffentliche Arbeit
   bekannt.
2. Ihr GitHub-Konto nutzt Zwei-Faktor-Authentifizierung.
3. Rechte werden so klein wie möglich vergeben (zuerst *Triage* bzw. *Write*, kein *Admin*) und
   in dieser Datei mit Datum eingetragen.
4. Rechte werden entzogen, wenn sie ein Jahr nicht genutzt wurden oder die Person es wünscht.

## Entscheidungen

- Der Maintainer entscheidet. Vorschläge und Fragen kommen als Issue oder Pull Request.
- Jede Änderung an `main` läuft über einen Pull Request mit grüner CI (Ruleset „main schützen“,
  Vorlage in [.github/rulesets/main-schuetzen.json](.github/rulesets/main-schuetzen.json)).
- Änderungen an dieser Datei beschließt der Maintainer per Pull Request.

## Kontinuität

Code, Daten, Doku und Workflows liegen vollständig im Repository; die Releases entstehen
automatisch aus `main`. Wer das Projekt fortführen will, kann es unter den offenen Lizenzen
(MIT, CC BY 4.0) forken. Eine Vertretung mit Schreibrechten ist derzeit nicht benannt.

---

## English summary

Par14a-Database is maintained by one person, Daniel Glaser (@the78mole), who decides on goals,
data model, licensing and releases, merges pull requests, maintains the data and handles security
reports. Only the maintainer has write/admin access to the repository, the security advisories and
the private PDF archive; releases and pages are published by workflows with the run's
`GITHUB_TOKEN`, and there are no repository secrets. Escalated permissions are granted only after
review by the maintainer (track record, 2FA, least privilege, recorded here, revoked after a year
of inactivity). All changes to `main` go through pull requests with passing CI.
