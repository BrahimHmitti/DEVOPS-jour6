import duckdb

con = duckdb.connect("warehouse.duckdb")

# Créer le schéma gold
con.execute("CREATE SCHEMA IF NOT EXISTS gold;")

print("=== AGRÉGATIONS MÉTIER (SILVER → GOLD) ===\n")

# Table métier : CA journalier
print("1. Création gold.daily_revenue...")
con.execute("""
    CREATE OR REPLACE TABLE gold.daily_revenue AS
    SELECT 
        order_date,
        ROUND(SUM(amount_eur), 2) AS revenue_eur,
        COUNT(*) AS orders_count,
        ROUND(AVG(amount_eur), 2) AS avg_order_value
    FROM silver.orders
    GROUP BY order_date
    ORDER BY order_date DESC
""")

# Vérifications
nb_days = con.execute("SELECT COUNT(*) FROM gold.daily_revenue").fetchone()[0]
print(f"   ✓ {nb_days} jours de données")

total_revenue = con.execute("SELECT SUM(revenue_eur) FROM gold.daily_revenue").fetchone()[0]
total_orders = con.execute("SELECT SUM(orders_count) FROM gold.daily_revenue").fetchone()[0]
print(f"   ✓ CA total : {total_revenue:,.2f}€")
print(f"   ✓ Total commandes : {total_orders:,}")

# Aperçu des meilleurs jours
print("\n=== TOP 5 JOURS PAR CA ===")
top5 = con.execute("""
    SELECT order_date, revenue_eur, orders_count, avg_order_value
    FROM gold.daily_revenue
    ORDER BY revenue_eur DESC
    LIMIT 5
""").fetchall()

for date, revenue, count, avg in top5:
    print(f"  {date} : {revenue:>10,.2f}€ ({count:>3} commandes, avg: {avg:>6,.2f}€)")

# Statistiques globales
print("\n=== STATISTIQUES GLOBALES ===")
stats = con.execute("""
    SELECT 
        MIN(revenue_eur) as min_revenue,
        MAX(revenue_eur) as max_revenue,
        ROUND(AVG(revenue_eur), 2) as avg_revenue,
        ROUND(STDDEV(revenue_eur), 2) as stddev_revenue
    FROM gold.daily_revenue
""").fetchone()

print(f"  CA min/jour : {stats[0]:,.2f}€")
print(f"  CA max/jour : {stats[1]:,.2f}€")
print(f"  CA moyen/jour : {stats[2]:,.2f}€")
print(f"  Écart-type : {stats[3]:,.2f}€")

con.close()
print("\n✅ Load → gold done")
