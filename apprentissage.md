# Journal d'Apprentissage - TP Data Engineering# Journal des Apprentissages - TP Data Engineering



## Étape 0 : Préparation de l'environnement## Étape 0 : Setup Environnement






**Commande :****Nouveau savoir** : 

```bash- Bronze = données brutes SANS transformation

python tools/generate_data.py- Les problèmes de qualité sont normaux en Bronze

```- La transformation se fait dans Silver



**Résultat :** J'ai obtenu `dataset/customers.csv` (500 lignes) et `dataset/orders.csv` (646 lignes).**Pourquoi c'est utile** : Architecture Bronze→Silver→Gold sépare les responsabilités et permet l'auditabilité.



**Nouveau savoir :** Faker permet de créer des données réalistes pour tester les pipelines ETL.---



**Pourquoi utile :** Je peux reproduire des problèmes de qualité courants (doublons, formats variés, casse incohérente).## Étape 2 : Extract → Bronze



### Problème rencontré

### Problème rencontréInsertions multiples dans `bronze.customers` (doublons à chaque exécution)

J'ai d'abord utilisé `INSERT INTO` et j'ai eu des doublons après plusieurs exécutions.

**Pourquoi** : Utilisation de `INSERT INTO` sans vider la table avant

**Pourquoi :** Chaque exécution ajoutait les données au lieu de les remplacer.

**Solution** :

**Solution :** J'ai utilisé `CREATE OR REPLACE TABLE` :```python

```python# ❌ MAUVAIS

con.execute("CREATE OR REPLACE TABLE bronze.customers AS SELECT * FROM df_customers")con.execute("INSERT INTO bronze.customers SELECT * FROM df_customers")

```# Ajoute à chaque fois → doublons



**Nouveau savoir :** L'idempotence est cruciale dans les pipelines ETL. `CREATE OR REPLACE` garantit qu'on peut relancer le script sans créer de doublons.# ✅ BON

con.execute("CREATE OR REPLACE TABLE bronze.customers AS SELECT * FROM df_customers")

**Pourquoi utile :** Je peux debugger et relancer mon pipeline autant de fois que nécessaire sans corrompre les données.# Remplace la table complètement → idempotent

```

---

**Nouveau savoir** : 

## Étape 3 : Transform → Silver- `CREATE OR REPLACE` rend le script **idempotent** (même résultat peu importe le nombre d'exécutions)

- Essentiel pour les pipelines automatisés

### Ce que j'ai fait

J'ai créé `pipelines/transform.py` pour nettoyer les données :**Pourquoi c'est utile** : Les pipelines doivent être rejouables sans effets de bord.



1. **Normalisation des pays** : `UPPER(TRIM(country))` → "fr " devient "FR"---

2. **Parsing des dates** : 3 formats différents parsés avec `CASE WHEN`

3. **Conversion devise** : USD → EUR avec taux fixe 0.9### Problème rencontré

4. **Déduplication** : `SELECT DISTINCT` sur les colonnes métierConfusion entre `.execute()`, `.fetchone()` et `.fetchall()`



**Commande :****Pourquoi** : Incompréhension du fonctionnement des curseurs DuckDB

```bash

python pipelines/transform.py**Solution** :

``````python

# con.execute() retourne un CURSEUR, pas les données

**Résultat :** cursor = con.execute("SELECT COUNT(*) FROM bronze.customers")

- `silver.customers` : 500 clients avec pays normalisés (FR, DE, ES, US)print(cursor)  # <DuckDBPyConnection object at 0x...>

- `silver.orders` : 628 commandes (18 doublons supprimés = 2.8%)

- CA total : 78,682.66 EUR# .fetchone() récupère UNE ligne sous forme de TUPLE

result = cursor.fetchone()

---print(result)  # (500,)



### Problème rencontré# [0] extrait la valeur du tuple

J'ai eu des erreurs avec les dates car il y avait 3 formats :count = cursor.fetchone()[0]

- ISO : "2025-09-28"print(count)  # 500

- Français : "28/09/2025"

- Compact : "20250928"# .fetchall() récupère TOUTES les lignes sous forme de LISTE de TUPLES

rows = con.execute("SELECT * FROM bronze.customers LIMIT 3").fetchall()

**Pourquoi :** DuckDB ne peut pas parser automatiquement plusieurs formats.print(rows)  # [(1, 'John', ...), (2, 'Jane', ...), (3, 'Bob', ...)]

```

**Solution :** J'ai utilisé `strptime()` avec un `CASE WHEN` :

```sql**Nouveau savoir** :

CASE- `con.execute(sql)` → retourne un curseur (pointeur vers résultats)

  WHEN date LIKE '%/%' THEN strptime(date, '%d/%m/%Y')- `.fetchone()` → récupère 1 ligne (tuple)

  WHEN LENGTH(date) = 8 THEN strptime(date, '%Y%m%d')- `.fetchall()` → récupère toutes les lignes (liste de tuples)

  ELSE strptime(date, '%Y-%m-%d')- `.df()` → récupère en DataFrame pandas

END AS order_date

