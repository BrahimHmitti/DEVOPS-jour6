import duckdb

con = duckdb.connect("warehouse.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS silver;")

print("=== TRANSFORMATION BRONZE → SILVER ===\n")

print("1. Nettoyage customers...")
con.execute("""
    CREATE OR REPLACE TABLE silver.customers AS
    SELECT 
        customer_id,
        name,
        LOWER(TRIM(email)) AS email,
        UPPER(TRIM(country)) AS country
    FROM bronze.customers
""")

print("   Pays après normalisation :")
countries = con.execute("""
    SELECT country, COUNT(*) as nb
    FROM silver.customers
    GROUP BY country
    ORDER BY nb DESC
""").fetchall()
for country, nb in countries:
    print(f"     {country}: {nb} clients")

print("\n2. Nettoyage orders...")
con.execute("""
    CREATE OR REPLACE TABLE silver.orders AS
    SELECT DISTINCT
        order_id,
        customer_id,
        CASE 
            WHEN date LIKE '%/%' THEN CAST(strptime(date, '%d/%m/%Y') AS DATE)
            WHEN LENGTH(date) = 8 THEN CAST(strptime(date, '%Y%m%d') AS DATE)
            ELSE CAST(date AS DATE)
        END AS order_date,
        CASE 
            WHEN LOWER(currency) = 'usd' THEN amount * 0.9
            ELSE amount
        END AS amount_eur
    FROM bronze.orders
    WHERE order_id IS NOT NULL
""")

print("\n=== STATISTIQUES SILVER.ORDERS ===")
stats = con.execute("""
    SELECT 
        COUNT(*) as total_orders,
        MIN(order_date) as first_order,
        MAX(order_date) as last_order,
        ROUND(SUM(amount_eur), 2) as total_revenue_eur
    FROM silver.orders
""").fetchone()

print(f"  Total commandes : {stats[0]}")
print(f"  Première commande : {stats[1]}")
print(f"  Dernière commande : {stats[2]}")
print(f"  CA total : {stats[3]:,.2f}€")

nb_bronze = con.execute("SELECT COUNT(*) FROM bronze.orders").fetchone()[0]
nb_silver = con.execute("SELECT COUNT(*) FROM silver.orders").fetchone()[0]
duplicates = nb_bronze - nb_silver
print(f"\n✓ {duplicates} doublons supprimés ({duplicates/nb_bronze*100:.1f}%)")

con.close()
print("\n✅ Transform → silver done")
