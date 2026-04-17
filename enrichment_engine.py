"""
Enrichment Engine v4
====================
Email-Suche mit 5 Strategien:
1. Firmen-Website scrapen (Impressum, Kontakt, Team)
2. Web-Suche nach "@firmenname.com"
3. Hunter.io API (Email-Format + bekannte Emails)
4. Pressemitteilungen (presseportal.de, prnewswire.com)
5. Google Scholar / PubMed (Wissenschaftler-Emails)

Plus:
- SMTP-Verifizierung (prüft ob Email-Postfach existiert)
- Konferenz-Speakerseiten
- Transparente Referenz-Email Spalte
"""

import re
import time
import json
import socket
import smtplib
import dns.resolver
import requests
from urllib.parse import urlparse
from typing import Optional

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from bs4 import BeautifulSoup


# --- Konstanten ---

JUNK_DOMAINS = {
    "rocketreach.co", "zoominfo.com", "lusha.com", "apollo.io",
    "signalhire.com", "contactout.com", "snov.io",
    "leadiq.com", "seamless.ai", "6sense.com", "adapt.io",
    "theorg.com", "peopledatalabs.com", "dnb.com",
}

EMAIL_JUNK_DOMAINS = {
    "example.com", "sentry.io", "schema.org", "wixpress.com",
    "w3.org", "googleapis.com", "firmendata.com", "northdata.com",
    "firmenwissen.de",
}

FREE_MAIL_PROVIDERS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.de",
    "outlook.com", "hotmail.com", "hotmail.de", "web.de",
    "gmx.de", "gmx.net", "t-online.de", "icloud.com",
    "protonmail.com", "proton.me", "aol.com", "mail.com",
}

