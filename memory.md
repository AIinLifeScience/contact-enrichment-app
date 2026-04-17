# Memory - Contact Enrichment App

## Zweck
Streamlit-App zum automatischen Anreichern von Kontaktlisten (Excel) mit Deep Research + KI-Analyse.
Input: `kontakte.xlsx` aus `selina-ai-leadgen/` · Output: Angereicherte Excel mit E-Mails, Telefonen,
Konferenzen, Dossier und personalisierter Nachricht.

## Deep Research Workflow (3-Stufen, implementiert April 2026)
1. **`_plan_research()`** — Gemini 2.5 Flash (ohne Grounding) entwirft 8-12 gezielte Suchfragen
   mit **LinkedIn-Fokus** (min. 3 LinkedIn-Fragen pro Kontakt: Posts 2025/2026, Pulse-Artikel,
   Kommentar-Muster, Hashtags, Gruppen, "site:linkedin.com"-Queries)
2. **`_execute_research()`** — Gemini 2.5 Flash + Google Grounding beantwortet Fragen mit echten Suchen
3. **`_analyze_with_llm()`** — Gemini 2.5 Flash erstellt Dossier aus Deep Research + DuckDuckGo Ergebnissen
   + **LeadGen-Context** (siehe unten)

**Kosten pro Kontakt:** ~0,03 € (Gemini Paid Tier) · **Dauer:** ~25 Sek

## LeadGen-DB-Integration (Apr 2026 — Option C)
Die App matcht automatisch jeden Kontakt gegen `selina-ai-leadgen/data/automation.db` (204 Kontakte):
- **Read-only Zugriff** via SQLite URI `mode=ro` (keine Writes möglich)
- **Match-Strategie:** `first_name + last_name` exakt, Firma als Tiebreaker (Konfidenz: "hoch" bei Firma-Match, "mittel" sonst)
- **Helper:** `_lookup_leadgen_context()` + `_format_leadgen_context_for_llm()` in `enrichment_engine.py`
- **UI-Integration:**
  - Sidebar zeigt Anzahl DB-Kontakte (`🔗 LeadGen-DB verbunden · 204 Kontakte`)
  - Detail-View zeigt Badge "Bekannt aus Outbound" mit Status + Reply-Text + LinkedIn-URL
  - Übersichts-Banner: "X von Y Kontakten sind in deiner Lead-Gen-Historie"
- **LLM bekommt:** Outbound-Timeline (Connection Request, Connected, Opener, Scorecard, Calendly, Reply),
  Reply-Text + Klassifizierung, LinkedIn-URL (verifiziert), bisherige Sprache
- **Default-Pfad:** `~/Documents/AI Products I build/selina-ai-leadgen/data/automation.db`
- **Override:** ENV-Variable `LEADGEN_DB_PATH`

## Retry & Fallback-Logik
- `_call_gemini()` versucht erst `gemini-2.5-flash`, dann `gemini-2.0-flash`
- Bei 503 (überlastet): 5s warten, Retry
- Bei 429 (Quota): Bei Free-Tier klare Fehlermeldung mit Hinweis auf Billing-Aktivierung
- Zwei Versuche pro Modell

## Wichtige Dateien
- `app.py` — Streamlit UI (mit CI-Styling: Purple/Gold/Charcoal, Arial)
- `enrichment_engine.py` — Hauptlogik (5 Email-Strategien + 3-Stufen Deep Research)
- `.env` — API Keys (GEMINI_API_KEY muss Paid Tier sein!)

## LLM Provider Auswahl (Sidebar)
- **Gemini Deep Research (3-Stufen)** → ~0,03 €/Kontakt, ~25 Sek, Standard
- **Perplexity Deep Research** → ~2–4 €/Kontakt, 30–90 Sek, nur für tiefste Dossiers

## Status-Spalten im Output (Excel)
Siehe README.md für vollständige Liste. Wichtigste:
- E-Mail + Status + SMTP-Verifizierung + Referenz-Email
- Konferenzen, Podcasts, Jobwechsel, LinkedIn-Aktivität
- KI-Zusammenfassung (Dossier A-G) + Personalisierte Nachricht + Kanal-Empfehlung
- Monitoring-Tags (für wöchentlichen Delta-Scan)

