# Dojo DevOps - Dojo Data — Pipeline ETL & Data Quality

## Consignes générales

- **Gardez une trace de vos actions** : créez une documentation en markdown dans ce dépôt, où vous notez les commandes utilisées, les erreurs rencontrées et comment vous les avez résolues.
- **Section "Apprentissages" obligatoire** : pour chaque difficulté, notez :
  - Problème rencontré (et pourquoi il est survenu)
  - Solution apportée (et pourquoi elle fonctionne)
  - Nouveau savoir (et pourquoi il est utile)

⸻

## 0. Préparer l’environnement

### Comment

- Python 3.11+ (venv), DuckDB (ou SQLite), pandas, pyarrow, streamlit (pour le mini-dashboard).
- faker pour la génération de données factices.

```bash
python -m venv .venv && source .venv/bin/activate
pip install duckdb pandas pyarrow streamlit matplotlib faker
```

### Vérifications

- python -c "import duckdb, pandas; print('ok')" affiche ok
- Le venv est activé (`which python` pointe vers .venv)

⸻

## 1. Générer le dataset d’exercice

### Pourquoi

On simule des sources hétérogènes pour illustrer Bronze→Silver→Gold et les problèmes de qualité courants. 

### Comment

Créez `tools/generate_data.py` avec l'exemple ci dessous:

```python
import csv, random, datetime, pathlib, itertools
from faker import Faker

fake = Faker()
root = pathlib.Path("dataset"); root.mkdir(exist_ok=True)

# Customers (CSV)
with open(root/"customers.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["customer_id","name","email","country"])
    for cid in range(1,501):
        name = fake.name()
        email = name.lower().replace(" ",".") + "@example.com"
        country = random.choice(["FR","FR","FR","DE","ES","us","fr ","DE "])  # volontairement bruité
        w.writerow([cid,name,email,country])

# Orders (CSV) - doublons & formats datés volontairement variés
start = datetime.date.today() - datetime.timedelta(days=40)
with open(root/"orders.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["order_id","customer_id","date","amount","currency"])
    oid = 1000
    for day in range(40):
        for _ in range(random.randint(5,25)):
            d = start + datetime.timedelta(days=day)
            date_str = random.choice([d.isoformat(), d.strftime("%d/%m/%Y"), d.strftime("%Y%m%d")])
            amount = round(random.uniform(5,250),2)
            currency = random.choice(["EUR","EUR","EUR","usd"])
            cid = random.randint(1,500)
            w.writerow([oid,cid,date_str,amount,currency])
            if random.random()<0.03:  # insère un doublon 3%
                w.writerow([oid,cid,date_str,amount,currency])
            oid+=1

print("Dataset generated in ./dataset")
```

Puis :

```bash
python tools/generate_data.py
```

### Vérifications

- dataset/customers.csv et dataset/orders.csv existent
- Les fichiers contiennent ~500 clients et plusieurs milliers de commandes

⸻

## 2. Extract → Bronze

### Pourquoi

Bronze = données brutes telles qu’ingérées. On ne jette rien, on trace tout.  ￼

### Comment

Créez `pipelines/extract.py` :

```python
import duckdb, pandas as pd, pathlib
con = duckdb.connect("warehouse.duckdb")

con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

# Ingestion CSV
# [...]
print("Extract → bronze done")
```

Exécutez :

```bash
python pipelines/extract.py
```

### Vérifications

- DuckDB warehouse.duckdb contient bronze.customers et bronze.orders

⸻

## 3. Transform & Normalize → Silver

### Pourquoi

Silver = tables nettoyées / conformes : types corrects, pays normalisés, dates parsées, doublons supprimés.  ￼

### Comment

Créez `pipelines/transform.py` :

```python
import duckdb
con = duckdb.connect("warehouse.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS silver;")

# Normalisation pays + lower/trim emails
# [...]

# Parsing de dates + currency to EUR (taux fixe 1 USD=0.9 EUR pour l'exercice)
# [...]

# Déduplication
# [...]

print("Transform → silver done")
```

### Vérifications

- silver.customers a des emails normalisés en lowercase@email.com
- silver.customers contient des "country" en FR/DE/ES/US
- silver.orders a order_date (type date) et amount_eur en euros
- Les doublons d’orders ont disparu

⸻

## 4. Data Quality checks (6 dimensions)

### Pourquoi

Mesurer la santé de la donnée : complétude, unicité, cohérence inter-sources, validité, exactitude, fraîcheur.  ￼

### Comment

Créez `pipelines/quality.py` :

```python
import duckdb, pandas as pd, datetime
con = duckdb.connect("warehouse.duckdb")
today = datetime.date.today()

metrics = {}

# Complétude (emails non nuls)
# metrics["customers_email_completeness"] = con.execute("""
#   SELECT ...

# Unicité (order_id unique)

# Cohérence (clé étrangère présente)

# Validité (countries autorisés)

# Exactitude (heuristique : montants > 0)

# Ponctualité (freshness <= 30j)

pd.Series(metrics).to_csv("quality_report.csv")
print("Wrote quality_report.csv")
```