PHONE_BLACKLIST_PATTERNS = [
    r'0000-\d{4}', r'ISBN', r'ISSN', r'HRB\s*\d', r'DOI',
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# --- Selinas Profil für personalisierte Nachrichten ---
SELINA_PROFIL = """
═══════════════════════════════════════════════════
ÜBER SELINA GÄRTNER:
═══════════════════════════════════════════════════
KI-Strategieberaterin (TÜV Rheinland zertifiziert) | Kommerzielle Exzellenz & Compliance
Life Sciences & MedTech | Speakerin | Freiburg, Deutschland
LinkedIn: https://www.linkedin.com/in/selinagaertner/
1.562 Follower | 500+ Connections

BERUFLICHER HINTERGRUND:
- Selina Gaertner Consulting (seit Feb 2024): Unternehmensberaterin für KI-isierung von Life Science
- HTG Molecular Diagnostics (7+ Jahre):
  • District Manager Central Europe (2016-2021): Aufbau des DE/AT/CH Geschäfts von Grund auf
  • Medical Affairs Manager EMEA (2019-2021)
  • Director EU Medical Affairs & Marketing (2021-2023): Supervisor 3 MA, CE-IVD Produkte, KOL-Netzwerk
- Mission Bio: Senior Marketing Manager EMEA (Feb-Okt 2025)
- Novoptim: Business Development Consultant Life Sciences (2014-2016)

AUSBILDUNG & ZERTIFIZIERUNGEN:
- MSc Life Science, Universität Konstanz (2010-2013)
- BSc Molecular Life Science, Universität zu Lübeck (2007-2010)
- AI Strategy Consultant mit TÜV Rheinland-Qualifikation (März 2026, gültig bis 2029)
- KI-Mastery Workshop Business Sparring (Körting Institute, Jan 2026)
- Zertifizierte Trainerin für AI Design Sprint® (Agent Design Sprint Format)

WAS SELINA TUT:
Hilft kommerziellen Führungskräften in Biotech, MedTech und Life Science Unternehmen,
KI so in Sales & Marketing bis hin zur gesamten Firmenstruktur zu integrieren, dass:
- Prozesse effizient laufen
- Teams spürbar entlastet werden
- Die Pipeline stabil messbare Ergebnisse liefert
Pragmatisch, EU-konform (GDPR, MDR/IVDR, EU AI Act), umsetzbar — keine Theorie.

KONKRETE LEISTUNGEN & SERVICES:
- KI-gestützte Sales- & Marketing-Strukturen (AI-Agenten, LLM-Systeme, Automatisierungen)
- Commercial Enablement (Training für Sales, Marketing & Management)
- GTM-Unterstützung (Workflow-Design, Messaging, Pipeline-Effizienz)
- EU-konforme Umsetzung entlang GDPR, MDR/IVDR & EU AI Act
- AI Readiness Assessment & Scorecard
- Workshops & Agent Design Sprints für Geschäftsführung und Teams
- Marketing Consulting, Business Consulting, Healthcare Consulting
- Change Management, Corporate Training, Executive Coaching, Public Speaking

UNIQUE SELLING POINTS (was Selina unterscheidet):
- Verbindet operative Life-Science-Erfahrung (Medical Affairs, Marketing, Sales)
  mit KI-Expertise und Commercial Execution
- Keine Buzzwords, kein Overengineering — funktionierende KI-Prozesse
- Versteht regulierte Märkte von innen (7 Jahre Diagnostik/IVD)
- Shadow AI erkennen und in strukturierte Governance überführen
- Kann sowohl strategisch beraten als auch operativ umsetzen

AKTUELLE AKTIVITÄTEN & EVENTS:
- Speakerin & Workshop-Leiterin beim KI Summit für Pharma & Life Sciences
  (Berlin, EUREF-Campus, 24.-25. April 2026)
  • Talk: "Warum Technologie allein nicht reicht: Erfolgsfaktoren für KI-Adoption"
  • Workshop: "Deep Research mit KI: von Information zu entscheidungsreifen Insights"
  • Co-Organisatorin mit Henrike Melmert (Pharma Uno Akademie)
- Teilnehmerin & Sprinterin beim AI Agent Design Sprint (Axel Beckert, Thomas Brunner)
- AI Summit Germany: Live-Case-Präsentation zu EU AI Act & High-Risk Klassifikation
- Aktiv auf LinkedIn: Posts zu KI-Strategie, EU AI Act, Commercial Excellence, Shadow AI
- Pro-bono: Gorilla Nuts (Schwester's Social Impact Projekt in Rwanda — Macadamia)

SELINAS LINKEDIN-THEMEN (für Matching mit Kontakt-Posts):
- KI in regulierten Märkten (MedTech, Pharma, Diagnostik)
- EU AI Act Compliance & GDPR
- Shadow AI vs. strukturierte KI-Governance
- AI als Execution Engine (nicht nur Chat-Tool)
- Commercial Excellence: Sales-Zyklen, CRM, Pipeline-Effizienz
- Agent-basierte Automatisierung & AI Design Sprints
- Change Management bei KI-Einführung
- MDR/IVDR Regulatorik
- Women in Leadership / Social Impact

SELINAS NETZWERK & GEMEINSAME KONTAKTE (zum Matching):
- Torsten Koerting, Birgit Koerting (DIE KOERTINGS — Körting Institute)
- Henrike Melmert (Pharma Uno Akademie, KI Summit Co-Organisatorin)
- Filip Brocke, Anja Holz, Svetlana Ryzhenko, Helmut Eberz (KI-Strategie Peer Group)
- Axel Beckert, Thomas Brunner (AI Agent Design Sprint)
- Dr. Johanna Dahm (Decision Management, Keynote-Sprecherin)
- Prof. Dr. Sylvia Thun (Charité Berlin, Digitale Medizin)
- Stefan Dr. Walzer (MArS Market Access)

ZIELGRUPPE:
CEOs, Geschäftsführer, CCOs, CMOs, CTOs, Directors und Führungskräfte in Biotech, MedTech
und Life Science Unternehmen (primär KMU/SME, 10-500 MA) die KI strategisch integrieren wollen.

KOSTENLOSE EINSTIEGS-ANGEBOTE:
- AI Readiness Scorecard (5 Min Online-Check): https://ai-readiness-scorecard.onrender.com/scorecard
- 30-Min Kennenlern-Gespräch: https://calendly.com/gaertner-selina/30min-with-selina-gaertner

═══════════════════════════════════════════════════
NACHRICHTEN-REGELN:
═══════════════════════════════════════════════════
STIL:
- Kurz, persönlich, auf Augenhöhe (NICHT verkäuferisch, KEIN Pitch)
- Max 3-4 Sätze für LinkedIn, max 5-6 Sätze für Email
- Beziehe dich auf genau 1 konkreten, recherchierten Fakt über die Person
- Zeige echtes Interesse — keine Floskeln wie "ich bin beeindruckt"
- Stelle eine offene Frage die zum Dialog einlädt
- Jede Nachricht MUSS mit einem klaren CTA enden

CTA-OPTIONEN (wähle den zum Kontext passendsten):
1. Scorecard-CTA: "Ich habe einen kurzen AI Readiness Check gebaut — wäre das interessant?"
   → Wenn: Person hat sich noch nicht mit KI beschäftigt, Firma nutzt keine KI
2. Calendly-CTA: "Hätten Sie Lust, sich dazu 30 Min auszutauschen?"
   → Wenn: Person ist bereits KI-affin, konkretes gemeinsames Thema, warmes Intro
3. Frage-CTA: "Wie gehen Sie aktuell mit [konkretes Thema] um?"
   → Wenn: Person hat kürzlich etwas Relevantes gepostet/gesagt, Discovery-Modus
4. Event-CTA: "Sind Sie beim KI Summit in Berlin (24.-25. April) dabei?"
   → Wenn: Person geht auf Konferenzen, ist in der DACH-Biotech/Pharma Szene
5. Inhalt-CTA: "Ich habe dazu einen Artikel/Post geschrieben — soll ich ihn teilen?"
   → Wenn: Person postet viel auf LinkedIn, Content-orientiert

SIGNATUR:
- Deutsch: "Herzliche Grüße, Selina"
- Englisch: "Best wishes, Selina"

ANTI-PATTERNS (NIEMALS in der Nachricht):
- "Ich bin beeindruckt von..." (klingt unecht)
- "Ich würde mich freuen..." (zu passiv)
- Aufzählung von Selinas eigenen Leistungen
- Links in der ersten Nachricht (Scorecard/Calendly)
- Mehr als 1 Frage stellen
- Englisch schreiben wenn Person in DACH sitzt (und umgekehrt)
"""


def _is_safe_url(url: str) -> bool:
    """SSRF-Guard: Verhindert Requests auf interne IPs und Metadata-Services.

    Blockiert:
    - Nicht-HTTP(S)-Schemas (file://, ftp://, gopher://)
    - Interne IP-Ranges (localhost, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    - Cloud-Metadata (169.254.169.254 — AWS/GCP/Azure)
    - Link-Local (169.254.0.0/16)
    - IPv6-Loopback und Link-Local (::1, fe80::)
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname
        if not host:
            return False
        host_lower = host.lower()
        # Offensichtliche Keywords sofort blockieren
        if host_lower in ("localhost", "metadata", "metadata.google.internal"):
            return False
        # Alle DNS-A-Records auflösen und jede IP prüfen
        try:
            infos = socket.getaddrinfo(host, None)
        except socket.gaierror:
            return False
        for info in infos:
            ip = info[4][0]
            # IPv4
            if ip.startswith("127.") or ip.startswith("10."):
                return False
            if ip.startswith("169.254."):  # Link-local + Metadata
                return False
            if ip.startswith("192.168."):
                return False
            if ip.startswith("172."):
                try:
                    second = int(ip.split(".")[1])
                    if 16 <= second <= 31:
                        return False
                except (ValueError, IndexError):
                    return False
            if ip == "0.0.0.0":
                return False
            # IPv6
            if ip in ("::1", "::") or ip.lower().startswith("fe80:") or ip.lower().startswith("fc") or ip.lower().startswith("fd"):
                return False
        return True
    except Exception:
        # Fail-closed: Bei jedem Fehler Request blockieren
        return False


def _sanitize_llm_input(text: str, max_len: int = 500) -> str:
    """Entfernt Prompt-Injection-Versuche aus User-Inputs vor LLM-Prompt.
    Schützt gegen: eingeschleuste Instruktionen, Rollenwechsel, System-Override.
    """
    if not text:
        return ""
    s = str(text)
    # Prompt-Injection-Muster entfernen (Instruktionen, die Claude/Gemini umlenken könnten)
    injection_patterns = [
        r'(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)',
        r'(?i)disregard\s+(all\s+)?(previous|above)',
        r'(?i)system\s*[:\]]\s*',
        r'(?i)</?(system|instruction|prompt)>',
        r'(?i)you\s+are\s+now\s+',
        r'(?i)new\s+instructions?[:\s]',
        r'(?i)forget\s+(everything|all)',
    ]
    for pat in injection_patterns:
        s = re.sub(pat, '[FILTERED]', s)
    # Kontrollzeichen entfernen (außer normalem Whitespace)
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
    # Länge begrenzen
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s.strip()


def _lookup_leadgen_context(name: str, company: str, db_path: str) -> dict:
    """Option C: Match mit Lead-Gen-DB (selina-ai-leadgen/data/automation.db).

    Prüft read-only, ob die Person bereits in Selinas Outbound-Kontakten ist.
    Gibt bei Match zurück: Status, letzte Aktionen, Reply-Text, LinkedIn-URL.
    Bei kein Match: leeres Dict.

    Sicherheit: read-only (Mode `ro`), keine SQL-Injection möglich (Parameterized Queries).
    """
    import sqlite3
    import os

    if not db_path or not os.path.exists(db_path):
        return {}
    if not name:
        return {}

    # Namen-Parts extrahieren (für first_name + last_name Match)
    parts = [p.strip() for p in name.strip().split() if p.strip()]
    if len(parts) < 2:
        return {}
    first_name = parts[0]
    last_name = parts[-1]

    try:
        # Read-only URI-Modus — kein Write möglich
        uri = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Match-Strategie:
        # 1. Exakt: first_name + last_name + company
        # 2. Fallback: first_name + last_name (wenn Firma in DB anders heißt)
        query = """
            SELECT id, linkedin_url, first_name, last_name, company, title,
                   status, connection_sent_at, connected_at, messaged_at,
                   scorecard_sent_at, calendly_sent_at, interested_at,
                   reply_text, reply_classification, reply_received_at,
                   last_action_at, language
            FROM contacts
            WHERE LOWER(first_name) = LOWER(?)
              AND LOWER(last_name) = LOWER(?)
            ORDER BY
                CASE WHEN LOWER(company) = LOWER(?) THEN 0 ELSE 1 END,
                last_action_at DESC
            LIMIT 1
        """
        cur.execute(query, (first_name, last_name, company or ""))
        row = cur.fetchone()
        conn.close()

        if not row:
            return {}

        # Score: exakter Firma-Match = höhere Konfidenz
        firma_match = (row["company"] or "").strip().lower() == (company or "").strip().lower()
        confidence = "hoch" if firma_match else "mittel (Name stimmt, Firma weicht ab)"

        return {
            "matched": True,
            "confidence": confidence,
            "leadgen_id": row["id"],
            "linkedin_url": row["linkedin_url"] or "",
            "status": row["status"] or "",
            "title_in_db": row["title"] or "",
            "company_in_db": row["company"] or "",
            "language": row["language"] or "",
            "connection_sent_at": row["connection_sent_at"] or "",
            "connected_at": row["connected_at"] or "",
            "messaged_at": row["messaged_at"] or "",
            "scorecard_sent_at": row["scorecard_sent_at"] or "",
            "calendly_sent_at": row["calendly_sent_at"] or "",
            "interested_at": row["interested_at"] or "",
            "last_action_at": row["last_action_at"] or "",
            "reply_text": row["reply_text"] or "",
            "reply_classification": row["reply_classification"] or "",
            "reply_received_at": row["reply_received_at"] or "",
        }
    except Exception as e:
        print(f"  [LeadGen-DB] ⚠️ Zugriff fehlgeschlagen: {e}")
        return {}


def _format_leadgen_context_for_llm(ctx: dict) -> str:
    """Formatiert den LeadGen-Context als Text-Block für das LLM-Prompt."""
    if not ctx or not ctx.get("matched"):
        return ""

    lines = ["=== INTERNER KONTEXT (aus Selinas Outbound-Historie) ==="]
    lines.append(f"Match-Konfidenz: {ctx['confidence']}")
    if ctx.get("linkedin_url"):
        lines.append(f"LinkedIn-URL (verifiziert): {ctx['linkedin_url']}")
    if ctx.get("title_in_db"):
        lines.append(f"Titel in DB: {ctx['title_in_db']}")
    if ctx.get("language"):
        lines.append(f"Sprache der bisherigen Kommunikation: {ctx['language']}")
    lines.append(f"Outbound-Status: {ctx['status']}")

    timeline = []
    if ctx.get("connection_sent_at"):
        timeline.append(f"  • Connection-Request: {ctx['connection_sent_at']}")
    if ctx.get("connected_at"):
        timeline.append(f"  • Connected am: {ctx['connected_at']}")
    if ctx.get("messaged_at"):
        timeline.append(f"  • Opener-Nachricht: {ctx['messaged_at']}")
    if ctx.get("scorecard_sent_at"):
        timeline.append(f"  • Scorecard-Follow-up: {ctx['scorecard_sent_at']}")
    if ctx.get("calendly_sent_at"):
        timeline.append(f"  • Calendly-Einladung: {ctx['calendly_sent_at']}")
    if ctx.get("interested_at"):
        timeline.append(f"  • Interesse signalisiert: {ctx['interested_at']}")
    if ctx.get("reply_received_at"):
        timeline.append(f"  • Reply erhalten: {ctx['reply_received_at']}")
    if timeline:
        lines.append("Timeline:")
        lines.extend(timeline)

    if ctx.get("reply_text"):
        reply_short = ctx["reply_text"][:500]
        lines.append(f"Reply-Text: \"{reply_short}\"")
        if ctx.get("reply_classification"):
            lines.append(f"Reply-Klassifizierung: {ctx['reply_classification']}")

    lines.append("")
    lines.append("WICHTIG: Diese Person ist KEIN kalter Kontakt. Berücksichtige den bisherigen Verlauf")
    lines.append("beim Formulieren der nächsten Nachricht — keine Wiederholungen, auf Reply-Text eingehen,")
    lines.append("anknüpfen an den letzten Kontaktpunkt.")
    lines.append("=== ENDE INTERNER KONTEXT ===")
    return "\n".join(lines)


class EnrichmentEngine:
    """Engine v4: 5 Email-Strategien + SMTP-Verifizierung + LeadGen-DB-Match."""

    # Default-Pfad zur Lead-Gen-DB (konfigurierbar via ENV LEADGEN_DB_PATH)
    DEFAULT_LEADGEN_DB = str(
        __import__("pathlib").Path.home()
        / "Documents" / "AI Products I build" / "selina-ai-leadgen" / "data" / "automation.db"
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        hunter_api_key: Optional[str] = None,
        llm_provider: str = "gemini",
        leadgen_db_path: Optional[str] = None,
    ):
        import os
        self.api_key = api_key
        self.hunter_api_key = hunter_api_key
        self.llm_provider = llm_provider  # "gemini" oder "perplexity"
        self.ddgs = DDGS()
        # LeadGen-DB-Pfad: Parameter > ENV > Default
        self.leadgen_db_path = (
            leadgen_db_path
            or os.environ.get("LEADGEN_DB_PATH")
            or self.DEFAULT_LEADGEN_DB
        )

    # ==================================================================
    # LLM HELPER: Gemini & Perplexity
    # ==================================================================

    def _call_gemini(self, prompt: str, max_tokens: int = 6000, use_grounding: bool = True) -> str:
        """Gemini 2.5 Flash mit optionalem Google Search Grounding. Retry + Fallback."""
        from google import genai
        from google.genai import types

        models = ["gemini-2.5-flash", "gemini-2.0-flash"]
        client = genai.Client(api_key=self.api_key)

        config_kwargs = {"max_output_tokens": max_tokens}
        if use_grounding:
            config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]

        for model in models:
            label = f"{model}{' + Google Grounding' if use_grounding else ''}"
            for attempt in range(2):
                try:
                    if attempt == 0:
                        print(f"  [LLM] Analysiere mit {label}...")
                    else:
                        print(f"  [LLM] Retry {label}...")
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(**config_kwargs),
                    )
                    return response.text.strip()
                except Exception as e:
                    err = str(e)
                    if "429" in err or "RESOURCE_EXHAUSTED" in err:
                        if "free_tier" in err.lower():
                            print(f"  [LLM] ⚠️ Kostenloses Gemini-Kontingent aufgebraucht!")
                            print(f"  [LLM] → Bitte Billing in Google AI Studio aktivieren (aistudio.google.com)")
                        else:
                            print(f"  [LLM] {model} Rate-Limit erreicht, warte 10s...")
                            time.sleep(10)
                        continue
                    if "503" in err or "UNAVAILABLE" in err:
                        print(f"  [LLM] {model} überlastet, warte 5s...")
                        time.sleep(5)
                        continue
                    raise
            print(f"  [LLM] {model} nicht verfügbar, versuche nächstes Modell...")

        raise Exception("Alle Gemini-Modelle sind aktuell überlastet. Bitte später erneut versuchen.")

    def _plan_research(self, name: str, company: str, title: str, location: str) -> list[str]:
        """Schritt 1: Flash entwirft gezielte Recherche-Fragen für die Person."""
        # Prompt-Injection-Schutz: User-Input aus Excel sanitizen
        safe_name = _sanitize_llm_input(name, 200)
        safe_company = _sanitize_llm_input(company, 200)
        safe_title = _sanitize_llm_input(title, 200)
        safe_location = _sanitize_llm_input(location, 200)

        print(f"  [Research Plan] Entwerfe gezielte Suchfragen für {safe_name}...")

        prompt = f"""Du bist ein Research-Planer. Deine Aufgabe: Erstelle 8-12 sehr spezifische
Recherche-Fragen über diese Person, die ein Deep Research Agent mit Google-Suche beantworten soll.

PERSON:
- Name: {safe_name}
- Titel: {safe_title}
- Firma: {safe_company}
- Standort: {safe_location}

KONTEXT: Selina Gärtner ist KI-Strategieberaterin für Life Science & MedTech.
Sie will diese Person als potenziellen Kunden ansprechen.

ERSTELLE Recherche-Fragen zu diesen Kategorien (mindestens 1 Frage pro Kategorie,
bei LinkedIn und KI/Digital jeweils 2-3 Fragen):

1. Person & Karriere (aktueller Job, Werdegang, Ausbildung, Expertise)
2. Firma (Produkte, Größe, Marktposition, Funding, aktuelle News)
3. KI & Digitalisierung (nutzt die Firma KI? Gibt es eine Digital-Strategie? EU AI Act betroffen?)

4. **LinkedIn-Tiefe** (HOCHRELEVANT für Personalisierung — mindestens 3 Fragen hier!):
   - Welche LinkedIn-Posts hat {safe_name} in 2025/2026 veröffentlicht?
     Was waren die Themen? Welche Haltung zu KI/Digital?
   - Welche LinkedIn-Artikel/Pulse-Beiträge hat {safe_name} geschrieben?
   - Welche Posts kommentiert oder teilt {safe_name} typischerweise?
     (gibt Aufschluss über Interessen und Netzwerk)
   - Welche LinkedIn-Gruppen oder Communities ist {safe_name} Mitglied?
   - Hat {safe_name} "Open to Work", "Hiring" oder andere LinkedIn-Signale gesetzt?
   - Welche gemeinsamen Themen-Hashtags nutzt {safe_name} auf LinkedIn?

5. Konferenzen & Medien (Speaker-Auftritte 2025/2026, Podcasts, YouTube, Publikationen)
6. Persönliches (Interessen, Ehrenämter, sichtbare gemeinsame Kontakte mit Selina Gärtner)
7. Timing-Signale (Jobwechsel, neues Funding, Stellenanzeigen für Digital/KI-Rollen,
   Unternehmens-Restrukturierung, Pressemitteilungen der letzten 3 Monate)

REGELN:
- Jede Frage muss den NAMEN oder die FIRMA der Person enthalten
- Fragen müssen so spezifisch sein, dass Google gute Ergebnisse liefert
- Bei LinkedIn-Fragen: explizit "site:linkedin.com" oder "LinkedIn post" erwähnen,
  damit Google gezielt LinkedIn-Inhalte findet
- Formuliere als Suchfrage, nicht als abstrakte Frage
- Antworte NUR mit einer JSON-Liste von Strings, keine Erklärungen

Beispiel-Output:
[
  "Was ist der Karriereweg von Max Mustermann bei BioTech AG?",
  "Welche LinkedIn-Posts hat Max Mustermann in 2025 veröffentlicht? site:linkedin.com",
  "Welche Haltung hat Max Mustermann zu KI in der Diagnostik auf LinkedIn geäußert?",
  "Nutzt BioTech AG künstliche Intelligenz oder KI-Tools?",
  ...
]"""

        text = self._call_gemini(prompt, max_tokens=2000, use_grounding=False)
        # JSON-Array extrahieren
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                stripped = part.strip()
                if stripped.startswith("json"):
                    stripped = stripped[4:].strip()
                if stripped.startswith("["):
                    text = stripped
                    break

        try:
            questions = json.loads(text)
            if isinstance(questions, list) and len(questions) > 0:
                print(f"  [Research Plan] ✅ {len(questions)} Recherche-Fragen erstellt")
                return questions
        except json.JSONDecodeError:
            pass

        # Zweiter Versuch: JSON-Array irgendwo im Text finden
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                questions = json.loads(match.group())
                if isinstance(questions, list) and len(questions) > 0:
                    print(f"  [Research Plan] ✅ {len(questions)} Recherche-Fragen erstellt (aus Text extrahiert)")
                    return questions
            except json.JSONDecodeError:
                pass

        print(f"  [Research Plan] ⚠️ JSON-Fehler, verwende Fallback-Fragen")
        # Fallback: Basis-Fragen
        return [
                f"Wer ist {name} und was ist sein/ihr Karriereweg?",
                f"Was macht die Firma {company}? Produkte, Größe, Marktposition?",
                f"Nutzt {company} künstliche Intelligenz oder KI?",
                f"{name} Konferenzen Speaker 2025 2026",
                f"{company} News Partnerschaften Funding 2025 2026",
                # LinkedIn-Tiefe (3 Fragen)
                f"{name} LinkedIn Posts 2025 2026 site:linkedin.com",
                f"{name} LinkedIn Artikel Pulse Meinung KI Digitalisierung",
                f"{name} LinkedIn Kommentar Aktivität Hashtags",
                f"{company} Stellenanzeigen Digital KI AI",
                f"{company} EU AI Act MDR IVDR Compliance",
            ]

    def _execute_research(self, questions: list[str], name: str, company: str) -> str:
        """Schritt 2: Flash + Google Grounding beantwortet jede Frage mit echten Suchergebnissen."""
        print(f"  [Deep Research] Starte Recherche mit {len(questions)} Fragen...")

        combined_prompt = f"""Du bist ein Deep Research Agent. Beantworte JEDE der folgenden Fragen
über {name} ({company}) so detailliert wie möglich. Nutze deine Google-Suche aktiv für jede Frage.

WICHTIG:
- Suche AKTIV nach Informationen — nicht aus dem Gedächtnis antworten
- Nenne immer die Quelle/URL wo du die Info gefunden hast
- Wenn du nichts findest, schreibe "Keine Ergebnisse gefunden"
- Antworte auf Deutsch

RECHERCHE-FRAGEN:
"""
        for i, q in enumerate(questions, 1):
            combined_prompt += f"\n{i}. {q}"

        combined_prompt += """

FORMAT: Beantworte jede Frage mit einer nummerierten Antwort. Sei ausführlich und nenne Quellen."""

        result = self._call_gemini(combined_prompt, max_tokens=8000, use_grounding=True)
        print(f"  [Deep Research] ✅ Recherche abgeschlossen ({len(result)} Zeichen)")
        return result

    def _call_perplexity(self, prompt: str, max_tokens: int = 6000) -> str:
        """Perplexity sonar-deep-research – 30+ Suchläufe, tiefste Recherche."""
        from openai import OpenAI

        print(f"  [LLM] Analysiere mit Perplexity sonar-deep-research (dauert 30-90 Sek.)...")
        client = OpenAI(api_key=self.api_key, base_url="https://api.perplexity.ai")
        msg = client.chat.completions.create(
            model="sonar-deep-research",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.choices[0].message.content.strip()

    # ==================================================================
    # WEB-SUCHE
    # ==================================================================

    def _search(self, query: str, max_results: int = 8) -> list[dict]:
        """DuckDuckGo-Suche mit Rate-Limiting und Retry."""
        query = query.replace(" OR ", " ")
        for attempt in range(3):
            try:
                raw = list(self.ddgs.text(query, max_results=max_results))
                time.sleep(3 + attempt * 2)
                return [r for r in raw
                        if not any(j in urlparse(r.get("href", "")).netloc for j in JUNK_DOMAINS)]
            except Exception as e:
                wait = 5 + attempt * 5
                print(f"    Suchfehler (Versuch {attempt+1}/3): {e}. Warte {wait}s...")
                time.sleep(wait)
        return []

    # ==================================================================
    # WEBSITE-SCRAPING
    # ==================================================================

    def _fetch_page_text(self, url: str, timeout: int = 10) -> str:
        """Holt Textinhalt einer Webseite. SSRF-geschützt: nur öffentliche URLs."""
        # SSRF-Guard: keine internen IPs, keine Metadata-Services, nur http(s)
        if not _is_safe_url(url):
            return ""
        try:
            # allow_redirects=False + manuelles Re-Check, damit Redirects nicht
            # an interne IPs umgeleitet werden können
            resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=False)
            # Folge Redirects nur wenn Ziel auch safe ist
            redirects = 0
            while resp.is_redirect and redirects < 3:
                next_url = resp.headers.get("Location", "")
                if not next_url or not _is_safe_url(next_url):
                    return ""
                resp = requests.get(next_url, headers=HEADERS, timeout=timeout, allow_redirects=False)
                redirects += 1
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            return soup.get_text(separator=" ", strip=True)
        except Exception:
            return ""

    def _find_company_website(self, company: str, search_results: list[dict]) -> str:
        """Findet die offizielle Firmen-Domain aus Suchergebnissen."""
        firma_kw = self._company_keywords(company)
        skip = {"linkedin.com", "facebook.com", "twitter.com", "x.com",
                "wikipedia.org", "bloomberg.com", "crunchbase.com",
                "northdata.com", "northdata.de"}
        for r in search_results:
            domain = urlparse(r.get("href", "")).netloc.replace("www.", "")
            if domain and not any(s in domain for s in skip | JUNK_DOMAINS):
                if any(kw in domain for kw in firma_kw):
                    return domain
        return ""

    def _scrape_company_emails(self, company_domain: str) -> list[dict]:
        """Scrapet Firmen-Website nach Emails."""
        pages = [
            "", "/impressum", "/kontakt", "/contact", "/imprint",
            "/about", "/about-us", "/team", "/ueber-uns",
            "/press", "/presse", "/news", "/en/imprint", "/en/contact",
        ]
        found = []
        seen = set()

        for page in pages:
            url = f"https://{company_domain}{page}"
            text = self._fetch_page_text(url)
            if not text:
                text = self._fetch_page_text(f"https://www.{company_domain}{page}")
                if text:
                    url = f"https://www.{company_domain}{page}"

            if text:
                for email in re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,8}', text):
                    e = email.lower()
                    if e.split("@")[1] not in EMAIL_JUNK_DOMAINS and e not in seen:
                        seen.add(e)
                        found.append({"email": e, "source_url": url, "page": page or "/",
                                      "methode": "Website-Scraping"})
            time.sleep(1)

            personal = [e for e in found if e["email"].split("@")[0]
                        not in ("info", "contact", "office", "hello", "press", "media", "mail")]
            if len(personal) >= 2 or len(found) >= 5:
                break

        return found

    # ==================================================================
    # STRATEGIE 3: HUNTER.IO API
    # ==================================================================

    def _hunter_search(self, company_domain: str, person_name: str) -> dict:
        """
        Hunter.io Domain-Suche: Gibt Email-Format + bekannte Emails zurück.
        Free: 25 Suchen/Monat. Braucht API Key.
        Returns: {"pattern": "vorname.nachname", "emails": [...], "domain": ...}
        """
        if not self.hunter_api_key:
            return {}

        try:
            url = (
                f"https://api.hunter.io/v2/domain-search"
                f"?domain={company_domain}&api_key={self.hunter_api_key}"
            )
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", {})

            pattern = data.get("pattern", "")  # z.B. "{first}.{last}"
            emails_raw = data.get("emails", [])

            emails = []
            for e in emails_raw:
                addr = e.get("value", "")
                first_name = e.get("first_name", "")
                last_name = e.get("last_name", "")
                confidence = e.get("confidence", 0)
                emails.append({
                    "email": addr,
                    "name": f"{first_name} {last_name}".strip(),
                    "confidence": confidence,
                    "source_url": f"https://hunter.io/verify/{addr}",
                    "methode": "Hunter.io",
                })

            # Prüfen ob die gesuchte Person dabei ist
            parts = self._clean_name_parts(person_name)
            last = parts[-1] if len(parts) > 1 else ""
            person_email = None
            for e in emails:
                if last in e["email"].split("@")[0]:
                    person_email = e
                    break

            return {
                "pattern": pattern,
                "emails": emails,
                "person_email": person_email,
                "domain": company_domain,
            }

        except Exception as e:
            print(f"    Hunter.io Fehler: {e}")
            return {}

    def _hunter_pattern_to_format(self, pattern: str) -> str:
        """Konvertiert Hunter.io Pattern zu unserem Format."""
        mapping = {
            "{first}.{last}": "vorname.nachname",
            "{f}.{last}": "v.nachname",
            "{first}{last}": "vornamenachname",
            "{f}{last}": "vnachname",
            "{first}": "vorname",
            "{last}": "nachname",
            "{first}_{last}": "vorname_nachname",
            "{first}-{last}": "vorname-nachname",
        }
        return mapping.get(pattern, pattern)

    # ==================================================================
    # STRATEGIE 4: PRESSEMITTEILUNGEN
    # ==================================================================

    def _search_press_releases(self, company: str, company_domain: str, person_name: str) -> list[dict]:
        """
        Durchsucht Presseportale nach Emails.
        Presseportale haben fast immer echte Kontakt-Emails.
        """
        found = []
        queries = [
            f'site:presseportal.de "{company}"',
            f'site:prnewswire.com "{company}"',
            f'site:businesswire.com "{company}"',
        ]

        firma_kw = self._company_keywords(company)

        for q in queries:
            results = self._search(q, max_results=5)
            for r in results:
                url = r.get("href", "")
                body = f"{r.get('title', '')} {r.get('body', '')}"

                # Emails aus Snippet extrahieren
                emails = self._extract_emails_from_text(body)

                # Auch die Seite direkt scrapen (Snippets kürzen oft die Email ab)
                page_text = self._fetch_page_text(url)
                if page_text:
                    emails.extend(self._extract_emails_from_text(page_text))

                for em in set(emails):
                    em_domain = em.split("@")[1]
                    # Muss zur Firma passen
                    if (company_domain and company_domain in em_domain) or \
                       any(kw in em_domain for kw in firma_kw):
                        found.append({
                            "email": em,
                            "source_url": url,
                            "page": "Pressemitteilung",
                            "methode": "Presseportal",
                        })

                time.sleep(1)

            if found:
                break  # Erste erfolgreiche Quelle reicht

        return found

    # ==================================================================
    # STRATEGIE 5: GOOGLE SCHOLAR / PUBMED
    # ==================================================================

    def _search_scholar(self, person_name: str, company: str) -> list[dict]:
        """
        Sucht auf Google Scholar und PubMed nach Publikationen.
        Wissenschaftler listen ihre Email in Papers.
        """
        found = []
        clean_name = person_name.replace(",", "").strip()

        queries = [
            f'site:scholar.google.com "{clean_name}" email',
            f'site:pubmed.ncbi.nlm.nih.gov "{clean_name}" {company}',
            f'"{clean_name}" author email correspondence {company}',
        ]

        for q in queries:
            results = self._search(q, max_results=5)
            for r in results:
                url = r.get("href", "")
                body = f"{r.get('title', '')} {r.get('body', '')}"

                emails = self._extract_emails_from_text(body)
                parts = self._clean_name_parts(person_name)
                last = parts[-1] if len(parts) > 1 else ""

                for em in emails:
                    local = em.split("@")[0]
                    domain = em.split("@")[1]
                    # Email muss zum Nachnamen passen oder zur Firma
                    if last in local or last in domain:
                        found.append({
                            "email": em,
                            "source_url": url,
                            "page": "Publikation",
                            "methode": "Google Scholar / PubMed",
                        })

            if found:
                break

        return found

    # ==================================================================
    # SMTP EMAIL-VERIFIZIERUNG
    # ==================================================================

    def _verify_email_smtp(self, email: str) -> str:
        """
        Prüft per SMTP ob ein Email-Postfach existiert.
        Sendet KEINE echte Email — nur RCPT TO Prüfung.

        Returns:
            "existiert" - Server bestätigt das Postfach
            "abgelehnt" - Server sagt Postfach gibt es nicht
            "catch-all" - Server akzeptiert alles (nicht prüfbar)
            "fehler" - Konnte nicht prüfen (Firewall, Timeout etc.)
        """
        domain = email.split("@")[1]

        try:
            # MX-Record finden
            mx_records = dns.resolver.resolve(domain, "MX")
            mx_host = str(sorted(mx_records, key=lambda x: x.preference)[0].exchange).rstrip(".")
        except Exception:
            return "fehler (kein MX-Record)"

        try:
            # SMTP-Verbindung
            smtp = smtplib.SMTP(timeout=10)
            smtp.connect(mx_host, 25)
            smtp.helo("verify.local")
            smtp.mail("verify@verify.local")

            # Die eigentliche Prüfung
            code, msg = smtp.rcpt(email)
            smtp.quit()

            if code == 250:
                # Noch prüfen ob es ein Catch-All ist
                # Test mit garantiert falscher Adresse
                try:
                    smtp2 = smtplib.SMTP(timeout=10)
                    smtp2.connect(mx_host, 25)
                    smtp2.helo("verify.local")
                    smtp2.mail("verify@verify.local")
                    code2, _ = smtp2.rcpt(f"definitelynotreal1234567@{domain}")
                    smtp2.quit()
                    if code2 == 250:
                        return "catch-all (Server akzeptiert alles)"
                except Exception:
                    pass
                return "existiert"
            elif code == 550:
                return "abgelehnt (Postfach existiert nicht)"
            else:
                return f"unklar (Code: {code})"

        except smtplib.SMTPServerDisconnected:
            return "fehler (Server trennt Verbindung)"
        except socket.timeout:
            return "fehler (Timeout)"
        except Exception as e:
            return f"fehler ({str(e)[:50]})"

    # ==================================================================
    # KONFERENZ-SPEAKERSEITEN
    # ==================================================================

    def _search_conference_speakers(self, person_name: str, company: str) -> list[dict]:
        """Durchsucht bekannte Biotech/MedTech Konferenz-Seiten nach Emails."""
        found = []
        clean_name = person_name.replace(",", "").strip()

        # Bekannte Biotech/MedTech Konferenzseiten
        conf_sites = [
            "informaconnect.com",   # LSX, BioTechX
            "bio.org",              # BIO International
            "cphi.com",
            "medica.de",
            "bioeurope.com",
        ]
        site_query = " ".join(f"site:{s}" for s in conf_sites[:3])
        q = f'"{clean_name}" {site_query}'
        results = self._search(q, max_results=5)

        firma_kw = self._company_keywords(company)

        for r in results:
            url = r.get("href", "")
            page_text = self._fetch_page_text(url)
            if page_text:
                emails = self._extract_emails_from_text(page_text)
                parts = self._clean_name_parts(person_name)
                last = parts[-1] if len(parts) > 1 else ""

                for em in emails:
                    local = em.split("@")[0]
                    em_domain = em.split("@")[1]
                    if last in local or any(kw in em_domain for kw in firma_kw):
                        found.append({
                            "email": em,
                            "source_url": url,
                            "page": "Konferenz-Sprecher",
                            "methode": "Konferenz-Speakerseite",
                        })
            time.sleep(1)

        return found

    # ==================================================================
    # EMAIL-HILFSFUNKTIONEN
    # ==================================================================

    def _extract_emails_from_text(self, text: str) -> list[str]:
        """Extrahiert alle sauberen Email-Adressen aus Text."""
        # TLD max 8 Zeichen (deckt .com .de .org .bio .health etc. ab,
        # verhindert aber angehängte Wörter wie "comemail")
        raw = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,8}', text)
        clean = []
        for e in raw:
            e = e.lower()
            d = e.split("@")[1]
            local = e.split("@")[0]

            # TLD-Validierung: letzte Domainteil darf max 6 Zeichen sein
            tld = d.split(".")[-1]
            if len(tld) > 6:
                # Versuche den TLD zu kürzen (z.B. "comemail" → "com")
                for known_tld in ["com", "de", "org", "net", "io", "bio", "eu",
                                  "ch", "at", "uk", "us", "info", "biz", "co"]:
                    if tld.startswith(known_tld) and len(tld) > len(known_tld):
                        e = e[:-(len(tld) - len(known_tld))]
                        d = e.split("@")[1]
                        tld = d.split(".")[-1]
                        break
                else:
                    continue  # Ungültige TLD, skip

            if d not in EMAIL_JUNK_DOMAINS and \
               not d.endswith((".png", ".jpg", ".gif")) and \
               "expand_less" not in local and "expand_more" not in local and \
               d not in FREE_MAIL_PROVIDERS:
                clean.append(e)
        return list(set(clean))

    def _classify_email(self, email: str, person_name: str, company: str) -> str:
        """Klassifiziert eine Email nach Typ."""
        parts = self._clean_name_parts(person_name)
        first = parts[0] if parts else ""
        last = parts[-1] if len(parts) > 1 else ""
        domain = email.split("@")[1]
        local = email.split("@")[0]

        firma_kw = self._company_keywords(company)
        is_company_domain = any(kw in domain for kw in firma_kw) if firma_kw else False

        if domain in FREE_MAIL_PROVIDERS:
            return "freemail" if (last in local and first in local) else "irrelevant"

        if is_company_domain:
            if last in local or (first in local and len(local) > 2):
                return "person_exact"
            if local in ("info", "contact", "office", "hello", "press", "media", "mail"):
                return "firma_allgemein"
            if "." in local or len(local) > 3:
                return "firma_mitarbeiter"

        if last in local:
            return "person_partial"
        return "irrelevant"

    def _detect_email_format(self, emails: list[str]) -> Optional[str]:
        """Erkennt Email-Format aus Mitarbeiter-Emails."""
        personal = [e for e in emails if e.split("@")[0]
                     not in ("info", "contact", "office", "hello", "press", "media", "mail")]
        if not personal:
            return None

        locals_ = [e.split("@")[0] for e in personal]
        dots = sum(1 for l in locals_ if "." in l)
        if dots > 0:
            sample = [l for l in locals_ if "." in l][0]
            return "v.nachname" if len(sample.split(".")[0]) == 1 else "vorname.nachname"

        if sum(len(l) for l in locals_) / len(locals_) > 8:
            return "vnachname"
        return None

    def _construct_email(self, person_name: str, domain: str, fmt: str) -> str:
        """Konstruiert Email basierend auf Format."""
        parts = self._clean_name_parts(person_name)
        if len(parts) < 2:
            return ""
        first, last = parts[0], parts[-1]
        formats = {
            "vorname.nachname": f"{first}.{last}@{domain}",
            "v.nachname": f"{first[0]}.{last}@{domain}",
            "vnachname": f"{first[0]}{last}@{domain}",
            "vorname": f"{first}@{domain}",
            "vorname_nachname": f"{first}_{last}@{domain}",
            "vorname-nachname": f"{first}-{last}@{domain}",
            "vornamenachname": f"{first}{last}@{domain}",
            "nachname": f"{last}@{domain}",
        }
        return formats.get(fmt, f"{first}.{last}@{domain}")

    # ==================================================================
    # TELEFON + NAME + PERSONEN-CHECK
    # ==================================================================

    def _extract_phones_strict(self, text: str) -> list[str]:
        for bp in PHONE_BLACKLIST_PATTERNS:
            text = re.sub(bp + r'[\s:]*[\d\-]+', '', text)
        patterns = [
            r'\+49\s*\(?\d[\d\s\-\(\)/]{7,16}',
            r'\+1\s*\(?\d[\d\s\-\(\)]{8,13}',
            r'\+\d{1,3}\s*\(?\d[\d\s\-\(\)/]{7,16}',
        ]
        phones = []
        for pat in patterns:
            for p in re.findall(pat, text):
                cleaned = re.sub(r'[\s]+', ' ', p.strip())
                if 10 <= len(re.sub(r'[^\d]', '', cleaned)) <= 15:
                    phones.append(cleaned)
        return list(set(phones))

    def _clean_name_parts(self, name: str) -> list[str]:
        skip = {"dr", "dr.", "prof", "prof.", "phd", "ph.d.", "ph.d",
                "mba", "msc", "m.sc.", "md", "jr", "sr", "dipl", "ing"}
        parts = name.lower().replace(",", " ").split()
        clean = [p for p in parts if p not in skip and len(p) > 1]
        return [p.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
                for p in clean]

    def _company_keywords(self, company: str) -> list[str]:
        if not company:
            return []
        skip = {"gmbh", "ag", "inc", "ltd", "co", "kg", "se", "corp",
                "ohg", "ug", "llc", "bv", "ehem.", "ehem", "/", "|", "&"}
        parts = company.lower().replace(",", " ").replace("(", " ").replace(")", " ").split()
        return [p for p in parts if p not in skip and len(p) > 1]

    def _is_about_person(self, text: str, person_name: str, company: str = "") -> bool:
        parts = self._clean_name_parts(person_name)
        if not parts:
            return False
        last, first = parts[-1], parts[0]

        orig = person_name.lower().replace(",", " ").split()
        orig = [p for p in orig if len(p) > 2 and p not in {"dr.", "dr", "prof.", "prof", "phd", "ph.d.", "mba"}]
        orig_last = orig[-1] if orig else ""
        orig_first = orig[0] if orig else ""

        t = text.lower()
        if not ((last in t) or (orig_last in t)):
            return False
        if not ((first in t) or (orig_first in t)):
            return False

        if company:
            if any(kw in t for kw in self._company_keywords(company)):
                return True

        variants = [f"{orig_first} {orig_last}", f"{first} {last}",
                    person_name.lower().split(",")[0].strip()]
        return any(v in t for v in variants if len(v) > 5)

    # ==================================================================
    # HAUPTFUNKTION
    # ==================================================================

    def enrich_contact(
        self,
        name: str,
        company: str = "",
        title: str = "",
        location: str = "",
        max_searches: int = 6,
    ) -> dict:

        findings = {
            "email": "",
            "email_status": "Nicht gefunden",
            "email_verifizierung": "",
            "referenz_email": "",
            "referenz_email_quelle": "",
            "personal_phone": "",
            "company_phone": "",
            "conferences": "",
            "podcasts_videos": "",
            "job_changes": "",
            "linkedin_activity": "",
            "birthday": "",
            "relevant_info": "",
            "zusammenfassung": "",
            "personalisierte_nachricht": "",
            "kanal_empfehlung": "",
            "monitoring_tags": "",
            "raw_findings": "",
            "sources": [],
        }

        all_texts = []
        all_phones = []
        company_phones = []
        relevant_sources = []
        conference_facts = []
        podcast_facts = []
        career_facts = []
        linkedin_facts = []
        other_facts = []

        # NaN/None Werte bereinigen
        if not company or str(company).lower() in ("nan", "none", ""):
            company = ""
        if not title or str(title).lower() in ("nan", "none", ""):
            title = ""
        if not location or str(location).lower() in ("nan", "none", ""):
            location = ""

        clean_name = name.replace(",", "").strip()
        firma_kw = self._company_keywords(company)

        # ==============================================================
        # LEADGEN-DB MATCH (Option C): prüfen ob Person schon in Selinas
        # Outbound-Historie ist → Status + Timeline + Reply-Text holen
        # ==============================================================
        leadgen_ctx = _lookup_leadgen_context(clean_name, company, self.leadgen_db_path)
        if leadgen_ctx.get("matched"):
            print(f"  [LeadGen-Match] ✅ '{clean_name}' gefunden — "
                  f"Status: {leadgen_ctx['status']} · Konfidenz: {leadgen_ctx['confidence']}")
            findings["leadgen_match"] = leadgen_ctx
            # LinkedIn-URL aus DB direkt übernehmen (verifiziert)
            if leadgen_ctx.get("linkedin_url"):
                findings["linkedin_activity"] = (
                    f"Profil: {leadgen_ctx['linkedin_url']}\n"
                    f"Outbound-Status: {leadgen_ctx['status']}"
                )
            # Reply-Text als "relevant_info" vormerken (LLM bekommt es gleich)
            if leadgen_ctx.get("reply_text"):
                findings["relevant_info"] = (
                    f"Reply aus bisheriger Kommunikation ({leadgen_ctx.get('reply_classification') or 'n/a'}): "
                    f"{leadgen_ctx['reply_text'][:300]}"
                )
        else:
            findings["leadgen_match"] = {}

        # Alle gefundenen Emails aus allen Strategien
        all_found_emails = []

        # ==============================================================
        # STRATEGIE 1: Firmen-Website finden + scrapen
        # ==============================================================
        print(f"  [S1] Website-Scraping für {company}...")
        company_domain = ""
        if company:
            q1 = f'"{company}" offizielle Website'
            r1 = self._search(q1, max_results=5)
            company_domain = self._find_company_website(company, r1)

            q1b = f'"{clean_name}" "{company}"'
            r1b = self._search(q1b, max_results=5)
            if not company_domain:
                company_domain = self._find_company_website(company, r1b)

            for r in r1 + r1b:
                url = r.get("href", "")
                t = r.get("title", "")
                b = r.get("body", "")
                d = urlparse(url).netloc.replace("www.", "")

                if any(kw in d for kw in firma_kw):
                    company_phones.extend(self._extract_phones_strict(f"{t} {b}"))

                if self._is_about_person(f"{t} {b}", name, company):
                    all_phones.extend(self._extract_phones_strict(f"{t} {b}"))
                    relevant_sources.append(f"{t} → {url}")

                all_texts.append(f"[S1 Website] {t}: {b}\n  URL: {url}")

            if company_domain:
                print(f"  [S1] Scrape {company_domain}...")
                scraped = self._scrape_company_emails(company_domain)
                all_found_emails.extend(scraped)

                for page in ["", "/impressum", "/kontakt", "/contact", "/imprint"]:
                    pt = self._fetch_page_text(f"https://{company_domain}{page}")
                    if not pt:
                        pt = self._fetch_page_text(f"https://www.{company_domain}{page}")
                    if pt:
                        company_phones.extend(self._extract_phones_strict(pt))
                        all_texts.append(f"[S1 Scrape {company_domain}{page}] OK")
                        break
                    time.sleep(1)

        # ==============================================================
        # STRATEGIE 2: Web-Suche nach "@domain"
        # ==============================================================
        if company_domain:
            print(f"  [S2] Web-Suche nach '@{company_domain}'...")
            email_queries = [
                f'"@{company_domain}"',
                f'"@{company_domain}" contact email',
                f'{company} email team press "@{company_domain}"',
            ]
            domain_parts = company_domain.split(".")
            if len(domain_parts) > 2:
                main = ".".join(domain_parts[-2:])
                if main != company_domain:
                    email_queries.append(f'"@{main}"')

            seen_emails = {e["email"] for e in all_found_emails}
            for eq in email_queries:
                for r in self._search(eq, max_results=8):
                    for em in self._extract_emails_from_text(f"{r.get('title','')} {r.get('body','')}"):
                        ed = em.split("@")[1]
                        if (company_domain in ed or any(kw in ed for kw in firma_kw)) and em not in seen_emails:
                            all_found_emails.append({
                                "email": em, "source_url": r.get("href", ""),
                                "page": "web-suche", "methode": "Web-Suche @domain",
                            })
                            seen_emails.add(em)
                    all_texts.append(f"[S2 @domain] {eq}: {r.get('title','')}\n  URL: {r.get('href','')}")

                personal = [e for e in all_found_emails
                            if e["email"].split("@")[0] not in ("info","contact","office","hello","press","media","mail")]
                if personal:
                    break

        # ==============================================================
        # STRATEGIE 3: Hunter.io
        # ==============================================================
        if self.hunter_api_key and company_domain:
            print(f"  [S3] Hunter.io für {company_domain}...")
            hunter = self._hunter_search(company_domain, name)
            if hunter:
                if hunter.get("person_email"):
                    pe = hunter["person_email"]
                    all_found_emails.append({
                        "email": pe["email"], "source_url": pe["source_url"],
                        "page": "Hunter.io", "methode": "Hunter.io (direkt gefunden)",
                    })
                for he in hunter.get("emails", []):
                    if he["email"] not in {e["email"] for e in all_found_emails}:
                        all_found_emails.append(he)

                if hunter.get("pattern"):
                    fmt = self._hunter_pattern_to_format(hunter["pattern"])
                    all_texts.append(f"[S3 Hunter.io] Pattern: {hunter['pattern']} → {fmt}, "
                                     f"Emails: {[e['email'] for e in hunter.get('emails', [])[:5]]}")

        # ==============================================================
        # STRATEGIE 4: Pressemitteilungen
        # ==============================================================
        if company:
            print(f"  [S4] Pressemitteilungen für {company}...")
            press_emails = self._search_press_releases(company, company_domain, name)
            seen = {e["email"] for e in all_found_emails}
            for pe in press_emails:
                if pe["email"] not in seen:
                    all_found_emails.append(pe)
                    seen.add(pe["email"])
            if press_emails:
                all_texts.append(f"[S4 Presse] Gefunden: {[e['email'] for e in press_emails]}")

        # ==============================================================
        # STRATEGIE 5: Google Scholar / PubMed
        # ==============================================================
        if max_searches >= 4:
            print(f"  [S5] Google Scholar / PubMed für {clean_name}...")
            scholar_emails = self._search_scholar(name, company)
            seen = {e["email"] for e in all_found_emails}
            for se in scholar_emails:
                if se["email"] not in seen:
                    all_found_emails.append(se)
                    seen.add(se["email"])
            if scholar_emails:
                all_texts.append(f"[S5 Scholar] Gefunden: {[e['email'] for e in scholar_emails]}")

        # ==============================================================
        # EMAIL-AUSWERTUNG
        # ==============================================================
        print(f"  [Email] {len(all_found_emails)} Emails gefunden, analysiere...")

        email_summary = [f"{e['email']} ({e.get('methode', '')})" for e in all_found_emails]
        all_texts.append(f"[Alle Emails] {email_summary}")

        if all_found_emails:
            for e in all_found_emails:
                e["classification"] = self._classify_email(e["email"], name, company)

            # Priorität: person_exact > firma_mitarbeiter > firma_allgemein
            exact = [e for e in all_found_emails if e["classification"] == "person_exact"]
            mitarbeiter = [e for e in all_found_emails if e["classification"] == "firma_mitarbeiter"]
            allgemein = [e for e in all_found_emails if e["classification"] == "firma_allgemein"]

            if exact:
                best = exact[0]
                findings["email"] = best["email"]
                findings["email_status"] = f"Verifiziert ({best.get('methode', '')})"
                findings["referenz_email"] = best["email"]
                findings["referenz_email_quelle"] = best["source_url"]

            elif mitarbeiter:
                ref = mitarbeiter[0]
                all_personal = [e["email"] for e in all_found_emails
                                if e["classification"] in ("firma_mitarbeiter", "person_exact")]

                # Hunter.io Format bevorzugen wenn vorhanden
                hunter_fmt = None
                if self.hunter_api_key and company_domain:
                    hunter_data = self._hunter_search(company_domain, name)
                    if hunter_data and hunter_data.get("pattern"):
                        hunter_fmt = self._hunter_pattern_to_format(hunter_data["pattern"])

                fmt = hunter_fmt or self._detect_email_format(all_personal)
                if fmt:
                    domain = ref["email"].split("@")[1]
                    constructed = self._construct_email(name, domain, fmt)
                    if constructed:
                        findings["email"] = constructed
                        findings["email_status"] = f"Konstruiert (Format: {fmt})"
                        findings["referenz_email"] = ref["email"]
                        findings["referenz_email_quelle"] = ref["source_url"]

            elif allgemein:
                ref = allgemein[0]
                domain = ref["email"].split("@")[1]
                parts = self._clean_name_parts(name)
                if len(parts) >= 2:
                    findings["email"] = f"{parts[0]}.{parts[-1]}@{domain}"
                    findings["email_status"] = "Konstruiert (nur info@ gefunden, Format geraten)"
                    findings["referenz_email"] = ref["email"]
                    findings["referenz_email_quelle"] = ref["source_url"]

        # Letzter Fallback: Domain bekannt, keine Emails
        if not findings["email"] and company_domain:
            parts = self._clean_name_parts(name)
            if len(parts) >= 2:
                findings["email"] = f"{parts[0]}.{parts[-1]}@{company_domain}"
                findings["email_status"] = "Konstruiert (keine Emails gefunden, Format geraten)"
                findings["referenz_email_quelle"] = f"https://{company_domain}"

        # ==============================================================
        # SMTP-VERIFIZIERUNG
        # ==============================================================
        if findings["email"]:
            print(f"  [SMTP] Verifiziere {findings['email']}...")
            smtp_result = self._verify_email_smtp(findings["email"])
            findings["email_verifizierung"] = f"SMTP-Check: {smtp_result}"
            all_texts.append(f"[SMTP] {findings['email']} → {smtp_result}")

        # ==============================================================
        # KONFERENZEN, PODCASTS, NEWS, KARRIERE
        # ==============================================================
        if max_searches >= 3:
            print(f"  [3/6] Konferenzen...")
            for r in self._search(f'"{clean_name}" conference speaker konferenz 2025 2026', max_results=5):
                url, t, b = r.get("href",""), r.get("title",""), r.get("body","")
                if self._is_about_person(f"{t} {b}", name, company):
                    if any(kw in f"{t} {b}".lower() for kw in
                           ["conference","congress","summit","symposium","konferenz","speaker","panel","expo","webinar"]):
                        conference_facts.append(f"{t} → {url}")
                all_texts.append(f"[Konferenz] {t}: {b}\n  URL: {url}")

            # Bonus: Konferenz-Speakerseiten für Emails
            conf_emails = self._search_conference_speakers(name, company)
            seen = {e["email"] for e in all_found_emails}
            for ce in conf_emails:
                if ce["email"] not in seen:
                    all_found_emails.append(ce)
                    all_texts.append(f"[Konferenz-Email] {ce['email']} von {ce['source_url']}")

        if max_searches >= 4:
            print(f"  [4/6] Podcasts/Videos...")
            for r in self._search(f'"{clean_name}" podcast interview video', max_results=5):
                url, t, b = r.get("href",""), r.get("title",""), r.get("body","")
                if self._is_about_person(f"{t} {b}", name, company):
                    if any(kw in f"{t} {b}".lower() for kw in
                           ["podcast","interview","video","youtube","episode","webinar","talk"]):
                        podcast_facts.append(f"{t} → {url}")
                all_texts.append(f"[Podcast/Video] {t}: {b}\n  URL: {url}")

        if max_searches >= 5:
            print(f"  [5/6] News & LinkedIn...")
            for r in self._search(f'"{clean_name}" {company} news 2025 2026'.strip(), max_results=5):
                url, t, b = r.get("href",""), r.get("title",""), r.get("body","")
                if self._is_about_person(f"{t} {b}", name, company):
                    if "linkedin.com" in url:
                        linkedin_facts.append(f"{t} → {url}")
                    else:
                        other_facts.append(f"{t} → {url}")
                all_texts.append(f"[News] {t}: {b}\n  URL: {url}")

            # LinkedIn-Posts der Person
            for r in self._search(f'site:linkedin.com/posts "{clean_name}" OR site:linkedin.com/pulse "{clean_name}"', max_results=5):
                url, t, b = r.get("href",""), r.get("title",""), r.get("body","")
                linkedin_facts.append(f"{t} → {url}")
                all_texts.append(f"[LinkedIn-Post] {t}: {b}\n  URL: {url}")

        if max_searches >= 6:
            print(f"  [6/6] Karriere & KI-Bezug...")
            for r in self._search(f'"{clean_name}" CEO career biography Lebenslauf', max_results=5):
                url, t, b = r.get("href",""), r.get("title",""), r.get("body","")
                if self._is_about_person(f"{t} {b}", name, company):
                    career_facts.append(f"{t} → {url}")
                all_texts.append(f"[Karriere] {t}: {b}\n  URL: {url}")

            # KI/Digitalisierungs-Bezug der Firma
            if company:
                for r in self._search(f'"{company}" AI artificial intelligence KI digital', max_results=5):
                    url, t, b = r.get("href",""), r.get("title",""), r.get("body","")
                    all_texts.append(f"[KI-Bezug Firma] {t}: {b}\n  URL: {url}")

                # Stellenausschreibungen (Wachstumssignal)
                for r in self._search(f'"{company}" hiring jobs stellenanzeige careers', max_results=3):
                    url, t, b = r.get("href",""), r.get("title",""), r.get("body","")
                    all_texts.append(f"[Stellenanzeigen] {t}: {b}\n  URL: {url}")

        # ==============================================================
        # ERGEBNISSE (vor Claude-Analyse zusammenstellen)
        # ==============================================================
        if all_phones:
            findings["personal_phone"] = all_phones[0]
        if company_phones:
            findings["company_phone"] = company_phones[0]

        findings["conferences"] = "\n".join(conference_facts[:3]) if conference_facts else "Nicht gefunden"
        findings["podcasts_videos"] = "\n".join(podcast_facts[:3]) if podcast_facts else "Nicht gefunden"
        findings["job_changes"] = "\n".join(career_facts[:3]) if career_facts else "Nicht gefunden"
        findings["linkedin_activity"] = "\n".join(linkedin_facts[:3]) if linkedin_facts else "Nicht gefunden"
        if other_facts:
            findings["relevant_info"] = "\n".join(other_facts[:5])

        findings["raw_findings"] = "\n\n".join(all_texts)
        findings["sources"] = relevant_sources

        # ==============================================================
        # DEEP RESEARCH: Plan → Search → Analyze (3-Stufen-Workflow)
        # ==============================================================
        deep_research_results = ""
        if self.api_key and self.llm_provider == "gemini":
            try:
                # Schritt 1: Recherche-Plan erstellen
                research_questions = self._plan_research(name, company, title, location)
                # Schritt 2: Gezielte Recherche mit Google Grounding
                deep_research_results = self._execute_research(research_questions, name, company)
            except Exception as e:
                print(f"  [Deep Research] ⚠️ Fehler: {e} — fahre ohne Deep Research fort")

        # ==============================================================
        # LLM-ANALYSE: Zusammenfassung + Nachricht + Kanal-Empfehlung
        # ==============================================================
        if self.api_key and (all_texts or deep_research_results):
            claude = self._analyze_with_llm(
                name=name,
                company=company,
                title=title,
                location=location,
                search_results="\n\n".join(all_texts),
                findings=findings,
                deep_research_results=deep_research_results,
            )
            if claude:
                findings["zusammenfassung"] = claude.get("zusammenfassung", "")
                findings["personalisierte_nachricht"] = claude.get("personalisierte_nachricht", "")
                nachricht_betreff = claude.get("nachricht_betreff", "")
                kanal = claude.get("kanal_empfehlung", "")
                begruendung = claude.get("kanal_begruendung", "")
                findings["kanal_empfehlung"] = f"{kanal} — {begruendung}" if begruendung else kanal

                # Betreff in die Nachricht einfügen wenn Email empfohlen
                if nachricht_betreff and "EMAIL" in kanal.upper():
                    findings["personalisierte_nachricht"] = (
                        f"Betreff: {nachricht_betreff}\n\n{findings['personalisierte_nachricht']}"
                    )

                # Anknüpfungspunkte in relevant_info ergänzen
                ankn = claude.get("anknuepfungspunkte", "")
                if ankn:
                    existing = findings.get("relevant_info", "")
                    findings["relevant_info"] = f"{ankn}\n\n{existing}" if existing else ankn

                # Monitoring-Tags für wöchentliche Delta-Scans speichern
                monitoring_tags = claude.get("monitoring_tags", [])
                if monitoring_tags:
                    findings["monitoring_tags"] = json.dumps(monitoring_tags, ensure_ascii=False)

        # ==============================================================
        # PFLICHTFELD-FALLBACKS: Diese 4 Felder sind NIEMALS leer
        # Kombiniert: LLM-Analyse + LeadGen-DB + Web-Scraping + Logik
        # ==============================================================
        lg = findings.get("leadgen_match", {}) or {}
        lg_status = lg.get("status", "") if lg.get("matched") else ""

        # 1. KI-Zusammenfassung — mindestens Basis-Facts
        if not findings["zusammenfassung"].strip():
            parts = []
            parts.append(f"{name} ist {title} bei {company}." if title and company else f"Kontakt: {name}.")
            if location:
                parts.append(f"Standort: {location}.")
            if lg_status:
                parts.append(f"Outbound-Status: {lg_status}.")
            if findings.get("email"):
                parts.append(f"Email: {findings['email']} ({findings.get('email_status', '')}).")
            if findings.get("conferences") and findings["conferences"] != "Nicht gefunden":
                parts.append(f"Konferenzen: {findings['conferences'][:200]}.")
            if findings.get("linkedin_activity") and findings["linkedin_activity"] != "Nicht gefunden":
                parts.append(f"LinkedIn: {findings['linkedin_activity'][:200]}.")
            parts.append("Wenig öffentliche Informationen verfügbar — persönliche Recherche empfohlen.")
            findings["zusammenfassung"] = " ".join(parts)
            print(f"  [Fallback] KI-Zusammenfassung aus Basis-Daten generiert")

        # 2. Personalisierte Nachricht — immer eine sendbare Nachricht
        if not findings["personalisierte_nachricht"].strip():
            german_indicators = ["deutsch", "dach", "germany", "austria", "swiss",
                                 "münchen", "berlin", "hamburg", "köln", "de"]
            is_de = any(ind in (location or "").lower() for ind in german_indicators)
            if lg.get("matched") and lg.get("reply_text"):
                # Bekannter Kontakt mit Reply → Follow-up
                if is_de:
                    findings["personalisierte_nachricht"] = (
                        f"Hallo {name.split()[0]},\n\n"
                        f"danke für die Rückmeldung! Wie sieht es aktuell bei {company} "
                        f"mit dem Thema KI-Strategie aus — hat sich seit unserem letzten "
                        f"Austausch etwas getan?\n\n"
                        f"Herzliche Grüße, Selina"
                    )
                else:
                    findings["personalisierte_nachricht"] = (
                        f"Hi {name.split()[0]},\n\n"
                        f"Thanks for getting back! How are things at {company} regarding "
                        f"AI strategy — has anything changed since we last connected?\n\n"
                        f"Best wishes, Selina"
                    )
            elif is_de:
                findings["personalisierte_nachricht"] = (
                    f"Hallo {name.split()[0]},\n\n"
                    f"ich beschäftige mich intensiv mit KI-Strategie in Life Science & MedTech "
                    f"und bin auf {company} aufmerksam geworden. Mich würde interessieren: "
                    f"Wie geht ihr bei {company} aktuell das Thema KI an?\n\n"
                    f"Herzliche Grüße, Selina"
                )
            else:
                findings["personalisierte_nachricht"] = (
                    f"Hi {name.split()[0]},\n\n"
                    f"I focus on AI strategy for Life Science & MedTech and came across {company}. "
                    f"I'd be curious to know: how is {company} currently approaching AI?\n\n"
                    f"Best wishes, Selina"
                )
            print(f"  [Fallback] Personalisierte Nachricht generiert")

        # 3. Kanal-Empfehlung — immer eine Empfehlung
        if not findings["kanal_empfehlung"].strip():
            if findings.get("email") and "verifiziert" in findings.get("email_status", "").lower():
                findings["kanal_empfehlung"] = "EMAIL — Verifizierte Email vorhanden"
            elif findings.get("email"):
                findings["kanal_empfehlung"] = "EMAIL — Email gefunden (konstruiert, bitte prüfen)"
            else:
                findings["kanal_empfehlung"] = "LINKEDIN — Keine sichere Email verfügbar"
            print(f"  [Fallback] Kanal-Empfehlung generiert")

        # 4. Relevante Infos für Ansprache — immer ausfüllen
        if not findings.get("relevant_info", "").strip():
            info_parts = []
            if title and company:
                info_parts.append(f"• {title} bei {company}")
            if location:
                info_parts.append(f"• Standort: {location}")
            if lg_status:
                info_parts.append(f"• Bereits kontaktiert (Status: {lg_status})")
            if lg.get("reply_text"):
                info_parts.append(f"• Hat geantwortet: \"{lg['reply_text'][:100]}...\"")
            if findings.get("conferences") and findings["conferences"] != "Nicht gefunden":
                info_parts.append(f"• Konferenzen: {findings['conferences'][:150]}")
            if not info_parts:
                info_parts.append("• Wenig öffentliche Daten — persönliche LinkedIn-Recherche empfohlen")
                info_parts.append(f"• Branche/Titel legen KI-Strategiebedarf nahe (Life Science / MedTech)")
            findings["relevant_info"] = "\n".join(info_parts)
            print(f"  [Fallback] Relevante Infos aus Basis-Daten generiert")

        return findings

    # ==================================================================
    # CLAUDE-ANALYSE: Verdaute Zusammenfassung + Personalisierte Nachricht
    # ==================================================================

    def _analyze_with_llm(self, name, company, title, location, search_results, findings, deep_research_results=""):
        """
        LLM-Analyse: Alle Fundstücke werden mit Selinas Profil abgeglichen.
        Unterstützt zwei Provider:
        - "gemini"     → Gemini 2.5 Flash + Google Search Grounding (schnell, günstig, top DACH-Abdeckung)
        - "perplexity" → Perplexity sonar-deep-research (30+ Suchläufe, tiefste Recherche)
        """
        if not self.api_key:
            return {}
        try:
            # Prompt-Injection-Schutz: User-Inputs sanitizen
            safe_name = _sanitize_llm_input(name, 200)
            safe_company = _sanitize_llm_input(company, 200)
            safe_title = _sanitize_llm_input(title, 200)
            safe_location = _sanitize_llm_input(location, 200)

            # Sprache aus Location/Suche ableiten
            german_indicators = ["deutsch", "dach", "germany", "austria", "swiss",
                                 "münchen", "berlin", "hamburg", "köln", "frankfurt",
                                 "zürich", "wien", "stuttgart", "de"]
            loc_lower = (location or "").lower()
            is_german = any(ind in loc_lower for ind in german_indicators)
            sprache = "Deutsch" if is_german else "Englisch"

            # Kontakt-Zusammenfassung für den Prompt
            kontakt_info = f"""
KONTAKT:
- Name: {safe_name}
- Titel: {safe_title}
- Firma: {safe_company}
- Standort: {safe_location}
- Gefundene Email: {findings.get('email', 'Nicht gefunden')} (Status: {findings.get('email_status', '')})
- SMTP-Check: {findings.get('email_verifizierung', 'nicht geprüft')}
- Persönliches Telefon: {findings.get('personal_phone', 'Nicht gefunden')}
- Firmentelefon: {findings.get('company_phone', 'Nicht gefunden')}
"""

            # LeadGen-Context: falls die Person schon in Selinas Outbound-DB ist,
            # den Timeline/Reply-Kontext ins Prompt mitgeben
            leadgen_block = _format_leadgen_context_for_llm(findings.get("leadgen_match", {}))

            prompt = f"""Du bist Selinas Deep Research Assistentin. Deine Aufgabe: Aus allen Recherche-Ergebnissen
ein vollständiges Dossier über diesen Kontakt erstellen und eine kurze, persönliche Nachricht formulieren.

{SELINA_PROFIL}

{kontakt_info}

{leadgen_block}

═══════════════════════════════════════════════════
DEEP RESEARCH ERGEBNISSE (Google-Recherche):
═══════════════════════════════════════════════════
{deep_research_results[:12000] if deep_research_results else "Keine Deep Research durchgeführt."}

═══════════════════════════════════════════════════
ZUSÄTZLICHE WEB-SCRAPING ERGEBNISSE:
═══════════════════════════════════════════════════
{search_results[:8000]}

═══════════════════════════════════════════════════
DEEP RESEARCH DOSSIER — AUFGABEN:
═══════════════════════════════════════════════════

1. **VOLLSTÄNDIGES DOSSIER** (für Selina als Vorbereitung):
   Gehe JEDE Kategorie systematisch durch. Nutze NUR echte Fakten mit Quellenlinks.
   Wenn du zu einer Kategorie nichts findest → "Keine Daten gefunden."

   A) PERSON & ROLLE:
      - Aktueller Titel, Firma, Verantwortungsbereich, Teamgröße
      - Karriereweg: Alle vorherigen Positionen, Werdegang (Aufstieg? Branchenwechsel?)
      - Ausbildung (Uni, Abschluss, Promotion?)
      - Expertise-Gebiete, Spezialisierungen, Fachgebiete
      - Awards, Auszeichnungen, Advisory Board Positionen

   B) FIRMA & MARKT:
      - Was macht die Firma genau? Kernprodukte/Services, Technologie-Plattform
      - Branche, Indikationsgebiete, Therapiefelder
      - Firmengröße (Mitarbeiter, Umsatz falls bekannt), Standorte
      - Marktposition, Wettbewerber, Alleinstellungsmerkmal
      - Funding-Runden, Investoren (bei Startups)
      - Aktuelle Entwicklungen: Partnerschaften, Produktlaunches, M&A, klinische Studien
      - Stellenausschreibungen (Hinweis auf Wachstum? Suchen sie KI/Digital-Experten?)

   C) KI & DIGITALISIERUNG (KERNKATEGORIE für Selina):
      - Nutzt die Person/Firma bereits KI? Welche Tools, Plattformen, Ansätze?
      - Hat die Person sich öffentlich zu KI/AI geäußert? (LinkedIn-Posts, Interviews, Panels)
      - Gibt es ein Digitalisierungsprojekt, einen CDO/CTO, eine Digital-Strategie?
      - Regulatorische Situation: MDR, IVDR, EU AI Act — betroffen? Vorbereitet?
      - "Shadow AI" Risiko: Nutzen Teams unkontrolliert ChatGPT o.ä.?
      - KI in Sales/Marketing/Medical Affairs — gibt es Ansätze?
      - Automatisierung: CRM, Pipeline, Forecasting — manuell oder digital?
      - Arbeitet die Firma bereits mit einem KI-Berater? (Wettbewerber von Selina?)

   D) ÖFFENTLICHE AUFTRITTE & CONTENT:
      - Konferenzen VERGANGENES JAHR (2025): Welche? Als Speaker oder Teilnehmer?
      - Konferenzen BEVORSTEHEND (2026): Geplante Auftritte, registriert?
      - Podcasts: Gast in Podcasts? Eigener Podcast?
      - Videos: YouTube, LinkedIn-Videos, Webinar-Auftritte
      - Publikationen: Papers, Artikel, Patente, Bücher
      - LinkedIn-Aktivität: Wie oft postet die Person? Welche Themen? Engagement?
      - Andere Social Media: Twitter/X, Blogs, Newsletter?

   E) PERSÖNLICHES & SOFT FACTS:
      - Geburtstag (falls öffentlich auf LinkedIn/XING)
      - Persönliche Interessen, Hobbies (aus Posts/Interviews ableitbar?)
      - Ehrenämter, Vereinsmitgliedschaften, Stiftungen, Beiräte
      - Alma Mater — gleiche Uni wie Selina (Konstanz, Lübeck)?
      - Gemeinsame LinkedIn-Kontakte mit Selina (aus dem Netzwerk-Abgleich oben)
      - Sprache: Kommuniziert die Person auf Deutsch oder Englisch?
      - Familienstand, Kinder (nur wenn öffentlich und relevant, z.B. "Familienmensch")

   F) STRATEGISCHE ANALYSE FÜR SELINA:
      - Die 3 STÄRKSTEN Anknüpfungspunkte (priorisiert nach Relevanz):
        Warum genau DIESER Kontakt für Selina spannend ist
      - Konkrete Schmerzpunkte die Selina lösen könnte:
        • Lange Sales-Zyklen? Ineffiziente Prozesse? Unsichere Forecasts?
        • Fehlende KI-Strategie? Compliance-Risiken? Shadow AI?
        • Team-Überlastung? Manuelle CRM-Pflege? Pipeline-Probleme?
      - Timing-Signale (JETZT ist ein guter Zeitpunkt weil...):
        • Kürzlicher Jobwechsel (neue Besen kehren gut — offen für neue Ansätze)
        • Neues Funding (Budget für Beratung vorhanden)
        • Stellenanzeige für Digital/KI-Rolle (Thema ist auf der Agenda)
        • Konferenz-Teilnahme (Person ist gerade im "Lern-Modus")
        • Regulatorische Deadline (EU AI Act, MDR-Übergang)
      - Risiken/Hindernisse:
        • Hat die Firma bereits einen KI-Berater?
        • Ist die Person bekannt als "KI-Skeptiker"?
        • Zu kleines Unternehmen für Beratungsprojekt?

   G) GESPRÄCHS-VORBEREITUNG (falls es zum Call kommt):
      - 3 gute Gesprächseinstiegsfragen
      - 2 Themen die Selina VERMEIDEN sollte
      - Tonalität-Empfehlung (formell/informell, Du/Sie)