```**Pourquoi c'est utile** : Comprendre les curseurs évite les erreurs et permet de choisir la bonne méthode selon le besoin (performance, mémoire).



**Nouveau savoir :** DuckDB supporte `strptime()` pour parser des dates avec formats personnalisés.---



**Pourquoi utile :** Je peux gérer des sources de données hétérogènes.## Étape 3 : Transform → Silver



---### Problème rencontré

Formats de dates hétérogènes : `2024-10-09`, `09/10/2024`, `20241009`

## Étape 4 : Data Quality

**Pourquoi** : Les sources utilisent des formats différents (ISO, français, compact)

### Ce que j'ai fait

J'ai créé `pipelines/quality.py` pour calculer 6 métriques de qualité :**Solution** :

```sql

1. **Complétude** : % emails non NULL → 100%CASE 

2. **Unicité** : % order_id uniques → 100%    WHEN date LIKE '%/%' THEN CAST(strptime(date, '%d/%m/%Y') AS DATE)

3. **Cohérence** : % customer_id valides → 100%    WHEN LENGTH(date) = 8 THEN CAST(strptime(date, '%Y%m%d') AS DATE)

4. **Validité** : % pays autorisés (FR/DE/ES/US) → 100%    ELSE CAST(date AS DATE)

5. **Exactitude** : % montants > 0 → 100%END AS order_date

6. **Fraîcheur** : % commandes < 30j → 80.73%```



**Commande :****Nouveau savoir** :

```bash- `strptime()` parse une chaîne selon un format

python pipelines/quality.py- `%d/%m/%Y` = jour/mois/année

```- `%Y%m%d` = année mois jour

- `CASE WHEN` permet de gérer plusieurs formats

**Résultat :** J'ai généré `quality_report.csv` avec un score global de **96.79%**.

**Pourquoi c'est utile** : Les données réelles ont souvent des formats inconsistants. Il faut savoir les normaliser.

**Nouveau savoir :** Les 6 dimensions de data quality permettent d'évaluer systématiquement la santé des données.

---

**Pourquoi utile :** Je peux identifier précisément quels aspects nécessitent des améliorations.

### Problème rencontré

---Pays avec espaces et casse différente : `"fr "`, `"FR"`, `"us"`, `"DE "`



## Étape 5 : Load → Gold**Pourquoi** : Erreurs de saisie, manque de validation à la source



### Ce que j'ai fait**Solution** :

J'ai créé `pipelines/load.py` pour agréger le CA journalier :```sql

```pythonUPPER(TRIM(country)) AS country

con.execute("""-- "fr " → "FR"

  CREATE OR REPLACE TABLE gold.daily_revenue AS-- "us" → "US"

  SELECT -- "DE " → "DE"

    order_date,```

    SUM(amount_eur) AS revenue_eur,

    COUNT(*) AS orders_count,**Nouveau savoir** :

    AVG(amount_eur) AS avg_order_value- `TRIM()` supprime les espaces avant/après

  FROM silver.orders- `UPPER()` met en majuscules

  GROUP BY order_date- Chaîner les fonctions : `UPPER(TRIM(x))`

  ORDER BY order_date

