#!/bin/bash
# Contact Enrichment App starten
# Einfach doppelklicken oder im Terminal ausführen: ./start.sh

cd "$(dirname "$0")"
echo "🔍 Starte Contact Enrichment App..."
echo "   Die App öffnet sich gleich im Browser."
echo ""
streamlit run app.py --server.port 8501