2. **PERSONALISIERTE NACHRICHT** (fertig zum Kopieren & Absenden):
   Schreibe eine KURZE Nachricht. Selina soll sie 1:1 senden können.

   REGELN:
   - Sprache: {sprache}
   - KURZ: Max 3-4 Sätze für LinkedIn / max 5-6 Sätze für Email
   - Beziehe dich auf genau 1 konkreten, recherchierten Fakt
   - Natürlich, auf Augenhöhe — kein Pitch, keine Floskeln
   - KEIN "Ich bin beeindruckt" oder "Ich würde mich freuen"
   - KEINE Links (Scorecard/Calendly) in der ersten Nachricht
   - IMMER mit einem klaren CTA enden (siehe CTA-Optionen oben)
   - Signatur: {"Herzliche Grüße, Selina" if sprache == "Deutsch" else "Best wishes, Selina"}

3. **KANAL-EMPFEHLUNG** (EMAIL oder LINKEDIN):
   - "EMAIL" wenn: verifizierte Email, Person postet wenig auf LinkedIn, B2B-Berater/CEO
   - "LINKEDIN" wenn: keine/unsichere Email, Person aktiv auf LinkedIn, noch keine Connection
   - Begründe in 1 Satz.

4. **MONITORING-TAGS** (für wöchentliche Delta-Scans):
   Erstelle 8-10 spezifische Suchbegriffe für den wöchentlichen Scan:
   - "[Firmenname]" + news/partnership/funding/hiring
   - "[Personenname]" + conference/speaker/podcast/interview 2026
   - "[Firmenname]" + AI/KI/digital/automation
   - "[Firmenname]" + EU AI Act/MDR/IVDR/compliance
   - "[Personenname]" + LinkedIn (für neue Posts)
   Diese Tags werden beim nächsten Scan verwendet um NUR NEUE Infos zu finden.