""")**Pourquoi c'est utile** : Normalisation essentielle pour les jointures et agrégations (sinon "FR" ≠ "fr ").

```

---

**Commande :**

```bash### Problème rencontré

python pipelines/load.pyDoublons dans les commandes (3% des lignes)

```

**Pourquoi** : Bug dans le système source qui insère parfois 2 fois la même commande

**Résultat :** J'ai créé `gold.daily_revenue` avec 40 jours de données agrégées.

**Solution** :

**Nouveau savoir :** La couche Gold contient des données prêtes pour l'analyse métier (agrégations, KPIs).```sql

CREATE OR REPLACE TABLE silver.orders AS

**Pourquoi utile :** Les analystes peuvent requêter directement les tables Gold sans refaire les calculs.SELECT DISTINCT  -- Dédupliquer

    order_id,

---    customer_id,

    order_date,

## Étape 6 : Dashboard Streamlit    amount_eur

FROM bronze.orders

### Ce que j'ai fait```

J'ai créé `apps/dashboard.py` avec :

- 4 KPIs (CA total, nb commandes, panier moyen, nb jours)**Nouveau savoir** :

- Graphique du CA journalier (matplotlib)- `SELECT DISTINCT` élimine les doublons

- Répartition par pays (bar chart)- Dans Silver, on nettoie les données (déduplication incluse)

- Table des métriques qualité- Bronze conserve TOUT (y compris les doublons pour auditabilité)



**Commande :****Pourquoi c'est utile** : La déduplication en Silver évite les erreurs d'analyse (surévaluation du CA).

```bash

streamlit run apps/dashboard.py---

```

## Étape 4 : Data Quality

**Résultat :** Dashboard accessible sur http://localhost:8501

### Problème rencontré

**Nouveau savoir :** Streamlit permet de créer rapidement des dashboards interactifs en Python.Comment mesurer la qualité des données de façon objective ?



**Pourquoi utile :** Je peux visualiser les données sans écrire de HTML/CSS/JavaScript.**Pourquoi** : Besoin de métriques quantifiables pour piloter les améliorations



---**Solution** : Implémenter les 6 dimensions de qualité :



### Problème rencontré1. **Complétude** : % valeurs non nulles

J'ai essayé `./run_dashboard.sh` mais j'ai eu :2. **Unicité** : % valeurs uniques

```bash3. **Cohérence** : % clés étrangères valides

streamlit: command not found4. **Validité** : % valeurs dans liste autorisée

```5. **Exactitude** : % valeurs dans plage attendue

6. **Fraîcheur** : % données récentes

**Pourquoi :** Sur Windows (WSL), Streamlit s'installe comme `streamlit.cmd`, pas comme exécutable Unix.

**Nouveau savoir** : 

**Solution :** J'ai modifié le script pour utiliser :- La qualité n'est pas binaire (bon/mauvais) mais mesurable en %

```bash- Chaque dimension a son importance selon le contexte métier

python -m streamlit run apps/dashboard.py- Un score global aide à prioriser les actions

```

**Pourquoi c'est utile** : Sans mesure, impossible d'améliorer. Les métriques permettent de suivre les progrès.

**Nouveau savoir :** `python -m <module>` est portable entre Windows/Linux/macOS.

---

**Pourquoi utile :** Mes scripts fonctionnent sur tous les environnements sans modification.

### Problème rencontré

---Score de fraîcheur faible (~75%)



## Étape 8 : Rapport et Remédiations**Pourquoi** : Dataset généré couvre 40 jours, donc 25% des données ont > 30 jours



### Ce que j'ai fait**Solution** : Automatiser le refresh quotidien (cron ou Airflow)

J'ai analysé les 6 métriques et identifié les problèmes dans `REPORT.md` :

**Nouveau savoir** :

**3 remédiations prioritaires :**- La fraîcheur dépend de la fréquence de refresh du pipeline

- Un pipeline manuel = données qui vieillissent

1. **P1 - Déduplication automatique** (2 jours)- Automatisation = fraîcheur garantie

   - Ajouter contrainte `UNIQUE(order_id)` en Bronze

   - Éliminer 18 doublons (2.8%)**Pourquoi c'est utile** : Les décisions se prennent sur des données fraîches. L'automatisation est indispensable.



2. **P2 - Automatisation pipeline** (3 jours)---

   - Implémenter Airflow DAG

   - Monitoring avec alertes## Étape 5 : Load → Gold



3. **P3 - Taux de change dynamique** (5 jours)### Problème rencontré

   - API externe pour USD/EURComment créer des tables métier utiles pour l'analyse ?

   - Améliorer l'exactitude des montants

**Pourquoi** : Silver contient des données atomiques, Gold doit contenir des agrégations prêtes à l'emploi

**Nouveau savoir :** Prioriser les remédiations par impact métier et effort technique.

**Solution** :

**Pourquoi utile :** Je peux argumenter mes décisions techniques auprès des stakeholders.```sql

CREATE OR REPLACE TABLE gold.daily_revenue AS

---SELECT 

    order_date,

## Debugging Final    ROUND(SUM(amount_eur), 2) AS revenue_eur,

    COUNT(*) AS orders_count,

### Problème rencontré    ROUND(AVG(amount_eur), 2) AS avg_order_value

Les tests DuckDB échouaient avec :FROM silver.orders

```GROUP BY order_date

Table with name SCHEMAS does not exist!ORDER BY order_date DESC

``````



**Pourquoi :** `SHOW SCHEMAS` n'est pas supporté par DuckDB 1.4.1.**Nouveau savoir** :

- Gold = agrégations pré-calculées (SUM, COUNT, AVG)

**Solution :** J'ai utilisé la norme ANSI SQL :- Performance : requête instantanée sur Gold vs calcul à la volée sur Silver

```sql- Dénormalisation acceptable en Gold (optimisation lecture)

SELECT schema_name FROM information_schema.schemata WHERE schema_name='bronze'

```**Pourquoi c'est utile** : Les dashboards interrogent Gold (rapide) plutôt que Silver (lent pour agrégations).



**Nouveau savoir :** `information_schema` est standard et fonctionne sur tous les SGBD (PostgreSQL, MySQL, DuckDB, SQLite 3.37+).---



**Pourquoi utile :** Mon code est portable entre différentes bases de données.## Étape 6 : Dashboard Streamlit



---### Problème rencontré

Comment créer un dashboard interactif rapidement ?

## Concepts Clés Compris

**Pourquoi** : Besoin de visualiser les KPIs et métriques qualité

### Architecture Medallion (Bronze → Silver → Gold)

**Solution** : Utiliser Streamlit

- **Bronze** : Données brutes, pas de transformation, tout est conservé (auditabilité)```python

- **Silver** : Données nettoyées, normalisées, dédupliquées (qualité)import streamlit as st

- **Gold** : Agrégations métier, prêtes pour l'analyse (performance)

st.title("📊 Dashboard")

**Pourquoi important :** Séparation des responsabilités et traçabilité des transformations.st.metric("CA Total", f"{total_revenue:,.0f}€")

st.dataframe(df)

---st.pyplot(fig)

```
