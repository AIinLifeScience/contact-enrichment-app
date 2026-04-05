"""
Contact Data Enrichment App
============================
Streamlit-App: Lädt Kontaktliste, geht automatisch ALLE Kontakte durch,
sucht E-Mail, Telefon, Firmentelefon, Konferenzen, Podcasts, Jobwechsel etc.
und speichert alles in eine neue angereicherte Excel-Datei.
"""

import streamlit as st
import pandas as pd
import os
import time
from io import BytesIO
from datetime import datetime
from pathlib import Path

from enrichment_engine import EnrichmentEngine

# --- .env Datei laden (lokale API Keys) ---
def _load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())
_load_env()

# --- Page Config ---
st.set_page_config(
    page_title="Contact Enrichment Tool",
    page_icon="🔍",
    layout="wide",
)

# --- Constants ---
DEFAULT_EXCEL = "/Users/selina/Documents/AI Products I build/selina-ai-leadgen/kontakte.xlsx"
DEFAULT_OUTPUT_DIR = "/Users/selina/Documents/AI Products I build/selina-ai-leadgen"

NEW_COLUMNS = [
    "E-Mail",
    "E-Mail Status",
    "E-Mail Verifizierung",
    "Referenz-Email",
    "Referenz-Email Quelle",
    "Persönliches Telefon",
    "Firmentelefon (Impressum)",
    "Konferenzen (2025/2026)",
    "Podcasts / Videos",
    "Jobwechsel / Karriere",
    "LinkedIn-Aktivität",
    "Geburtstag",
    "Relevante Infos für Ansprache",
    "KI-Zusammenfassung",
    "Personalisierte Nachricht",
    "Kanal-Empfehlung (Email/LinkedIn)",
    "Monitoring-Tags (Delta-Scan)",
    "Enrichment Datum",
]

# Column name mappings for flexible Excel formats
NAME_COLS = ["Name", "name", "NAME", "Kontakt", "kontakt"]
FIRMA_COLS = ["Firma", "firma", "Company", "company", "Unternehmen"]
TITEL_COLS = ["Titel/Position", "Titel", "Position", "Title", "titel"]
ORT_COLS = ["Kontakt Standort", "Standort", "Location", "Stadt", "Firma Stadt"]


def find_column(df, candidates):
    """Findet die erste passende Spalte aus einer Liste von Kandidaten."""
    for col_name in candidates:
        if col_name in df.columns:
            return col_name
    return None


def get_cell_value(row, col_name):
    """Holt einen Wert aus einer Zeile, gibt '' zurück wenn leer/None."""
    if col_name is None:
        return ""
    val = row.get(col_name)
    if pd.isna(val) or val is None or str(val).strip().lower() in ("none", "nan", ""):
        return ""
    return str(val).strip()


def is_already_enriched(row):
    """Prüft ob ein Kontakt bereits angereichert wurde (hat schon E-Mail-Daten)."""
    for col in ["E-Mail", "E-Mail Status", "Enrichment Datum"]:
        if col in row.index:
            val = row.get(col)
            if pd.notna(val) and str(val).strip() and str(val).strip().lower() != "none":
                return True
    return False