═══════════════════════════════════════════════════
ABSOLUTE PFLICHT — DIESE 4 FELDER MÜSSEN IMMER AUSGEFÜLLT WERDEN:
═══════════════════════════════════════════════════

Auch wenn die Recherche wenig ergibt: Kombiniere ALLES was du hast —
Deep Research + Web-Scraping + LeadGen-DB-Kontext (falls vorhanden) +
Branchenwissen + logische Schlussfolgerungen aus Titel/Firma/Standort.

1. **zusammenfassung** → IMMER ausfüllen. Minimum 5 Sätze. Fasse zusammen was du über
   Person, Firma, KI-Bezug und Anknüpfungspunkte weißt. Wenn wenig gefunden:
   schreibe was du aus Titel+Firma+Branche ABLEITEN kannst (z.B. "Als CEO eines
   MedTech-Unternehmens in München ist davon auszugehen, dass...")

2. **personalisierte_nachricht** → IMMER ausfüllen. Fertige Nachricht, 1:1 sendbar.
   Wenn wenig Fakten: nutze Titel + Firma + Branche als Hook. Es gibt IMMER
   genug für eine authentische Nachricht.

3. **kanal_empfehlung** → IMMER ausfüllen. "EMAIL" oder "LINKEDIN" + Begründung.

4. **anknuepfungspunkte** → IMMER ausfüllen. Minimum 2 Punkte. Wenn wenig gefunden:
   leite aus Branche/Titel/Firma ab (z.B. "CEO eines Life-Science-Unternehmens →
   EU AI Act und MDR-Compliance sind aktuelle Themen").

NIEMALS leere Strings ("") oder "Keine Daten gefunden" für diese 4 Felder zurückgeben.
Leere Felder sind ein FEHLER.

Antworte im folgenden JSON-Format (ohne Markdown-Codeblock):
{{
  "zusammenfassung": "Vollständiges Dossier mit allen Kategorien A-G...",
  "personalisierte_nachricht": "Kurze, fertige Nachricht (3-4 Sätze + CTA + Signatur)...",
  "nachricht_betreff": "Betreff-Zeile falls Email empfohlen (sonst leer)",
  "kanal_empfehlung": "EMAIL oder LINKEDIN",
  "kanal_begruendung": "Kurze Begründung...",
  "anknuepfungspunkte": "Top 3 Anknüpfungspunkte als Stichpunkte...",
  "monitoring_tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"]
}}"""

            if self.llm_provider == "gemini":
                text = self._call_gemini(prompt, max_tokens=6000)
            else:
                text = self._call_perplexity(prompt, max_tokens=6000)

            # JSON extrahieren
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.split("```")[0].strip()

            result = json.loads(text)
            print(f"  [LLM] ✅ Analyse fertig — Kanal: {result.get('kanal_empfehlung', '?')}")
            return result

        except json.JSONDecodeError as e:
            print(f"  [LLM] JSON-Parse-Fehler: {e}")
            print(f"  [LLM] Rohtext: {text[:200]}...")
            return {}
        except Exception as e:
            print(f"  [LLM] {self.llm_provider.capitalize()}-Fehler: {e}")
            return {}

    # ==================================================================
    # DELTA-SCAN: Wöchentliches Monitoring auf neue Infos
    # ==================================================================

    def delta_scan(
        self,
        name: str,
        company: str = "",
        title: str = "",
        location: str = "",
        monitoring_tags: list[str] = None,
        previous_summary: str = "",
    ) -> dict:
        """
        Wöchentlicher Delta-Scan: Sucht NUR nach neuen Infos seit dem letzten Scan.
        Verwendet monitoring_tags aus dem vorherigen Dossier.
        Gibt neue Fakten + angepasste Follow-up-Nachricht zurück.
        """
        if not monitoring_tags:
            monitoring_tags = [
                f'"{name}" {company}',
                f'"{company}" news',
                f'"{name}" conference 2026',
                f'"{company}" hiring',
                f'"{name}" LinkedIn',
            ]

        # NaN/None bereinigen
        if not company or str(company).lower() in ("nan", "none", ""):
            company = ""

        all_texts = []
        print(f"  [DELTA] Starte wöchentlichen Scan für {name}...")

        for tag in monitoring_tags:
            results = self._search(tag, max_results=5)
            for r in results:
                url = r.get("href", "")
                t = r.get("title", "")
                b = r.get("body", "")
                all_texts.append(f"[DELTA: {tag}] {t}: {b}\n  URL: {url}")
            time.sleep(2)

        if not all_texts:
            print(f"  [DELTA] Keine neuen Ergebnisse gefunden.")
            return {"has_updates": False, "neue_infos": "", "follow_up_nachricht": ""}

        # Delta-Analyse mit LLM
        if not self.api_key:
            return {"has_updates": False}

        try:

            # Sprache ableiten
            german_indicators = ["deutsch", "dach", "germany", "austria", "swiss",
                                 "münchen", "berlin", "hamburg", "de"]
            loc_lower = (location or "").lower()
            is_german = any(ind in loc_lower for ind in german_indicators)
            sprache = "Deutsch" if is_german else "Englisch"

            delta_prompt = f"""Du bist Selinas Deep Research Assistentin im DELTA-MODUS.
Aufgabe: Prüfe ob es NEUE, relevante Infos über diesen Kontakt gibt seit dem letzten Scan.

{SELINA_PROFIL}

KONTAKT: {name} — {title} bei {company} ({location})

BISHERIGES DOSSIER (letzter Scan):
{previous_summary[:5000]}

═══════════════════════════════════════════════════
NEUE SUCHERGEBNISSE:
═══════════════════════════════════════════════════
{chr(10).join(all_texts[:10000])}

═══════════════════════════════════════════════════
DEINE AUFGABEN:
═══════════════════════════════════════════════════

1. **NEUE INFOS IDENTIFIZIEREN**:
   Vergleiche die neuen Suchergebnisse mit dem bisherigen Dossier.
   Liste NUR Infos auf die NEU sind (nicht schon im Dossier standen):
   - Neue Konferenzen / Events
   - Neue Stellenausschreibungen der Firma
   - Neue LinkedIn-Posts oder Artikel
   - Jobwechsel oder neue Rolle
   - Neue Partnerschaften / Produkte / Funding
   - Neue Publikationen / Podcasts / Videos
   - Regulatorische Neuigkeiten (MDR, IVDR, EU AI Act Bezug)
   Falls KEINE relevanten neuen Infos: setze has_updates auf false.

2. **FOLLOW-UP NACHRICHT** (nur wenn es neue Infos gibt):
   Schreibe eine KURZE Follow-up Nachricht basierend auf der neuen Info.
   - Sprache: {sprache}
   - Max 3 Sätze + CTA
   - Beziehe dich auf die konkrete neue Info ("Ich habe gesehen, dass...")
   - CTA-Optionen:
     • "Ich habe einen kurzen AI Readiness Check gebaut — wäre das interessant?"
     • "Hätten Sie Lust, sich dazu 30 Min auszutauschen?"
     • "Wie gehen Sie aktuell mit [konkretes Thema] um?"
     • "Sind Sie beim KI Summit in Berlin (24.-25. April) dabei?"
   - Signatur: {"Herzliche Grüße, Selina" if sprache == "Deutsch" else "Best wishes, Selina"}

Antworte im JSON-Format (ohne Markdown-Codeblock):
{{
  "has_updates": true/false,
  "neue_infos": "Zusammenfassung der neuen Fakten (oder leer wenn keine)",
  "update_kategorie": "conference|job_change|hiring|publication|news|linkedin_post|regulatory|other",
  "follow_up_nachricht": "Kurze Nachricht basierend auf neuer Info (oder leer)",
  "nachricht_betreff": "Betreff falls Email (oder leer)",
  "monitoring_tags": ["aktualisierte", "suchbegriffe", "für", "nächsten", "scan"]
}}"""

            provider_label = "Gemini 2.5 Flash" if self.llm_provider == "gemini" else "Perplexity Deep Research"
            print(f"  [DELTA-LLM] Analysiere neue Fundstücke mit {provider_label}...")
            if self.llm_provider == "gemini":
                text = self._call_gemini(delta_prompt, max_tokens=2000)
            else:
                text = self._call_perplexity(delta_prompt, max_tokens=2000)

            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.split("```")[0].strip()

            result = json.loads(text)
            has_updates = result.get("has_updates", False)
            kategorie = result.get("update_kategorie", "")
            print(f"  [DELTA-LLM] ✅ {'Neue Infos gefunden: ' + kategorie if has_updates else 'Keine relevanten Updates'}")
            return result

        except json.JSONDecodeError as e:
            print(f"  [DELTA-LLM] JSON-Parse-Fehler: {e}")
            return {"has_updates": False}
        except Exception as e:
            print(f"  [DELTA-LLM] Fehler: {e}")
            return {"has_updates": False}
