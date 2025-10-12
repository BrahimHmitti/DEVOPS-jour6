# Rapport d'Analyse - Data Quality

**Projet** : Pipeline ETL Bronze → Silver → Gold  
**Date** : 12 octobre 2025  
**Auteur** : Brahim Hmitti

---

## 1. Synthèse des Métriques de Qualité

| Dimension | Score | Statut | Priorité | Impact Métier |
|-----------|-------|--------|----------|---------------|
| Complétude (email) | 100% | ✅ Excellent | - | Aucun |
| Unicité (order_id) | ~97% | ⚠️ À améliorer | **P1** | Surévaluation du CA |
| Cohérence (FK) | 100% | ✅ Excellent | - | Aucun |
| Validité (country) | 100% | ✅ Excellent | - | Aucun |
| Exactitude (amount) | 100% | ✅ Excellent | - | Aucun |
| Fraîcheur (< 30j) | ~75% | ⚠️ À améliorer | **P2** | Dashboards obsolètes |

**Score global** : ~95% (5/6 métriques à 100%)

---

## 2. Analyse Détaillée et Remédiations

### 🔴 P1 : Unicité des order_id (~97%)

#### Problème Rencontré
- **Symptôme** : 3% des commandes sont dupliquées (même order_id apparaît 2 fois)
- **Cause Racine** : 
  - Le système source insère parfois 2 fois la même commande
  - Absence de contrainte UNIQUE sur order_id dans la base source
  - Possible race condition lors de la création des commandes

#### Impact Métier
- **Financier** : Surévaluation du CA (comptage double des commandes dupliquées)
- **Analytique** : Fausses statistiques sur le nombre réel de commandes
- **Opérationnel** : Risque de facturation double du client
- **Estimation** : ~3% d'erreur sur le CA = potentiellement plusieurs milliers d'euros par an

#### Solution Immédiate (Déjà Implémentée)
```sql
-- Dans transform.py : déduplication dans la couche Silver
CREATE OR REPLACE TABLE silver.orders AS
SELECT DISTINCT 
    order_id,
    customer_id,
    order_date,
    amount_eur
FROM bronze.orders;
```

✅ **Avantage** : Nettoie les données pour l'analyse  
⚠️ **Limite** : Ne corrige pas le problème à la source

#### Solution Long Terme
1. **À la source (Recommandation prioritaire)** :
   ```sql
   -- Ajouter une contrainte UNIQUE dans la base de production
   ALTER TABLE orders ADD CONSTRAINT uk_order_id UNIQUE (order_id);
   ```

2. **Monitoring proactif** :
   ```python
   # Alerte si doublons détectés en Bronze
   duplicates = con.execute("""
       SELECT order_id, COUNT(*) as nb
       FROM bronze.orders
       GROUP BY order_id
       HAVING COUNT(*) > 1
   """).fetchall()
   
   if duplicates:
       send_alert(f"⚠️ {len(duplicates)} order_id dupliqués détectés !")
   ```

3. **Data Contract** :
   - Documenter la règle métier : "1 order_id = 1 commande unique"
   - Imposer la validation avant insertion
   - SLA avec l'équipe source : 0 doublon toléré

#### Effort et Priorité
- **Effort** : 2 jours (1j dev + 1j coordination avec équipe source)
- **Priorité** : **P1** (impact financier direct)
- **ROI** : Élevé (évite pertes financières + améliore confiance dans les données)

---

### 🟠 P2 : Fraîcheur des données (~75%)

