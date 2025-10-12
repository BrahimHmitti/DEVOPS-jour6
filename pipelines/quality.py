import duckdb, pandas as pd, datetime

con = duckdb.connect("warehouse.duckdb")
today = datetime.date.today()

print("=== CONTRÔLES QUALITÉ (6 DIMENSIONS) ===\n")

metrics = {}

# 1. COMPLÉTUDE : % emails non nuls
print("1. Complétude...")
total = con.execute("SELECT COUNT(*) FROM silver.customers").fetchone()[0]
non_null = con.execute("SELECT COUNT(email) FROM silver.customers WHERE email IS NOT NULL AND email != ''").fetchone()[0]
metrics["completeness_email"] = non_null / total if total > 0 else 0
print(f"   Email complétude : {metrics['completeness_email']:.2%}")

# 2. UNICITÉ : % order_id uniques
print("2. Unicité...")
total_orders = con.execute("SELECT COUNT(*) FROM silver.orders").fetchone()[0]
unique_orders = con.execute("SELECT COUNT(DISTINCT order_id) FROM silver.orders").fetchone()[0]
metrics["uniqueness_order_id"] = unique_orders / total_orders if total_orders > 0 else 0
print(f"   Order ID unicité : {metrics['uniqueness_order_id']:.2%}")

# 3. COHÉRENCE : % commandes avec customer_id valide (clé étrangère)
print("3. Cohérence...")
total_orders = con.execute("SELECT COUNT(*) FROM silver.orders").fetchone()[0]
valid_fk = con.execute("""
    SELECT COUNT(*) FROM silver.orders o
    WHERE EXISTS (SELECT 1 FROM silver.customers c WHERE c.customer_id = o.customer_id)
""").fetchone()[0]
metrics["consistency_fk"] = valid_fk / total_orders if total_orders > 0 else 0
print(f"   Clés étrangères valides : {metrics['consistency_fk']:.2%}")

# 4. VALIDITÉ : % pays dans la liste autorisée [FR, DE, ES, US]
print("4. Validité...")
total_customers = con.execute("SELECT COUNT(*) FROM silver.customers").fetchone()[0]
valid_countries = con.execute("""
    SELECT COUNT(*) FROM silver.customers 
    WHERE country IN ('FR', 'DE', 'ES', 'US')
""").fetchone()[0]
metrics["validity_country"] = valid_countries / total_customers if total_customers > 0 else 0
print(f"   Pays valides : {metrics['validity_country']:.2%}")

# 5. EXACTITUDE : % montants > 0
print("5. Exactitude...")
total_orders = con.execute("SELECT COUNT(*) FROM silver.orders").fetchone()[0]
positive_amounts = con.execute("SELECT COUNT(*) FROM silver.orders WHERE amount_eur > 0").fetchone()[0]
metrics["accuracy_amount"] = positive_amounts / total_orders if total_orders > 0 else 0
print(f"   Montants > 0 : {metrics['accuracy_amount']:.2%}")

# 6. FRAÎCHEUR : % commandes < 30 jours
print("6. Fraîcheur...")
total_orders = con.execute("SELECT COUNT(*) FROM silver.orders").fetchone()[0]
recent_orders = con.execute(f"""
    SELECT COUNT(*) FROM silver.orders 
    WHERE order_date >= DATE '{today}' - INTERVAL '30 days'
""").fetchone()[0]
metrics["freshness_30d"] = recent_orders / total_orders if total_orders > 0 else 0
print(f"   Données < 30j : {metrics['freshness_30d']:.2%}")

# Sauvegarder le rapport
df_metrics = pd.Series(metrics)
df_metrics.to_csv("quality_report.csv", header=["score"])
print(f"\n✅ Rapport sauvegardé dans quality_report.csv")

# Résumé
print("\n=== RÉSUMÉ QUALITÉ ===")
for metric, score in metrics.items():
    status = "✅" if score >= 0.98 else "⚠️" if score >= 0.90 else "❌"
    print(f"{status} {metric}: {score:.2%}")

# Score global
avg_score = sum(metrics.values()) / len(metrics)
print(f"\n📊 Score global de qualité : {avg_score:.2%}")

con.close()
