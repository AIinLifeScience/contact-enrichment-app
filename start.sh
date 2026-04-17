#!/bin/bash
# Contact Enrichment App starten
# Einfach doppelklicken oder im Terminal ausführen: ./start.sh

cd "$(dirname "$0")"
echo "🔍 Starte Contact Enrichment App..."
echo "   Die App öffnet sich gleich im Browser."
echo "   (Lokal gebunden an 127.0.0.1 — nicht im Netzwerk erreichbar.)"
echo ""
# --server.address=127.0.0.1  → App ist nur lokal erreichbar (nicht im WLAN)
# --server.headless=true      → öffnet Browser sauber, ohne Email-Prompt
streamlit run app.py \
    --server.port 8501 \
    --server.address 127.0.0.1 \
    --server.headless true
