from helpers import (
    clean_data,
    compute_indicators,
    compute_kpis,
    generate_figures,
    merge_data,
)
from logger import get_logger
from repository import load_data, save_report

from view import display_summary, display_kpi_country, display_kpi_sector

logger = get_logger(__name__)


def run(config: dict) -> None:
  
    paths = config["paths"]
    thresholds = config["thresholds"]

    logger.info("=== Démarrage de l'analyse ===")

    # Chargement
    clients, exposures, collaterals = load_data(paths["input_excel"])

    # Nettoyage
    clients, exposures, collaterals = clean_data(clients, exposures, collaterals)

    # Fusion
    df = merge_data(clients, exposures, collaterals)

    # Indicateurs
    df = compute_indicators(df, thresholds)

    # KPIs
    kpi_country, kpi_sector, basel_summary, summary = compute_kpis(df)

    # Graphiques
    generate_figures(df, kpi_country, kpi_sector, paths["figures_dir"])

    # Export
    save_report(
        output_path=paths["output_excel"],
        df=df,
        kpi_country=kpi_country,
        kpi_sector=kpi_sector,
        basel_summary=basel_summary,
        summary=summary,
        figures_dir=paths["figures_dir"],
    )
    
    display_summary(summary)
    display_kpi_country(kpi_country)
    display_kpi_sector(kpi_sector)

    logger.info("=== Analyse terminée ===")