## Behobene Bugs
- **Gemini 404 (Apr 2026):** `gemini-2.5-flash-preview-05-20` wurde von Google entfernt → Fix: auf `gemini-2.5-flash` umgestellt
- **Falsche Fehlermeldung (Apr 2026):** Except-Block sagte immer "Perplexity-Fehler" auch bei Gemini → Fix: `{self.llm_provider.capitalize()}-Fehler`
- **Schlechte Ergebnisse mit Flash (Apr 2026):** Einstufige Analyse mit generischen DuckDuckGo-Suchen fand zu wenig → Fix: 3-Stufen Deep Research Workflow (Plan → Search → Analyze)
- **JSON-Parse-Fehler in `_plan_research()`:** Gemini gibt JSON in Markdown-Codeblock zurück → Fix: Regex-basierter Fallback-Parser der `[...]` im Text findet
- **Free Tier Quota aufgebraucht:** Fehlermeldung zeigt jetzt klar "Bitte Billing in Google AI Studio aktivieren"
- **"Excel speichern"-Button tat nichts (Apr 2026):** Klassischer Streamlit-Nested-Button-Bug — Speicher-Button war innerhalb des Anreichern-Buttons verschachtelt, Rerun beim Klick setzte äußeren Button auf `False`, innerer Block wurde nie erreicht → keine Datei, keine Meldung. **Fix:** `results`/`skipped`/`errors` in `st.session_state` persistiert; Zusammenfassung + Speicher-Block aus dem äußeren if-Block herausgezogen; `try/except` mit spezifischen Fehlermeldungen (PermissionError, FileNotFoundError) beim Speichern
- **DSGVO-Expander zeigte `arrow_down` als Text (Apr 2026):** CI-CSS hatte `span { font-family: Arial !important }` — das überschrieb auch die Material-Icons-Font von Streamlit, dadurch wurde der Icon-Name als Text sichtbar. **Fix:** `span` aus globalem Override entfernt + explizite Ausnahme für `span[class*="material-icons"]`, `span[class*="material-symbols"]`, `[data-testid="stExpanderToggleIcon"]`

## Security-Hardening (Apr 2026, vor GitHub Push)
Vollständiges Security-Audit durchgeführt — 10 Findings, alle behoben:
- **DSGVO-Zustimmungs-Gate** in `app.py` (`st.stop()` bis akzeptiert) + Sidebar-Reminder
- **Input-Validation** (`_validate_and_load_excel`): max 10 MB, max 500 Kontakte, Pflichtspalten-Check
- **Error-Sanitization** (`_sanitize_error`): API-Keys (`sk-*`, `AIza*`), Tokens, `/Users/*`-Pfade werden redacted
- **Prompt-Injection-Filter** (`_sanitize_llm_input` in `enrichment_engine.py`): Patterns wie "ignore previous instructions", `<system>`, "you are now", Kontrollzeichen
- **SSRF-Guard** (`_is_safe_url`): Blockiert `localhost`, private IP-Ranges (10.x, 172.16–31.x, 192.168.x), AWS/GCP-Metadata (169.254.x), IPv6-Loopback, Nicht-HTTP-Schemas; 16/16 Tests grün
- **Localhost-Binding** in `start.sh`: `--server.address 127.0.0.1` (nicht mehr im WLAN erreichbar)
- **Dependencies gepinnt** mit `==` in `requirements.txt`
- **.gitignore erweitert**: PII-Dateien (`kontakte*`, `contacts*`, `leads*`, `enriched*`), `.env*`, Keys, Logs, venv

## Enrichment-Ergebnis-DB (Apr 2026)
SQLite-Datenbank zum automatischen Speichern aller Enrichment-Ergebnisse:
- **Datei:** `enrichment_db.py` → `data/enrichment_results.db`
- **Auto-Save:** Jedes Ergebnis wird sofort nach `enrich_contact()` gespeichert (kein Datenverlust)
- **Cache-Lookup:** Bereits recherchierte Kontakte werden direkt aus DB geladen (API-Kosten sparen)
- **UI:** Sidebar zeigt DB-Count + Export-Button; Tabelle zeigt "In DB (vor X Tagen)"; Zusammenfassung zeigt "Aus DB geladen"-Metrik
- **Export:** Alle DB-Ergebnisse als formatierte Excel (CI-Farben, Purple Header)
- **Override:** ENV `ENRICHMENT_DB_PATH`
- **.gitignore:** `data/` und `*.db` sind ausgeschlossen (PII!)
- **Tabelle:** `enrichment_results` mit 29 Spalten (alle Result-Felder + Metadata)
- **Unique Index:** `(name COLLATE NOCASE, company COLLATE NOCASE)` → kein Duplicate, Update bei Re-Run

## Sicherheits-Limits (konfigurierbar via .env)
- `MAX_UPLOAD_SIZE_MB = 10`
- `MAX_CONTACTS = 500`
- `DEFAULT_EXCEL_PATH` / `DEFAULT_OUTPUT_DIR` aus ENV statt hardcoded

## Offene To-Dos vor Push
- **API-Keys rotieren** (waren in Konversation sichtbar): Google AI Studio, Anthropic, Hunter.io

## Corporate Identity
- App-UI und Excel-Export nutzen SGC CI (Purple `#370C7B`, Gold `#FCB02F`, Charcoal `#2D2D2D`, Arial)
- Footer: "Selina Gaertner Consulting · AI Strategy & Governance for Life Sciences & MedTech"

## GitHub
- Repo: `AIinLifeScience/contact-enrichment-app`
- Remote: `https://github.com/AIinLifeScience/contact-enrichment-app.git`

## Start-Befehl
```bash
cd ~/Documents/"AI Products I build"/contact-enrichment-app
./start.sh
```
Läuft auf http://127.0.0.1:8501 (nur lokal, an 127.0.0.1 gebunden)
