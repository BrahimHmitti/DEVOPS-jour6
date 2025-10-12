#!/bin/bash
# Script pour exécuter tout le pipeline ETL

set -e  # Arrêter en cas d'erreur

echo " LANCEMENT DU PIPELINE ETL COMPLET "

# Vérifier que le venv est activé
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Le venv n'est pas activé."
    echo "Exécutez d'abord : source .venv/bin/activate"
    exit 1
fi

# Étape 1: Génération des données
echo "📊 Étape 1/5 : Génération des données..."
python tools/generate_data.py
echo "✅ Données générées"
echo ""

# Étape 2: Extract → Bronze
echo "📥 Étape 2/5 : Extract → Bronze..."
python pipelines/extract.py
echo "✅ Données extraites vers Bronze"
echo ""

# Étape 3: Transform → Silver
echo "🔄 Étape 3/5 : Transform → Silver..."
python pipelines/transform.py
echo "✅ Données transformées vers Silver"
echo ""

# Étape 4: Quality checks
echo "✔️  Étape 4/5 : Calcul des métriques de qualité..."
python pipelines/quality.py
echo "✅ Rapport qualité généré"
echo ""

# Étape 5: Load → Gold
echo "💎 Étape 5/5 : Load → Gold..."
python pipelines/load.py
echo "✅ Données agrégées vers Gold"
echo ""

echo "PIPELINE TERMINÉ AVEC SUCCÈS╗"


echo " Fichiers générés :"
echo "   - warehouse.duckdb (base de données)"
echo "   - quality_report.csv (métriques qualité)"
echo ""
echo " Pour voir le dashboard :"
echo "   ./run_dashboard.sh"
echo ""
