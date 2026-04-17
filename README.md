# Contact Enrichment App

Streamlit-App zur automatischen Anreicherung von Kontaktlisten mit Deep Research und KI-Analyse.
Gestaltet in der **Selina Gaertner Consulting Corporate Identity** (Deep Purple, Gold, Charcoal).

## Features

- **3-Stufen Deep Research Workflow** (Plan → Search → Analyze):
  1. Gemini Flash entwirft 8-12 gezielte Recherche-Fragen
  2. Gemini Flash + Google Grounding beantwortet jede Frage mit echten Suchergebnissen
  3. Gemini Flash analysiert alles und erstellt Dossier + personalisierte Nachricht
- **5 Email-Strategien**: Website-Scraping, Web-Suche, Hunter.io, Presseportale, Google Scholar
- **SMTP-Verifizierung**: Prüft ob Email-Postfächer existieren
- **Personalisierte Nachrichten**: Fertige Ansprache-Texte basierend auf recherchierten Fakten
- **Kanal-Empfehlung**: Email vs. LinkedIn mit Begründung
- **Delta-Scan**: Wöchentliches Monitoring auf neue Infos
- **Excel-Export**: Formatierte Excel-Datei in CI-Farben (Purple Header, Gold Enrichment-Spalten)

## LLM Provider

Zwei wählbare Provider in der Sidebar:

| Provider | Kosten/Kontakt | Dauer | Empfehlung |
|----------|---------------|-------|------------|
| **Gemini Deep Research (3-Stufen)** | ~0,03 € | ~25 Sek | **Standard** — beste Kosten-Nutzen-Rechnung |
| **Perplexity Deep Research** | ~2–4 € | 30–90 Sek | Nur bei tiefsten Dossiers nötig |

**Wichtig:** Gemini braucht **Paid Tier** aktiviert (Google AI Studio → Billing). Das kostenlose Kontingent reicht nicht für Enrichment.

## Installation

```bash
pip install -r requirements.txt
```

## API Keys

Kopiere `.env.example` nach `.env` und trage deine Keys ein:

```
GEMINI_API_KEY=...       # aistudio.google.com → API Keys (Paid Tier aktivieren!)
PERPLEXITY_API_KEY=...   # perplexity.ai → API → Keys (optional)
HUNTER_API_KEY=...       # hunter.io (optional, Free Tier: 25 Suchen/Monat)
```

## Starten

```bash
cd ~/Documents/"AI Products I build"/contact-enrichment-app
./start.sh
```

App läuft auf **http://127.0.0.1:8501** (nur lokal, nicht im Netzwerk erreichbar).

## Sicherheit & DSGVO

Die App implementiert mehrere Schutzebenen (Security by Design):

| Maßnahme | Schutz gegen |
|----------|--------------|
| **DSGVO-Zustimmungs-Gate** | Nutzung nur nach aktiver Bestätigung der Datenschutzhinweise |
| **Input-Validation** | Max. 10 MB Upload · max. 500 Kontakte · Pflichtspalten-Check |
| **Prompt-Injection-Filter** | Bösartige Instruktionen in Excel-Zellen werden vor LLM-Call gefiltert |
| **SSRF-Guard** | Blockiert interne IPs (localhost, 10.x, 169.254.x, AWS-Metadata) beim Scrapen |
| **Error-Sanitization** | API-Keys, Tokens und Home-Pfade werden aus UI-Fehlermeldungen entfernt |
| **Localhost-Binding** | Streamlit bindet an `127.0.0.1` — nicht im WLAN erreichbar |
| **Gepinnte Dependencies** | `requirements.txt` nutzt `==` für alle Pakete (Supply-Chain-Schutz) |
| **.gitignore** | Alle Excel-Dateien (PII), `.env`, Keys, Logs werden nie committed |

**Nutzer-Pflichten (DSGVO):**
- Berechtigtes Interesse (Art. 6 Abs. 1 lit. f) muss gegeben sein
- Informationspflicht (Art. 14) bei erster Ansprache erfüllen
- Widerspruchsrecht respektieren, Daten bei Widerspruch löschen
- Angereicherte Daten nur zweckgebunden verwenden (B2B-Anbahnung)

## Nutzung

1. Excel-Datei mit Kontakten laden (Spalten: Name, Firma, Titel/Position, Standort)
2. API Keys in der Sidebar prüfen (werden automatisch aus `.env` geladen)
3. Kontakte auswählen (Checkbox-Tabelle) oder alle auswählen
4. "X Kontakte anreichern" klicken
5. Ergebnisse prüfen und als Excel speichern

## Spalten im Output

| Spalte | Beschreibung |
|--------|-------------|
| E-Mail | Gefundene oder konstruierte Email |
| E-Mail Status | Verifiziert / Konstruiert / Nicht gefunden |
| E-Mail Verifizierung | SMTP-Check Ergebnis |
| Referenz-Email | Email die als Format-Vorlage diente |
| Persönliches Telefon | Direkte Telefonnummer |
| Firmentelefon | Aus Impressum |
| Konferenzen | Speaker-Auftritte, Events |
| Podcasts / Videos | Medien-Auftritte |
| Jobwechsel / Karriere | Werdegang, aktuelle Positionen |
| LinkedIn-Aktivität | Posts, Pulse-Artikel |
| KI-Zusammenfassung | Deep Research Dossier (Kategorien A-G) |
| Personalisierte Nachricht | Fertige Ansprache mit CTA |
| Kanal-Empfehlung | Email oder LinkedIn mit Begründung |
| Monitoring-Tags | Suchbegriffe für wöchentlichen Delta-Scan |
| Enrichment Datum | Wann angereichert |

## Technologie

- **Python, Streamlit** — UI
- **Google Gemini 2.5 Flash + Google Grounding** — Deep Research (3-Stufen-Workflow)
- **Perplexity sonar-deep-research** — Alternative für tiefste Recherche
- **DuckDuckGo Search, BeautifulSoup** — Web-Scraping
- **Hunter.io API** — Email-Format-Erkennung
- **dnspython, smtplib** — SMTP-Verifizierung
- **openpyxl** — Excel-Export mit CI-Formatierung

## Corporate Identity

App und Excel-Export nutzen die Selina Gaertner Consulting CI:
- **Deep Purple** `#370C7B` — Header, Überschriften
- **Gold** `#FCB02F` — Buttons, Akzente, neue Excel-Spalten
- **Charcoal** `#2D2D2D` — Fließtext
- **Arial** als Schriftart