#### Problème Rencontré
- **Symptôme** : 25% des commandes datent de plus de 30 jours
- **Cause Racine** :
  - Le dataset généré couvre 40 jours (par design pour l'exercice)
  - Dans un contexte réel : pipeline non automatisé ou exécuté manuellement
  - Pas de refresh quotidien des données

#### Impact Métier
- **Décisionnel** : Les dashboards ne reflètent pas la situation actuelle
- **Réactivité** : Impossible de détecter rapidement les tendances récentes
- **Business** : Décisions basées sur des données obsolètes (risque stratégique)

#### Solution : Automatisation du Pipeline

##### Option 1 : Cron (Solution Simple)
```bash
# Éditer le crontab
crontab -e

# Ajouter l'exécution quotidienne à 6h du matin
0 6 * * * cd /path/to/DEVOPS-jour6 && /path/to/.venv/bin/python pipelines/extract.py && /path/to/.venv/bin/python pipelines/transform.py && /path/to/.venv/bin/python pipelines/load.py && /path/to/.venv/bin/python pipelines/quality.py
```

✅ **Avantages** : Simple, rapide à mettre en place  
❌ **Inconvénients** : Pas de gestion d'erreurs, pas de retry, pas de visibilité

##### Option 2 : Airflow (Solution Robuste) - Recommandée
```python
# dags/etl_pipeline.py
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 1),
    'email': ['alert@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'etl_bronze_silver_gold',
    default_args=default_args,
    description='Pipeline ETL quotidien',
    schedule_interval='@daily',  # Exécution quotidienne
    catchup=False
)

extract = BashOperator(
    task_id='extract_to_bronze',
    bash_command='cd /path/to/DEVOPS-jour6 && python pipelines/extract.py',
    dag=dag
)

transform = BashOperator(
    task_id='transform_to_silver',
    bash_command='cd /path/to/DEVOPS-jour6 && python pipelines/transform.py',
    dag=dag
)

quality = BashOperator(
    task_id='quality_checks',
    bash_command='cd /path/to/DEVOPS-jour6 && python pipelines/quality.py',
    dag=dag
)

load = BashOperator(
    task_id='load_to_gold',
    bash_command='cd /path/to/DEVOPS-jour6 && python pipelines/load.py',
    dag=dag
)

# Définir les dépendances
extract >> transform >> quality >> load
```

✅ **Avantages** : 
- Gestion d'erreurs et retry automatique
- Interface web pour monitoring
- Logs centralisés
- Alertes email en cas d'échec
- Rejeu facile en cas de problème

#### Effort et Priorité
- **Effort** : 
  - Cron : 1 heure
  - Airflow : 3 jours (installation + configuration + tests)
- **Priorité** : **P2** (améliore la qualité décisionnelle)
- **ROI** : Moyen à long terme (gain de temps + fiabilité)

---

### 🟢 P3 : Amélioration - Taux de Change Dynamique

#### Problème Actuel
- **Situation** : Taux de change fixe utilisé (1 USD = 0.9 EUR)
- **Impact** : Imprécision du CA en EUR (±5% selon les fluctuations)
- **Priorité** : P3 (amélioration qualité, pas bloquant)

#### Solution : Intégration API Taux de Change
```python
# Dans transform.py - Version améliorée
import requests
from datetime import datetime

def get_exchange_rate(date, from_currency='USD', to_currency='EUR'):
    """Récupère le taux de change réel pour une date donnée"""
    # API gratuite : https://api.exchangerate.host/
    response = requests.get(
        f"https://api.exchangerate.host/{date}",
        params={'base': from_currency, 'symbols': to_currency}
    )
    data = response.json()
    return data['rates'][to_currency]

# Appliquer le taux dynamique
con.execute("""
    CREATE OR REPLACE TABLE silver.orders AS
    SELECT 
        order_id,
        customer_id,
        order_date,
        CASE 
            WHEN currency = 'USD' THEN amount * get_udf_exchange_rate(order_date, 'USD', 'EUR')
            ELSE amount
        END AS amount_eur
    FROM bronze.orders
""")
```

#### Effort et Priorité
- **Effort** : 5 jours (intégration API + gestion cache + tests)
- **Priorité** : **P3** (nice-to-have)
- **ROI** : Faible à court terme, élevé si multi-devises devient critique

---

## 3. Plan d'Action Priorisé

### Court Terme (1-2 semaines)
1. ✅ **P1** : Éliminer les doublons à la source
   - Coordonner avec l'équipe backend
   - Ajouter contrainte UNIQUE sur order_id
   - Implémenter monitoring des doublons

2. ✅ **P2** : Automatiser le pipeline
   - Déployer cron ou Airflow
   - Configurer les alertes
   - Tester le refresh quotidien

### Moyen Terme (1-3 mois)
3. 🔄 Monitoring continu de la qualité
   - Dashboard temps réel des 6 métriques
   - Alertes si score < 95%
   - Rapports hebdomadaires automatiques

4. 🔄 Tests unitaires et intégration
   ```python
   # tests/test_transform.py
   def test_country_normalization():
       assert normalize_country("fr ") == "FR"
       assert normalize_country("us") == "US"
   
   def test_no_duplicates_in_silver():
       duplicates = get_duplicate_order_ids("silver.orders")
       assert len(duplicates) == 0
   ```

### Long Terme (6+ mois)
5. 🚀 Migration vers Data Warehouse Cloud
   - Snowflake ou BigQuery pour scalabilité
   - Séparation compute/storage
   - Coûts optimisés

6. 🤖 Machine Learning pour anomalies
   - Détection automatique d'anomalies (montants aberrants, pics suspects)
   - Alertes prédictives

7. 📋 Data Contracts avec les équipes sources
   - Schémas validés (Great Expectations)
   - SLAs de qualité
   - Validation avant ingestion

---

## 4. Métriques de Succès

| Objectif | Métrique Actuelle | Cible Q1 2026 |
|----------|-------------------|---------------|
| Unicité order_id | 97% | **100%** |
| Fraîcheur données | 75% | **95%+** |
| Score global qualité | 95% | **98%+** |
| Temps d'exécution pipeline | Manuel | **< 10 min automatisé** |
| Taux d'échec pipeline | N/A | **< 1%** |

---

## 5. Coûts et Bénéfices

### Investissement Total Estimé
- **P1 (Doublons)** : 2 jours × 500€/j = **1 000€**
- **P2 (Automatisation)** : 3 jours × 500€/j = **1 500€**
- **P3 (Taux change)** : 5 jours × 500€/j = **2 500€**

**Total** : **5 000€** pour atteindre 100% de qualité

### Bénéfices Attendus
- **Financiers** : Élimination des erreurs de CA (~3% = 10K€+/an économisés)
- **Temps** : Automatisation = 2h/jour économisées = 40K€/an
- **Qualité décisionnelle** : Données fiables → meilleures décisions stratégiques

**ROI** : Rentabilisé en **1 mois**

---

## 6. Conclusion

Le pipeline ETL fonctionne correctement avec **un score de qualité de 95%**. Les 2 axes d'amélioration prioritaires sont :

1. **P1 - Éliminer les doublons** : Impact financier direct, quick win
2. **P2 - Automatiser le refresh** : Améliore la fraîcheur et la fiabilité

Avec un investissement de **10 jours de développement**, nous pouvons atteindre **100% de qualité** et un **pipeline fully automatisé**.

---

**Recommandation finale** : Lancer les travaux P1 et P2 immédiatement. P3 peut être décalé au Q2 2026 selon les priorités métier.
