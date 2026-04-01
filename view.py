import pandas as pd

from logger import get_logger

logger = get_logger(__name__)


def display_summary(summary: pd.DataFrame) -> None:
  
    logger.info("=== RÉSUMÉ DU PORTEFEUILLE ===")
    for _, row in summary.iterrows():
        logger.info("%s : %s", row["metric"], round(row["value"], 4))


def display_kpi_country(kpi_country: pd.DataFrame) -> None:

    logger.info("=== TOP 5 PAYS PAR EAD ===")
    for _, row in kpi_country.head(5).iterrows():
        logger.info(
            "%s — EAD: %s, PD moy: %s",
            row["country"],
            round(row["total_ead"], 0),
            round(row["avg_pd"], 4),
        )


def display_kpi_sector(kpi_sector: pd.DataFrame) -> None:

    logger.info("=== TOP 5 SECTEURS PAR EAD ===")
    for _, row in kpi_sector.head(5).iterrows():
        logger.info(
            "%s — EAD: %s, Watchlist: %s%%",
            row["sector"],
            round(row["total_ead"], 0),
            round(row["watchlist_rate"] * 100, 2),
        )