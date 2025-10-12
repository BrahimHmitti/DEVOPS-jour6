import duckdb
import pandas as pd

con = duckdb.connect("warehouse.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

print("=== EXTRACT → BRONZE ===\n")
print("1. Chargement des CSV...")

df_customers = pd.read_csv('dataset/customers.csv')
df_orders = pd.read_csv('dataset/orders.csv')

print(f"   ✓ {len(df_customers)} customers lus")
print(f"   ✓ {len(df_orders)} orders lus")

print("\n2. Insertion dans Bronze...")

con.execute("CREATE OR REPLACE TABLE bronze.customers AS SELECT * FROM df_customers")
con.execute("CREATE OR REPLACE TABLE bronze.orders AS SELECT * FROM df_orders")

print("\n=== VÉRIFICATIONS ===")

nb_customers = con.execute("SELECT COUNT(*) FROM bronze.customers").fetchone()[0]
nb_orders = con.execute("SELECT COUNT(*) FROM bronze.orders").fetchone()[0]

print(f"✓ {nb_customers} customers dans bronze.customers")
print(f"✓ {nb_orders} orders dans bronze.orders")

print("\n--- Aperçu bronze.customers (3 premières lignes) ---")
sample_customers = con.execute("SELECT * FROM bronze.customers LIMIT 3").fetchall()
for row in sample_customers:
    print(f"  {row}")

print("\n--- Aperçu bronze.orders (3 premières lignes) ---")
sample_orders = con.execute("SELECT * FROM bronze.orders LIMIT 3").fetchall()
for row in sample_orders:
    print(f"  {row}")

print("\n--- Problèmes détectés (normal en Bronze) ---")
countries = con.execute("SELECT DISTINCT country FROM bronze.customers ORDER BY country").fetchall()
print(f"Pays (avec espaces/casse) : {[c[0] for c in countries]}")

date_samples = con.execute("SELECT DISTINCT date FROM bronze.orders LIMIT 5").fetchall()
print(f"Formats de dates variés : {[d[0] for d in date_samples]}")

con.close()
print("\n Extract → bronze done")
