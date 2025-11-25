import duckdb
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import subprocess
import os
import sys

# Configuration
st.set_page_config(page_title="Dashboard Data Quality", layout="wide")

# Header avec branding
col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("### 👨‍💻")
with col2:
    st.title("📊 Dashboard - Pipeline ETL & Data Quality")
    st.markdown("**Brahim Hmitti** - Data Engineer | [GitHub](https://github.com/BrahimHmitti/DEVOPS-jour6)")

# Générer les données automatiquement si la DB n'existe pas (pour Streamlit Cloud)
@st.cache_resource
def initialize_database():
    if not os.path.exists("warehouse.duckdb"):
        with st.spinner("🔄 Initialisation de la base de données..."):
            try:
                # Ajouter le dossier racine au path
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
                # Générer les données
                subprocess.run(["python", "tools/generate_data.py"], check=True)
                subprocess.run(["python", "pipelines/extract.py"], check=True)
                subprocess.run(["python", "pipelines/transform.py"], check=True)
                subprocess.run(["python", "pipelines/quality.py"], check=True)
                subprocess.run(["python", "pipelines/load.py"], check=True)
                
                st.success("✅ Base de données initialisée avec succès !")
            except Exception as e:
                st.error(f"❌ Erreur lors de l'initialisation : {e}")
                st.stop()
    return True

# Initialiser la DB
initialize_database()

# Connexion DuckDB (en lecture seule pour éviter les conflits)
con = duckdb.connect("warehouse.duckdb", read_only=True)

# === SECTION 1 : KPIs ===
st.header("🎯 KPIs Globaux")

col1, col2, col3, col4 = st.columns(4)

with col1:
    nb_customers = con.execute("SELECT COUNT(*) FROM silver.customers").fetchone()[0]
    st.metric("👥 Clients", f"{nb_customers:,}")

with col2:
    nb_orders = con.execute("SELECT COUNT(*) FROM silver.orders").fetchone()[0]
    st.metric("🛒 Commandes", f"{nb_orders:,}")

with col3:
    total_revenue = con.execute("SELECT SUM(revenue_eur) FROM gold.daily_revenue").fetchone()[0]
    st.metric("💰 CA Total", f"{total_revenue:,.0f}€")

with col4:
    avg_order = con.execute("SELECT ROUND(AVG(amount_eur), 2) FROM silver.orders").fetchone()[0]
    st.metric("📈 Panier Moyen", f"{avg_order:.2f}€")

# === SECTION 2 : Qualité des données ===
st.header("🔍 Qualité des Données")

try:
    # Charger le rapport qualité
    quality_df = pd.read_csv("quality_report.csv", index_col=0)
    quality_df.columns = ["Score"]
    quality_df["Score %"] = (quality_df["Score"] * 100).round(2)
    
    # Afficher le tableau
    st.dataframe(
        quality_df.style.background_gradient(cmap="RdYlGn", subset=["Score"]),
        use_container_width=True
    )
    
    # Score global
    avg_score = quality_df["Score"].mean()
    st.metric("📊 Score Global de Qualité", f"{avg_score:.2%}")
    
except FileNotFoundError:
    st.warning("⚠️ Fichier quality_report.csv non trouvé. Exécutez d'abord: `python pipelines/quality.py`")

# === SECTION 3 : Chiffre d'affaires journalier ===
st.header("📈 Chiffre d'Affaires Journalier")

# Charger les données
df_revenue = con.execute("""
    SELECT order_date, revenue_eur, orders_count, avg_order_value
    FROM gold.daily_revenue
    ORDER BY order_date
""").df()

if not df_revenue.empty:
    # Graphique
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df_revenue['order_date'], df_revenue['revenue_eur'], marker='o', linewidth=2, color='steelblue')
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("CA (€)", fontsize=12)
    ax.set_title("Évolution du Chiffre d'Affaires", fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    
    # Statistiques
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_revenue = df_revenue['revenue_eur'].mean()
        st.metric("📊 CA moyen/jour", f"{avg_revenue:,.2f}€")
    
    with col2:
        max_revenue_day = df_revenue.loc[df_revenue['revenue_eur'].idxmax()]
        st.metric(
            "🏆 Meilleur jour", 
            f"{max_revenue_day['revenue_eur']:,.2f}€",
            delta=f"{max_revenue_day['order_date']}"
        )
    
    with col3:
        total_days = len(df_revenue)
        st.metric("📅 Jours de données", f"{total_days}")

# === SECTION 4 : Top jours ===
st.header("🏅 Top 10 Jours par CA")

top10 = df_revenue.sort_values('revenue_eur', ascending=False).head(10)
st.dataframe(
    top10[['order_date', 'revenue_eur', 'orders_count', 'avg_order_value']].style.format({
        'revenue_eur': '{:,.2f}€',
        'orders_count': '{:,}',
        'avg_order_value': '{:.2f}€'
    }),
    use_container_width=True
)

# === SECTION 5 : Répartition par pays ===
st.header("🌍 Répartition des Clients par Pays")

df_countries = con.execute("""
    SELECT country, COUNT(*) as nb_customers
    FROM silver.customers
    GROUP BY country
    ORDER BY nb_customers DESC
""").df()

col1, col2 = st.columns([2, 1])

with col1:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(df_countries['country'], df_countries['nb_customers'], color='steelblue')
    ax.set_xlabel("Pays", fontsize=12)
    ax.set_ylabel("Nombre de clients", fontsize=12)
    ax.set_title("Clients par Pays", fontsize=14, fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.dataframe(
        df_countries.style.format({'nb_customers': '{:,}'}),
        use_container_width=True
    )

# === SECTION 6 : Distribution des commandes ===
st.header("📦 Distribution des Montants de Commandes")

df_amounts = con.execute("""
    SELECT amount_eur
    FROM silver.orders
    WHERE amount_eur > 0
""").df()

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(df_amounts['amount_eur'], bins=30, color='lightcoral', edgecolor='black')
ax.set_xlabel("Montant (€)", fontsize=12)
ax.set_ylabel("Fréquence", fontsize=12)
ax.set_title("Distribution des Montants de Commandes", fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
st.pyplot(fig)

con.close()

# Footer
st.markdown("---")
st.markdown("**Pipeline ETL** : Bronze → Silver → Gold | **Data Quality** : 6 dimensions")
