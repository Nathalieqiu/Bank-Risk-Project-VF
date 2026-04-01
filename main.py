from app import run
from logger import get_logger
from new import generate_data
from repository import load_config

logger = get_logger(__name__)


def main() -> None:
  
    config = load_config("config.json")

    # Génération des données si nécessaire
    generate_data(config, config["paths"]["input_excel"])

    # Lancement de l'analyse
    run(config)


if __name__ == "__main__":
    main()