def run_enrichment(df, engine, max_searches, skip_enriched, progress_bar, status_container):
    """Geht ALLE Kontakte durch und reichert sie an."""
    name_col = find_column(df, NAME_COLS)
    firma_col = find_column(df, FIRMA_COLS)
    titel_col = find_column(df, TITEL_COLS)
    ort_col = find_column(df, ORT_COLS)

    if not name_col:
        st.error("Keine 'Name'-Spalte gefunden!")
        return {}

    results = {}
    total = len(df)
    skipped = 0
    errors = 0

    for idx, row in df.iterrows():
        name = get_cell_value(row, name_col)
        firma = get_cell_value(row, firma_col)
        titel = get_cell_value(row, titel_col)
        ort = get_cell_value(row, ort_col)

        if not name:
            skipped += 1
            progress_bar.progress((idx + 1) / total)
            continue

        # Skip already enriched contacts
        if skip_enriched and is_already_enriched(row):
            skipped += 1
            with status_container:
                st.markdown(f"⏭️ **{idx+1}/{total}:** {name} — bereits angereichert, übersprungen")
            progress_bar.progress((idx + 1) / total)
            continue

        with status_container:
            st.markdown(f"🔍 **{idx+1}/{total}:** Recherchiere **{name}** ({firma})...")

        try:
            result = engine.enrich_contact(
                name=name,
                company=firma,
                title=titel,
                location=ort,
                max_searches=max_searches,
            )
            results[idx] = result

            # Kurze Zusammenfassung anzeigen
            email_info = result.get("email", "-") or "-"
            phone_info = result.get("personal_phone", "-") or "-"
            with status_container:
                st.markdown(
                    f"✅ **{name}** — "
                    f"E-Mail: `{email_info}` | "
                    f"Tel: `{phone_info}` | "
                    f"Status: {result.get('email_status', '-')}"
                )

        except Exception as e:
            errors += 1
            results[idx] = {"error": str(e)}
            with status_container:
                st.markdown(f"❌ **{name}** — Fehler: {e}")

        progress_bar.progress((idx + 1) / total)

    return results, skipped, errors


