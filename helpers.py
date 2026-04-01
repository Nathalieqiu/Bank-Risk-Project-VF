from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from logger import get_logger

logger = get_logger(__name__)


def clean_data(
    clients: pd.DataFrame,
    exposures: pd.DataFrame,
    collaterals: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    
    clients = clients.dropna(subset=["client_id"]).copy()
    clients["client_id"] = clients["client_id"].astype(str).str.strip()
    clients["country"] = clients["country"].astype(str).str.strip()
    clients["sector"] = clients["sector"].astype(str).str.strip()
    clients["rating"] = clients["rating"].astype(str).str.strip().str.upper()

    exposures = exposures.dropna(
        subset=["client_id", "loan_amount", "ead", "pd", "lgd"]
    ).copy()
    exposures["client_id"] = exposures["client_id"].astype(str).str.strip()

    for col in ["loan_amount", "ead", "pd", "lgd"]:
        exposures[col] = pd.to_numeric(exposures[col], errors="coerce")

    exposures = exposures.dropna(subset=["loan_amount", "ead", "pd", "lgd"])
    exposures = exposures[(exposures["loan_amount"] > 0) & (exposures["ead"] > 0)]
    exposures = exposures[exposures["pd"].between(0, 1)]
    exposures = exposures[exposures["lgd"].between(0, 1)]
    exposures = exposures[exposures["loan_amount"] <= exposures["ead"]]

    collaterals = collaterals.dropna(
        subset=["client_id", "collateral_value"]
    ).copy()
    collaterals["client_id"] = collaterals["client_id"].astype(str).str.strip()
    collaterals["collateral_value"] = pd.to_numeric(
        collaterals["collateral_value"], errors="coerce"
    )
    collaterals = collaterals.dropna(subset=["collateral_value"])
    collaterals = collaterals[collaterals["collateral_value"] >= 0]

    logger.info("Nettoyage terminé.")
    return clients, exposures, collaterals


def merge_data(
    clients: pd.DataFrame,
    exposures: pd.DataFrame,
    collaterals: pd.DataFrame,
) -> pd.DataFrame:
     
    df = exposures.merge(clients, on="client_id", how="left")

    coll_agg = collaterals.groupby("client_id", as_index=False).agg(
        total_collateral=("collateral_value", "sum"),
        collateral_lines=("collateral_value", "size"),
    )
    df = df.merge(coll_agg, on="client_id", how="left")
    df["total_collateral"] = df["total_collateral"].fillna(0.0)
    df["collateral_lines"] = df["collateral_lines"].fillna(0).astype(int)

    logger.info("Fusion terminée — %d lignes.", len(df))
    return df


def compute_indicators(df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
   
    pd_wl = thresholds["pd_watchlist"]
    rw = thresholds["rw_proxy"]
    cet1_rate = thresholds["cet1_rate_proxy"]
    basel_45 = thresholds["basel_cet1_min"]
    basel_8 = thresholds["basel_tier1_total"]
    basel_105 = thresholds["basel_cet1_buffer"]

    df["expected_loss"] = df["ead"] * df["pd"] * df["lgd"]
    df["loan_to_ead_ratio"] = df["loan_amount"] / df["ead"]
    df["watchlist_flag"] = (df["pd"] > pd_wl).astype(int)
    df["collateral_coverage"] = np.where(
        df["ead"] > 0, df["total_collateral"] / df["ead"], 0.0
    )

    df["rwa"] = df["ead"] * rw
    df["cet1_capital"] = df["ead"] * cet1_rate
    df["cet1_ratio"] = np.where(df["rwa"] > 0, df["cet1_capital"] / df["rwa"], 0.0)

    df["cet1_ok_4_5"] = df["cet1_ratio"] >= basel_45
    df["cet1_ok_8"] = df["cet1_ratio"] >= basel_8
    df["cet1_ok_10_5"] = df["cet1_ratio"] >= basel_105

    logger.info("Indicateurs calculés.")
    return df


def compute_kpis(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
     
    agg_fields = {
        "n_clients": ("client_id", "count"),
        "total_loan": ("loan_amount", "sum"),
        "total_ead": ("ead", "sum"),
        "avg_pd": ("pd", "mean"),
        "total_el": ("expected_loss", "sum"),
        "watchlist_rate": ("watchlist_flag", "mean"),
        "avg_collateral_coverage": ("collateral_coverage", "mean"),
        "avg_loan_to_ead": ("loan_to_ead_ratio", "mean"),
    }

    kpi_country = (
        df.groupby("country", dropna=False)
        .agg(**agg_fields)
        .reset_index()
        .sort_values("total_ead", ascending=False)
    )

    kpi_sector = (
        df.groupby("sector", dropna=False)
        .agg(**agg_fields)
        .reset_index()
        .sort_values("total_ead", ascending=False)
    )

    basel_summary = pd.DataFrame({
        "threshold": ["CET1 >= 4.5%", "CET1 >= 8%", "CET1 >= 10.5%"],
        "clients_compliant": [
            int(df["cet1_ok_4_5"].sum()),
            int(df["cet1_ok_8"].sum()),
            int(df["cet1_ok_10_5"].sum()),
        ],
        "compliance_rate_%": [
            float(df["cet1_ok_4_5"].mean() * 100),
            float(df["cet1_ok_8"].mean() * 100),
            float(df["cet1_ok_10_5"].mean() * 100),
        ],
    })

    ead_total = df["ead"].sum()
    weighted_pd = (
        (df["pd"] * df["ead"]).sum() / ead_total if ead_total > 0 else 0.0
    )

    summary = pd.DataFrame({
        "metric": [
            "Number of clients",
            "Total loan amount",
            "Total EAD",
            "EAD-weighted PD",
            "Total expected loss",
            "WatchList rate",
            "Average collateral coverage",
        ],
        "value": [
            len(df),
            df["loan_amount"].sum(),
            ead_total,
            weighted_pd,
            df["expected_loss"].sum(),
            df["watchlist_flag"].mean(),
            df["collateral_coverage"].mean(),
        ],
    })

    logger.info("KPIs calculés.")
    return kpi_country, kpi_sector, basel_summary, summary


def generate_figures(
    df: pd.DataFrame,
    kpi_country: pd.DataFrame,
    kpi_sector: pd.DataFrame,
    figures_dir: str,
) -> None:
    
    fig_dir = Path(figures_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)

    plt.figure()
    sns.histplot(df["pd"], bins=40, kde=True)
    plt.title("PD Distribution")
    plt.tight_layout()
    plt.savefig(fig_dir / "pd_distribution.png")
    plt.close()

    plt.figure()
    sns.barplot(data=kpi_country.head(10), x="country", y="total_ead")
    plt.title("Total EAD by Country (Top 10)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(fig_dir / "ead_by_country.png")
    plt.close()

    plt.figure()
    sns.barplot(data=kpi_sector.head(10), x="sector", y="watchlist_rate")
    plt.title("WatchList Rate by Sector (Top 10 by EAD)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(fig_dir / "watchlist_by_sector.png")
    plt.close()
    
    plt.figure()
    sns.countplot(data=df, x="rating", order=["AAA", "AA", "A", "BBB", "BB", "B"])
    plt.title("Number of Clients by Rating")
    plt.xlabel("Rating")
    plt.ylabel("Number of Clients")
    plt.tight_layout()
    plt.savefig(fig_dir / "clients_by_rating.png")
    plt.close()

    logger.info("Graphiques générés dans %s", fig_dir)

