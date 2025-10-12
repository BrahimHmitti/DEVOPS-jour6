#!/bin/bash
# Script pour lancer le dashboard Streamlit

echo "LANCEMENT DU DASHBOARD : ....................... "

echo ""

# Vérifier que le venv est activé
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "  Le venv n'est pas activé."
    echo "Exécutez d'abord : source .venv/bin/activate"
    exit 1
fi

# Vérifier que les données existent
if [ ! -f "warehouse.duckdb" ]; then
    echo " warehouse.duckdb n'existe pas."
    echo ""
    echo "Exécutez d'abord le pipeline complet :"
    echo "   ./run_all.sh"
    exit 1
fi

if [ ! -f "quality_report.csv" ]; then
    echo "  quality_report.csv manquant. Génération..."
    python pipelines/quality.py
fi

echo " Le dashboard sera accessible sur : http://localhost:8501"
echo "  Appuyez sur Ctrl+C pour arrêter le serveur."
echo ""

# Lancer Streamlit (compatible Windows/Linux)
python -m streamlit run apps/dashboard.py
