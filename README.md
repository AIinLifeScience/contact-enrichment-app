# Contact Enrichment App

Streamlit-App zur automatischen Anreicherung von Kontaktlisten mit Web-Recherche und KI-Analyse.

## Features

- **5 Email-Strategien**: Website-Scraping, Web-Suche, Hunter.io, Presseportale, Google Scholar
- **SMTP-Verifizierung**: Prüft ob Email-Postfächer existieren
- **Deep Research Dossier**: KI erstellt vollständiges Profil über jeden Kontakt
- **Personalisierte Nachrichten**: Fertige Ansprache-Texte basierend auf recherchierten Fakten
- **Kanal-Empfehlung**: Email vs. LinkedIn mit Begründung
- **Delta-Scan**: Wöchentliches Monitoring auf neue Infos
- **Excel-Export**: Formatierte Excel-Datei mit allen Enrichment-Spalten

## Installation

```bash
pip install -r requirements.txt
```

## API Keys

Kopiere `.env.example` nach `.env` und trage deine Keys ein:

- **Anthropic API Key** (empfohlen): Für KI-Zusammenfassung und personalisierte Nachrichten
- **Hunter.io API Key** (optional): Für Email-Format-Erkennung (Free: 25 Suchen/Monat)

## Starten

```bash
streamlit run app.py
```

Oder:

```bash
./start.sh
```

## Nutzung

1. Excel-Datei mit Kontakten laden (Spalten: Name, Firma, Titel/Position)
2. API Keys in der Sidebar eingeben
3. "Alle Kontakte anreichern" klicken
4. Ergebnisse prüfen und als Excel speichern

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
| KI-Zusammenfassung | Deep Research Dossier |
| Personalisierte Nachricht | Fertige Ansprache |
| Kanal-Empfehlung | Email oder LinkedIn |

## Technologie

- Python, Streamlit, DuckDuckGo Search, BeautifulSoup
- Anthropic Claude API (Sonnet) für KI-Analyse
- Hunter.io API für Email-Recherche
- dnspython für SMTP-Verifizierung
