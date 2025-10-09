

## 2. Extract → Bronze

### Pourquoi

#Bronze = données brutes telles qu’ingérées. On ne jette rien, on trace tout.  ￼

### Comment

#Créez `pipelines/extract.py` :


import duckdb, pandas as pd, pathlib
con = duckdb.connect("warehouse.duckdb")

con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
con.execute("""CREATE TABLE IF NOT EXISTS bronze.customers (
    customer_id INTEGER,
    name VARCHAR,
    email VARCHAR,
    country VARCHAR);
""")

df_cutomers = pd.read_csv('../dataset/customers.csv')
#con.execute("INSERT INTO bronze.customers select * from df_cutomers ") #ici j'ai fait l'erreur de nepas commenter cette ligne 
#con.execute("truncate table bronze.customers;")#j'ai truncate une seule fois

df_orders = pd.read_csv('../dataset/orders.csv')
con.execute("CREATE TABLE IF NOT EXISTS bronze.orders AS select * from df_orders") #solution efficace pour eveter plusieurs insertions



print("-------------- fetchall -------------------------")

count_customers = con.execute("SELECT * FROM bronze.customers limit 2;").fetchall()
print(count_customers)

print(con.execute("SElect * FROM bronze.orders limit 2;").fetchall())

print(con.execute("SElect count(*) FROM bronze.orders;").fetchone())



print("-------------- fetchone -------------------------")
count_customers = con.execute("SELECT count(*) FROM bronze.customers;") #cela retourne l'adresse memoire du résultat
print(count_customers)


count_customers = con.execute("SELECT count(*) FROM bronze.customers;").fetchone() #to see the effect of the fetchone function.
print(count_customers)

count_customers = con.execute("SELECT count(*) FROM bronze.customers;").fetchone()[0]
print(count_customers)



print("Extract → bronze done")
