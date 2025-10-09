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