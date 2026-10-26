-- §14a EnWG Preisdatenbank (steuerbare Verbrauchseinrichtungen), Niederspannung ohne Leistungsmessung.
-- Alle Preise NETTO (wie im Preisblatt). Brutto bei Bedarf mit 19 % USt berechnen.

CREATE TABLE IF NOT EXISTS vnb (
  vnb_id              TEXT PRIMARY KEY,  -- vnbdigital-ID
  name                TEXT NOT NULL,
  bdew_code           TEXT,              -- 13-stellige Marktpartner-ID (Netzbetreiber Strom)
  website             TEXT,
  plz                 TEXT,
  ort                 TEXT,
  spannungsebenen     TEXT,              -- aus vnbdigital, z. B. "Niederspannung,Mittelspannung"
  -- Für Folgeläufe: stabile Einstiegsseite, auf der das jeweils aktuelle Preisblatt verlinkt ist
  netzentgelt_seite_url TEXT,
  letzte_pruefung     DATE,              -- wann zuletzt nach neuen Preisblättern gesucht wurde
  quelle_stammdaten   TEXT               -- z. B. vnbdigital
);

CREATE TABLE IF NOT EXISTS preisblatt (
  vnb_id          TEXT NOT NULL REFERENCES vnb(vnb_id),
  jahr            INTEGER NOT NULL,      -- 2026, 2027, ...
  gueltig_ab      DATE,
  status          TEXT,                  -- endgueltig | vorlaeufig | nicht_gefunden
  preisblatt_url  TEXT,                  -- direkter Link auf das PDF
  quelle_seite_url TEXT,                 -- Seite, die auf das PDF verlinkt
  seite           TEXT,                  -- Seite(n) des §14a-Abschnitts im PDF
  pdf_sha256      TEXT,                  -- erkennt geänderte PDFs bei gleicher URL
  -- Referenz: Standard-Netzentgelt NS ohne Leistungsmessung
  std_grundpreis_eur_a     REAL,
  std_arbeitspreis_ct_kwh  REAL,
  -- Modul 1: pauschale Netzentgeltreduzierung (€/a)
  m1_reduzierung_eur_a     REAL,
  -- Modul 2: prozentuale Reduzierung des Arbeitspreises (separater Zählpunkt)
  m2_grundpreis_eur_a      REAL,
  m2_arbeitspreis_ct_kwh   REAL,
  -- Modul 3: zeitvariables Netzentgelt (nur zusammen mit Modul 1)
  m3_ht_ct_kwh             REAL,
  m3_st_ct_kwh             REAL,
  m3_nt_ct_kwh             REAL,
  m3_quartale_aktiv        TEXT,         -- z. B. "1,4"
  abgerufen_am    DATE,
  hinweise        TEXT,
  PRIMARY KEY (vnb_id, jahr)
);

-- Zeitfenster Modul 3: eine Zeile je Quartal, Stufe und Fenster (nur HT/NT; übrige Zeit = ST)
CREATE TABLE IF NOT EXISTS m3_zeitfenster (
  vnb_id   TEXT NOT NULL,
  jahr     INTEGER NOT NULL,
  quartal  INTEGER NOT NULL CHECK (quartal BETWEEN 1 AND 4),
  stufe    TEXT NOT NULL CHECK (stufe IN ('HT','ST','NT')),
  von      TEXT NOT NULL,                -- "HH:MM"
  bis      TEXT NOT NULL,                -- "HH:MM" (24:00 = Tagesende)
  FOREIGN KEY (vnb_id, jahr) REFERENCES preisblatt(vnb_id, jahr)
);
