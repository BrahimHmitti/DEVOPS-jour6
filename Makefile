# Makefile pour le Pipeline ETL

.PHONY: help setup generate extract transform quality load dashboard clean all

help:
	@echo "📋 Commandes disponibles :"
	@echo "  make setup       - Installer l'environnement Python"
	@echo "  make generate    - Générer le dataset"
	@echo "  make extract     - Extract → Bronze"
	@echo "  make transform   - Transform → Silver"
	@echo "  make quality     - Contrôles qualité"
	@echo "  make load        - Load → Gold"
	@echo "  make dashboard   - Lancer le dashboard Streamlit"
	@echo "  make all         - Exécuter tout le pipeline"
	@echo "  make clean       - Nettoyer les fichiers générés"

setup:
	@echo "🔧 Installation de l'environnement..."
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install duckdb pandas pyarrow streamlit matplotlib faker

generate:
	@echo "📊 Génération du dataset..."
	python tools/generate_data.py

extract:
	@echo "🔵 Extract → Bronze..."
	python pipelines/extract.py

transform:
	@echo "🟢 Transform → Silver..."
	python pipelines/transform.py

quality:
	@echo "✅ Contrôles qualité..."
	python pipelines/quality.py

load:
	@echo "🟡 Load → Gold..."
	python pipelines/load.py

dashboard:
	@echo "📊 Lancement du dashboard..."
	streamlit run apps/dashboard.py

all: generate extract transform quality load
	@echo "✨ Pipeline complet exécuté avec succès !"
	@echo ""
	@echo "📊 Pour voir le dashboard : make dashboard"
	@echo "📄 Voir le rapport qualité : cat quality_report.csv"
	@echo "📄 Voir le rapport d'analyse : cat REPORT.md"

clean:
	@echo "🧹 Nettoyage..."
	rm -f warehouse.duckdb
	rm -f quality_report.csv
	rm -rf dataset/*.csv
	rm -rf __pycache__
	rm -rf pipelines/__pycache__
	@echo "✅ Nettoyage terminé"
