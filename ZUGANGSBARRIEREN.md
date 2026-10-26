# Zugangsbarrieren bei Preisblättern

Netzbetreiber müssen ihre Netzentgelte nach § 20 Abs. 1 EnWG im Internet veröffentlichen. Bei den folgenden VNB ließen sich die Preisblätter
am 26.10.2026 nicht automatisiert abrufen. Ein einfacher HTTP-Abruf (z. B. mit `curl` oder einem Screenreader-/Download-Werkzeug ohne
JavaScript) wird abgewiesen. Lesbar sind sie nur in einem vollwertigen Browser, der eine JavaScript-Prüfung besteht.

Geprüft wurde aus einem Rechenzentrum (Cloud) und von einem privaten DSL-Anschluss, jeweils ohne Umgehungsmaßnahmen.

Zuständig für die Veröffentlichungspflichten ist die Bundesnetzagentur bzw. die jeweilige Landesregulierungsbehörde.

| VNB-ID | Netzbetreiber | Art der Barriere | privater Anschluss | Preisblatt 2026 |
|---|---|---|---|---|
| 7332 | Westnetz GmbH | Bot-Schutz (HTTP 403) | 403 | [PDF](https://www.westnetz.de/content/dam/revu-global/westnetz/documents/ueber-westnetz/unser-netz/netzentgelte-strom/preisblaetter-westnetz-strom-01-01-2026.pdf) |
| 535 | Schleswig-Holstein Netz GmbH | Bot-Schutz (HTTP 403) | 403 | [PDF](https://www.sh-netz.com/content/dam/revu-global/sh-netz/Documents/Schleswig-Holstein-Netz/Netzentgelte/Strom/Allgemeine-Netzentgelte/2026_netzentgelte/finale_netzentgelte_strom_ab_20260101.pdf) |
| 1000 | E.DIS Netz GmbH | Bot-Schutz (HTTP 403) | 403 | [PDF](https://www.e-dis-netz.de/content/dam/revu-global/e-dis-netz/dokumente/Preisblaetter_Netzentgelte_Strom_20260101.pdf) |
| 7137 | Avacon Netz GmbH | Bot-Schutz (HTTP 403) | 403 | [PDF](https://www.avacon-netz.de/content/dam/revu-global/avacon-netz/documents/netzentgelte-strom/2026/Preisbl%C3%A4tter_AVANG_Strom_01.01.2026%20(1).pdf) |
| 1068 | Bayernwerk Netz GmbH | Bot-Schutz (HTTP 403) | 403 | [PDF](https://www.bayernwerk-netz.de/content/dam/revu-global/bayernwerk-netz/files/netz/netzzugang/netzentgeltestrom/bayernwerk-preisblatt-netzentgelte-2026.pdf) |
| 1064 | Syna GmbH | Bot-Schutz (HTTP 403) | 403 | [PDF](https://www.syna.de/content/dam/syna-de/dokumente/netz/netzentgelte-strom/preisblaetter-strom-2026-syna-gmbh.pdf) |
| 7510 | Energienetze Bayern GmbH | Bot-Schutz (HTTP 403) | 403 | [PDF](https://www.energienetze-bayern.com/content/dam/revu-global/energienetze-bayern/Files/Strom/Netzzugang/Netzentgelte/energienetze-bayern-preisblatt-strom-2026.pdf) |
| 7750 | Stuttgart Netze GmbH | Bot-Schutz (HTTP 403) | 403 | [PDF](https://www.stuttgart-netze.de/media//filer_public/4f/9b/4f9b9806-62be-4df9-84de-d2a044c86be2/preise_und_regelungen_2026_v10.pdf) |
| 7768 | NordNetz GmbH | Cloudflare-Challenge | 403 | [PDF](https://www.nordnetz.com/content/dam/revu-global/nordnetz/Dokumente/NordNetz/Netzinformationen/netzentgelte_strom/2026/nordnetz_finale_netzentgelte_strom_ab_20260101.pdf) |
| 485 | Oberhausener Netzgesellschaft mbH | Cloudflare-Challenge | 403 | [PDF](https://www.ob-netz.de/fileadmin/user_upload/OB-Netzgesellschaft/Strom/Mustervertraege_und_Entgelte/Preisblaetter_Strom_-_01.01.2026.pdf) |
| 221 | ELE Verteilnetz GmbH | Cloudflare-Challenge | 403 | [PDF](https://www.evng.de/content/dam/revu-global/evng/documents/strom/entgelte-strom/netznutzungsentgelte_strom_2026_evng.pdf) |
| 7793 | Stromnetz Weilheim GmbH & Co. KG | Cloudflare-Challenge | 403 | [PDF](https://assets.stromnetz-weilheim.de/media/downloads/2026/01/28/Netzentgelte_2026.pdf) |
| 7800 | Netzgesellschaft Panketal GmbH | Cloudflare-Challenge | 403 | [PDF](https://www.panketal-netz.de/content/dam/revu-global/panketal-netz/dokumente/Preisblaetter_Panketal_Netzentgelte_Strom_20260101.pdf) |
| 7601 | Energieversorgung Putzbrunn GmbH & Co. KG | Cloudflare-Challenge | 403 | [PDF](https://www.energieversorgung-putzbrunn.de/content/dam/revu-global/energieversorgung-putzbrunn/Documents/Strom/Netzentgelte/energieversorgung-putzbrunn-strom-preisblatt-2026.pdf) |
| 7113 | Gemeindewerke Markt Stockstadt am Main | Cloudflare-Challenge | 403 | noch nicht gefunden |
| 7024 | Elektrizitätswerk Frammersbach | Cloudflare-Challenge | 403 | noch nicht gefunden |
| 7778 | Stromnetz Pullach GmbH | Cloudflare-Challenge | erreichbar | [PDF](https://assets.stromnetz-pullach.de/media/downloads/2026/07/16/stromnetz-pullach-preisblatt-strom-2026.pdf) |
| 7791 | Stadtwerke Olching Stromnetz GmbH & Co. KG | Cloudflare-Challenge | erreichbar | noch nicht gefunden |
| 7087 | Stadtwerke Hammelburg GmbH | Cloudflare-Challenge | erreichbar | noch nicht gefunden |
| 7281 | Markt Zellingen | Cloudflare-Challenge | erreichbar | [PDF](https://www.markt-zellingen.de/eigene_dateien/aktuell/2023/dezember/markt_zellingen_strom_preisblatt_2026_endgueltig_20251217.pdf) |
| 602 | Stadtwerke Soest GmbH | TLS-Fehler | TLS-Fehler | noch nicht gefunden |
| 201 | Stadtwerke Freudenstadt GmbH & Co. KG | TLS-Fehler | TLS-Fehler | noch nicht gefunden |
| 635 | SWT Stadtwerke Trier Versorgungs-GmbH | TLS-/Verbindungsfehler | erreichbar | noch nicht gefunden |

Stand: 26.10.2026. Die Liste wird bei neuen Abrufen aktualisiert.
