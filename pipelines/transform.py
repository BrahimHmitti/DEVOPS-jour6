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