from pathlib import Path

import numpy as np
import pandas as pd

from logger import get_logger

logger = get_logger(__name__)


def generate_data(config: dict, output_path: str) -> None:
    
    gen = config["generation"]
    n_clients: int = gen["n_clients"]
    seed: int = gen["seed"]
    countries: list = gen["countries"]
    sectors: list = gen["sectors"]
    ratings: list = gen["ratings"]
    rating_probs: list = gen["rating_probabilities"]

    rng = np.random.default_rng(seed)

    # Table clients
    clients = pd.DataFrame()
    clients["client_id"] = [f"C{i:05d}" for i in range(1, n_clients + 1)]
    clients["country"] = rng.choice(countries, size=n_clients)
    clients["sector"] = rng.choice(sectors, size=n_clients)
    clients["rating"] = rng.choice(ratings, size=n_clients, p=rating_probs)

    # Table exposures
    ead = rng.lognormal(mean=12.0, sigma=0.8, size=n_clients)
    ead = np.clip(ead, 10000, 15000000)

    ratio_loan = rng.uniform(0.6, 1.0, size=n_clients)
    loan_amount = ead * ratio_loan

    pd_values = rng.beta(a=1.5, b=50, size=n_clients) * 0.25
    pd_values = np.clip(pd_values, 0.0001, 0.20)

    lgd_values = rng.beta(a=2.0, b=2.5, size=n_clients)
    lgd_values = np.clip(lgd_values, 0.10, 0.90)

    exposures = pd.DataFrame()
    exposures["client_id"] = clients["client_id"]
    exposures["loan_amount"] = loan_amount.round(2)
    exposures["ead"] = ead.round(2)
    exposures["pd"] = pd_values.round(6)
    exposures["lgd"] = lgd_values.round(4)

    # Table collaterals
    n_lines = rng.integers(0, 4, size=n_clients)
    client_ids = np.repeat(clients["client_id"].values, n_lines)

    collateral_value = rng.lognormal(mean=10.5, sigma=0.7, size=len(client_ids))
    collateral_value = np.clip(collateral_value, 5000, 5000000)

    collaterals = pd.DataFrame()
    collaterals["client_id"] = client_ids
    collaterals["collateral_value"] = collateral_value.round(2)

    # Export
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        clients.to_excel(writer, sheet_name="clients", index=False)
        exposures.to_excel(writer, sheet_name="exposures", index=False)
        collaterals.to_excel(writer, sheet_name="collaterals", index=False)

    logger.info(
        "Données générées — clients: %d, collaterals: %d → %s",
        len(clients),
        len(collaterals),
        path,
    )