### Vérifications

- quality_report.csv existe et contient 6 métriques
- Vous commentez dans le README ce que vous jugez P0/P1/P2 à corriger (et pourquoi)

⸻

## 5. Modèle & Load → Gold

### Pourquoi

Gold = tables métier prêtes pour l’analyse (ex : CA par jour).  ￼

### Comment

Créez `pipelines/load.py` :

```python
import duckdb
con = duckdb.connect("warehouse.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS gold;")

# CA journalier
print("Load → gold done")
```

### Vérifications

- gold.daily_revenue existe avec order_date, revenue_eur, orders


## 6. Visualisation & mini-dashboard

### Pourquoi

Le Data Analyst construit des visualisations pédagogiques et des dashboards pour différents publics.  ￼

### Comment

Créez `apps/dashboard.py` :

```python
import duckdb, pandas as pd, streamlit as st, matplotlib.pyplot as plt

con = duckdb.connect("warehouse.duckdb")
# [...]

# st.title("Daily Revenue")
# st.metric...

# pyplot

st.write("Top jours par CA")
st.dataframe(df.sort_values("revenue_eur", ascending=False).head(10))
```

Lancez :

```bash
streamlit run apps/dashboard.py
```

### Vérifications

- Un graphique CA journalier s’affiche
- Deux metrics s’affichent (nb jours, CA total)
- Un top 10 des jours par CA est visible

⸻

## 7. Orchestration (bonus)

### Pourquoi

Automatiser l’exécution récurrente des jobs évite l’intervention manuelle et les erreurs ; exemples : Airflow, Prefect, Dagster.  ￼

Comment

- Automatisez l’exécution des étapes via Airflow
  - Installer Airflow via helm dans le cluster minikube (cf. https://artifacthub.io/packages/helm/apache-airflow/airflow, attention aux images bitnami)
  - Créer un DAG qui exécute les étapes extract, transform, quality, load (cf. https://airflow.apache.org/docs/apache-airflow/stable/tutorial/fundamentals.html)

### Vérifications

- J'ai une pipeline Airflow qui exécute les étapes
- Chaque étape est un task séparé
- Les dépendances entre tâches sont correctes
- La pipeline s’exécute sans erreur
- Un log d’exécution est committé

⸻

8. Restitution & remédiations

### Pourquoi

Passer du constat (métriques) à des actions (remédiations) est le cœur du travail Data Engineer : qualité des sources, ingestion, transformations, performance & coûts.  ￼  ￼

### Comment

Dans REPORT.md, listez pour chaque métrique < 0.98 :

- Cause probable (source / ingestion / transform)  ￼
- Impact (métier) & priorité (P0→P4)
- Remédiation (ex : règles de normalisation, contraintes d’unicité, contrôles d’entrée)  ￼

### Vérifications

- REPORT.md contient au moins 3 remédiations argumentées
- Chaque remédiation a une priorité et un effort estimé

## Annexes utiles (rappels du cours)

- Rôles : DE = pipelines & qualité & dispo ; DA = dataviz/dashboards ; DS = modèles & expérimentation.  ￼
- ETL : extraire multi-sources, transformer (nettoyage/format), charger (DB/DWH).  ￼
- Batch vs Streaming : traitement en lots vs temps réel/near-real-time ; choix = contraintes métier.  ￼
- Orchestration : automatiser les workflows (Airflow/Prefect/Dagster).  ￼
- Qualité : 6 dimensions & contrôles (monitoring, data contracts, checks techniques & métier).  ￼

## Livrables à rendre

- Code : pipelines/*.py, apps/dashboard.py, Makefile (ou équivalent)
- Données : dataset/*.csv
- Sorties : quality_report.csv, REPORT.md
- Journal : LOG.md (commandes, erreurs, apprentissages)
(même philosophie que l’exemple DevSecOps)

## Objectifs pédagogiques

### Savoir

- [ ] Je sais quelles sont les responsabilité du Data Analyst
- [ ] Je sais ce qu’est un ETL
- [ ] Je sais quel est le rôle du Data engineer
- [ ] Je sais pourquoi il faut s’intéresser à la data quality
- [ ] Je sais citer les 6 principaux problèmes de la data quality
- [ ] Je sais expliquer la distinction Bronze Sliver Gold
- [ ] Je connais la différence entre DA DE et DS

### Savoir-faire

- [ ] Je sais Extract de la donnée csv
- [ ] Je sais transformer les colonnes de cette donnée
- [ ] Je sais normaliser cette donnée
- [ ] Je sais dédoublonner cette donnée
- [ ] Je sais insérer cette donnée transformée
- [ ] Je sais visualiser la donnée
- [ ] Je sais créer un dashboard qui m’informe d’une métrique métier de la donnée
- [ ] Je sais analyser les corrections à prendre pour rendre la donnée qualitative
