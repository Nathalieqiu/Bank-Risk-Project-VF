import numpy as np
import pandas as pd
from pathlib import Path

# PARAMETRES

N_CLIENTS = 10000

# Fichier Final
OUTPUT_FILE = Path("/Users/nathalyqiu/Desktop/data/raw/bank_database.xlsx")

# (optionnel) 
SEED = 42

# GENERATION DES DONNEES

rng = np.random.default_rng(SEED)

countries = ["France", "Germany", "Italy", "Spain", "Belgium", "Netherlands"]
sectors = ["Industry", "Services", "Retail", "Energy", "Tech", "RealEstate"]
ratings = ["AAA", "AA", "A", "BBB", "BB", "B"]

# ----- TABLE CLIENTS -----
clients = pd.DataFrame()
clients["client_id"] = [f"C{i:05d}" for i in range(1, N_CLIENTS + 1)]
clients["country"] = rng.choice(countries, size=N_CLIENTS)
clients["sector"] = rng.choice(sectors, size=N_CLIENTS)
clients["rating"] = rng.choice(ratings, size=N_CLIENTS, p=[0.03, 0.07, 0.20, 0.35, 0.25, 0.10])

# ----- TABLE EXPOSURES -----
# EAD : distribution réaliste très étalée
ead = rng.lognormal(mean=12.0, sigma=0.8, size=N_CLIENTS)
ead = np.clip(ead, 10000, 15000000)

# Montant du prêt : 
ratio_loan = rng.uniform(0.6, 1.0, size=N_CLIENTS)
loan_amount = ead * ratio_loan

# PD et LGD
pd_values = rng.beta(a=1.5, b=50, size=N_CLIENTS) * 0.25
pd_values = np.clip(pd_values, 0.0001, 0.20)

lgd_values = rng.beta(a=2.0, b=2.5, size=N_CLIENTS)
lgd_values = np.clip(lgd_values, 0.10, 0.90)

exposures = pd.DataFrame()
exposures["client_id"] = clients["client_id"]
exposures["loan_amount"] = loan_amount.round(2)
exposures["ead"] = ead.round(2)
exposures["pd"] = pd_values.round(6)
exposures["lgd"] = lgd_values.round(4)

# ----- TABLE COLLATERALS -----
n_lines = rng.integers(0, 4, size=N_CLIENTS)  # 0,1,2,3
client_ids = np.repeat(clients["client_id"].values, n_lines)

collateral_value = rng.lognormal(mean=10.5, sigma=0.7, size=len(client_ids))
collateral_value = np.clip(collateral_value, 5000, 5000000)

collaterals = pd.DataFrame()
collaterals["client_id"] = client_ids
collaterals["collateral_value"] = collateral_value.round(2)

# EXPORT EXCEL 

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    clients.to_excel(writer, sheet_name="clients", index=False)
    exposures.to_excel(writer, sheet_name="exposures", index=False)
    collaterals.to_excel(writer, sheet_name="collaterals", index=False)

print("Fichier Excel généré :", OUTPUT_FILE)
print("Clients :", len(clients))
print("Exposures :", len(exposures))
print("Collaterals lines :", len(collaterals))