def save_enriched_excel(df, results, output_path):
    """Speichert die angereicherte Excel-Datei mit Formatierung."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    enriched_df = df.copy()

    # Neue Spalten hinzufügen
    for col_name in NEW_COLUMNS:
        if col_name not in enriched_df.columns:
            enriched_df[col_name] = ""

    # Mapping von internen Keys zu Spaltennamen
    key_to_col = {
        "email": "E-Mail",
        "email_status": "E-Mail Status",
        "email_verifizierung": "E-Mail Verifizierung",
        "referenz_email": "Referenz-Email",
        "referenz_email_quelle": "Referenz-Email Quelle",
        "personal_phone": "Persönliches Telefon",
        "company_phone": "Firmentelefon (Impressum)",
        "conferences": "Konferenzen (2025/2026)",
        "podcasts_videos": "Podcasts / Videos",
        "job_changes": "Jobwechsel / Karriere",
        "linkedin_activity": "LinkedIn-Aktivität",
        "birthday": "Geburtstag",
        "relevant_info": "Relevante Infos für Ansprache",
        "zusammenfassung": "KI-Zusammenfassung",
        "personalisierte_nachricht": "Personalisierte Nachricht",
        "kanal_empfehlung": "Kanal-Empfehlung (Email/LinkedIn)",
        "monitoring_tags": "Monitoring-Tags (Delta-Scan)",
    }

    # Ergebnisse eintragen
    for idx, result in results.items():
        if "error" in result:
            enriched_df.at[idx, "Relevante Infos für Ansprache"] = f"FEHLER: {result['error']}"
            continue
        for key, col_name in key_to_col.items():
            val = result.get(key, "")
            if val:
                enriched_df.at[idx, col_name] = val
        enriched_df.at[idx, "Enrichment Datum"] = datetime.now().strftime("%Y-%m-%d")

    # Als Excel speichern
    enriched_df.to_excel(output_path, index=False, engine="openpyxl")

    # Formatierung anwenden
    wb = openpyxl.load_workbook(output_path)
    ws = wb.active

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
    new_col_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    enriched_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    error_fill = PatternFill(start_color="FCE4EC", end_color="FCE4EC", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    original_col_count = len(df.columns)
    total_cols = len(enriched_df.columns)

    # Header formatieren
    for col_idx in range(1, total_cols + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = thin_border
        cell.fill = header_fill if col_idx <= original_col_count else new_col_fill

    # Datenzeilen formatieren
    for row_idx in range(2, ws.max_row + 1):
        for col_idx in range(1, total_cols + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = thin_border
            cell.alignment = Alignment(wrap_text=True, vertical="top")

        # Neue Spalten grün markieren wenn befüllt
        row_data_idx = row_idx - 2  # 0-based index
        if row_data_idx in results:
            result = results[row_data_idx]
            fill = error_fill if "error" in result else enriched_fill
            for col_idx in range(original_col_count + 1, total_cols + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                if cell.value:
                    cell.fill = fill

    # Spaltenbreiten
    for col_idx in range(1, total_cols + 1):
        letter = openpyxl.utils.get_column_letter(col_idx)
        if col_idx <= original_col_count:
            ws.column_dimensions[letter].width = 20
        else:
            ws.column_dimensions[letter].width = 35

    # Name-Spalte breiter
    ws.column_dimensions["A"].width = 25

    # Freeze header + Auto-Filter
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{openpyxl.utils.get_column_letter(total_cols)}1"

    wb.save(output_path)
    return enriched_df


# ============================================================
# UI
# ============================================================

st.title("🔍 Contact Data Enrichment")
st.markdown("Lädt die Kontaktliste und reichert **automatisch alle Kontakte** an.")

# --- Sidebar ---
st.sidebar.title("⚙️ Einstellungen")

llm_choice = st.sidebar.radio(
    "🤖 KI-Modell",
    [
        "🚀 Gemini 2.5 Flash (schnell & günstig)",
        "🔬 Perplexity Deep Research (tiefste Recherche)",
    ],
    help=(
        "Gemini: ~5-10 Sek/Kontakt, sehr günstig, beste DACH-Abdeckung via Google Search.\n\n"
        "Perplexity: 30-90 Sek/Kontakt, 30+ Suchläufe automatisch, tiefste Dossiers."
    ),
)
llm_provider = "gemini" if "Gemini" in llm_choice else "perplexity"

if llm_provider == "gemini":
    api_key = st.sidebar.text_input(
        "Google Gemini API Key",
        value=os.environ.get("GEMINI_API_KEY", ""),
        type="password",
        help="Kostenlos via Google AI Studio (aistudio.google.com). Sehr günstiges Paid-Tier.",
    )
else:
    api_key = st.sidebar.text_input(
        "Perplexity API Key",
        value=os.environ.get("PERPLEXITY_API_KEY", ""),
        type="password",
        help="Via perplexity.ai → API → API Keys.",
    )

if not api_key:
    st.sidebar.warning("Ohne API Key: Keine KI-Zusammenfassung und keine personalisierten Nachrichten.")

hunter_api_key = st.sidebar.text_input(
    "Hunter.io API Key (optional)",
    value=os.environ.get("HUNTER_API_KEY", ""),
    type="password",
    help="Free Tier: 25 Suchen/Monat. Findet Email-Formate von Firmen. https://hunter.io",
)

search_depth = st.sidebar.selectbox(
    "Suchtiefe pro Kontakt",
    ["Schnell (3 Suchen)", "Normal (6 Suchen)", "Gründlich (10 Suchen)"],
    index=1,
)
depth_map = {"Schnell (3 Suchen)": 3, "Normal (6 Suchen)": 6, "Gründlich (10 Suchen)": 10}
max_searches = depth_map[search_depth]

skip_enriched = st.sidebar.checkbox(
    "Bereits angereicherte überspringen",
    value=True,
    help="Kontakte die schon eine E-Mail/Enrichment-Datum haben werden übersprungen.",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Geschätzte Zeit:** ~{max_searches * 5}s pro Kontakt\n\n"
    "DuckDuckGo hat Rate-Limits. Bei Fehlern: Suchtiefe reduzieren oder warten.\n\n"
    "**Hinweis:** Konstruierte E-Mails immer manuell prüfen!"
)

# --- File Input ---
st.markdown("### 📂 Kontaktliste")

input_mode = st.radio(
    "Datei laden",
    ["Standard-Pfad verwenden", "Datei hochladen"],
    horizontal=True,
)

file_path = None
uploaded_df = None

if input_mode == "Standard-Pfad verwenden":
    file_path = st.text_input("Excel-Pfad", value=DEFAULT_EXCEL)
    if file_path and os.path.exists(file_path):
        uploaded_df = pd.read_excel(file_path)
    elif file_path:
        st.warning(f"Datei nicht gefunden: {file_path}")
else:
    uploaded_file = st.file_uploader("Excel-Datei (.xlsx)", type=["xlsx"])
    if uploaded_file:
        uploaded_df = pd.read_excel(uploaded_file)
        file_path = uploaded_file.name

# --- Kontakte anzeigen + starten ---
if uploaded_df is not None:
    df = uploaded_df
    st.session_state.df = df

    # Kontakt-Übersicht
    name_col = find_column(df, NAME_COLS)
    firma_col = find_column(df, FIRMA_COLS)

    already_enriched = sum(1 for _, row in df.iterrows() if is_already_enriched(row))
    to_enrich = len(df) - already_enriched if skip_enriched else len(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Kontakte gesamt", len(df))
    col2.metric("Bereits angereichert", already_enriched)
    col3.metric("Noch zu enrichen", to_enrich)

    # Vorschau
    with st.expander("📋 Kontaktliste Vorschau", expanded=False):
        display_cols = [c for c in [name_col, firma_col, "Status", "Firma Stadt"] if c and c in df.columns]
        if display_cols:
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

    # --- START ---
    st.markdown("---")

    if to_enrich == 0:
        st.success("✅ Alle Kontakte sind bereits angereichert! Deaktiviere 'Bereits angereicherte überspringen' um sie erneut zu durchsuchen.")
    else:
        estimated_time = to_enrich * max_searches * 2
        st.info(
            f"**{to_enrich} Kontakte** werden mit **{max_searches} Suchen** pro Kontakt durchsucht. "
            f"Geschätzte Dauer: ~{estimated_time // 60} Min {estimated_time % 60} Sek."
        )

    if st.button(f"🚀 Alle {to_enrich} Kontakte anreichern", type="primary", disabled=(to_enrich == 0)):
        engine = EnrichmentEngine(
            api_key=api_key if api_key else None,
            hunter_api_key=hunter_api_key if hunter_api_key else None,
            llm_provider=llm_provider,
        )

        progress_bar = st.progress(0)
        status_container = st.container()

        with st.spinner("Enrichment läuft..."):
            results, skipped, errors = run_enrichment(
                df, engine, max_searches, skip_enriched, progress_bar, status_container,
            )

        # --- Zusammenfassung ---
        st.markdown("---")
        st.subheader("📊 Zusammenfassung")

        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
        res_col1.metric("Angereichert", len(results) - errors)
        res_col2.metric("Übersprungen", skipped)
        res_col3.metric("Fehler", errors)
        res_col4.metric("Gesamt", len(df))

        # --- Detail-Ergebnisse ---
        if results:
            with st.expander("🔎 Detail-Ergebnisse", expanded=True):
                for idx, result in results.items():
                    if "error" in result:
                        continue
                    row = df.iloc[idx]
                    name = get_cell_value(row, name_col)
                    st.markdown(f"#### {name}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**E-Mail:** {result.get('email') or '-'}")
                        st.markdown(f"**Status:** {result.get('email_status') or '-'}")
                        verif = result.get('email_verifizierung') or '-'
                        st.markdown(f"**SMTP-Verifizierung:** {verif}")
                        ref = result.get('referenz_email') or '-'
                        ref_q = result.get('referenz_email_quelle') or ''
                        st.markdown(f"**Referenz-Email:** {ref}" + (f" ([Quelle]({ref_q}))" if ref_q else ""))
                        st.markdown(f"**Pers. Telefon:** {result.get('personal_phone') or '-'}")
                        st.markdown(f"**Firmentelefon:** {result.get('company_phone') or '-'}")
                    with col_b:
                        st.markdown(f"**Konferenzen:** {result.get('conferences') or '-'}")
                        st.markdown(f"**Podcasts/Videos:** {result.get('podcasts_videos') or '-'}")
                        st.markdown(f"**Jobwechsel:** {result.get('job_changes') or '-'}")
                        st.markdown(f"**LinkedIn:** {result.get('linkedin_activity') or '-'}")

                    # KI-Zusammenfassung + Nachricht prominent anzeigen
                    zusammenfassung = result.get('zusammenfassung') or ''
                    nachricht = result.get('personalisierte_nachricht') or ''
                    kanal = result.get('kanal_empfehlung') or ''

                    if zusammenfassung:
                        st.markdown("**📋 KI-Zusammenfassung:**")
                        st.info(zusammenfassung)

                    if nachricht:
                        kanal_icon = "📧" if "EMAIL" in kanal.upper() else "💬"
                        kanal_label = "Email" if "EMAIL" in kanal.upper() else "LinkedIn"
                        st.markdown(f"**{kanal_icon} Personalisierte Nachricht ({kanal_label}):**")
                        st.success(nachricht)

                    if kanal:
                        st.markdown(f"**🎯 Kanal-Empfehlung:** {kanal}")

                    st.markdown("---")

        # --- Export ---
        st.subheader("💾 Speichern")

        output_name = f"kontakte_data_enriched_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        output_dir = DEFAULT_OUTPUT_DIR if os.path.isdir(DEFAULT_OUTPUT_DIR) else str(Path.home() / "Downloads")
        output_path = os.path.join(output_dir, output_name)

        output_path = st.text_input("Speicherpfad", value=output_path)

        if st.button("💾 Excel speichern", type="primary"):
            enriched_df = save_enriched_excel(df, results, output_path)
            st.success(f"✅ Gespeichert: `{output_path}`")
            st.balloons()

        # Download-Button
        buffer = BytesIO()
        temp_df = df.copy()
        for col_name in NEW_COLUMNS:
            if col_name not in temp_df.columns:
                temp_df[col_name] = ""
        key_to_col = {
            "email": "E-Mail", "email_status": "E-Mail Status",
            "email_verifizierung": "E-Mail Verifizierung",
            "referenz_email": "Referenz-Email", "referenz_email_quelle": "Referenz-Email Quelle",
            "personal_phone": "Persönliches Telefon", "company_phone": "Firmentelefon (Impressum)",
            "conferences": "Konferenzen (2025/2026)", "podcasts_videos": "Podcasts / Videos",
            "job_changes": "Jobwechsel / Karriere", "linkedin_activity": "LinkedIn-Aktivität",
            "birthday": "Geburtstag", "relevant_info": "Relevante Infos für Ansprache",
            "zusammenfassung": "KI-Zusammenfassung",
            "personalisierte_nachricht": "Personalisierte Nachricht",
            "kanal_empfehlung": "Kanal-Empfehlung (Email/LinkedIn)",
        }
        for idx, result in results.items():
            if "error" in result:
                continue
            for key, col_name in key_to_col.items():
                val = result.get(key, "")
                if val:
                    temp_df.at[idx, col_name] = val
            temp_df.at[idx, "Enrichment Datum"] = datetime.now().strftime("%Y-%m-%d")
        temp_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            label="📥 Download Excel",
            data=buffer,
            file_name=output_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

else:
    st.markdown("""
    ### So funktioniert's:
    1. **Excel laden** — Standard-Pfad oder Datei hochladen
    2. **Start klicken** — App geht automatisch ALLE Kontakte durch
    3. **Für jeden Kontakt wird gesucht nach:**
       - 📧 E-Mail-Adresse (verifiziert oder aus Firmenformat konstruiert)
       - 📞 Persönliches Telefon + Firmentelefon aus Impressum
       - 🎤 Konferenzen, Podcasts, YouTube-Videos
       - 💼 Jobwechsel, LinkedIn-Aktivität
       - 🎂 Geburtstag und relevante Infos für die Ansprache
    4. **Ergebnis** — Neue Excel-Datei mit allen Enrichment-Spalten
    """)
