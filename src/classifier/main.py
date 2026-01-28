"""
Main entry point for the classifier module.
"""

import argparse
import logging
import sys
from pathlib import Path

from src.common.config import ConfigLoader
from src.common.storage import StorageManager
from src.classifier.session_converter import SessionConverter
from src.classifier.annotator import Annotator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("classifier.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ClassifierApp:
    """
    Main application for the classifier module.
    Handles session conversion and annotation.
    """

    def __init__(self, config):
        """
        Initialize classifier application.

        Args:
            config: ClassifierConfig instance
        """
        self.config = config
        self.storage = StorageManager(
            raw_dir=config.input_dir, processed_dir=config.output_dir
        )
        self.converter = SessionConverter(
            input_dir=config.input_dir, output_dir=config.output_dir
        )

        logger.info("ClassifierApp initialized")

    def run(
        self, session_id: str, auto_convert: bool = True, force_convert: bool = False
    ) -> None:
        """
        Run the classifier for a specific session.

        Args:
            session_id: Session identifier
            auto_convert: Automatically convert session if not already processed
            force_convert: Force conversion even if already processed
        """
        logger.info(f"Running classifier for session: {session_id}")

        try:
            # Check if session exists
            if not self.storage.session_exists(session_id, processed=False):
                logger.error(f"Raw session not found: {session_id}")
                print(
                    f"Erreur: Session '{session_id}' introuvable dans {self.config.input_dir}"
                )
                return

            # Check if session is already converted
            db_path = self.storage.get_processed_session_path(session_id)

            if not db_path.exists() or force_convert:
                if auto_convert:
                    print(f"\nConversion de la session '{session_id}'...")
                    db_path = Path(
                        self.converter.convert_session(session_id, force=force_convert)
                    )
                    print(f"✓ Session convertie: {db_path}")
                else:
                    logger.error(f"Session not converted: {session_id}")
                    print(
                        f"Erreur: Session non convertie. Utilisez --convert pour la convertir."
                    )
                    return
            else:
                logger.info(f"Using existing processed session: {db_path}")

            # Start annotator
            print(f"\nLancement de l'annotateur...")
            annotator = Annotator(str(db_path))
            annotator.start()

        except Exception as e:
            logger.error(f"Error running classifier: {e}", exc_info=True)
            print(f"\nErreur: {e}")

    def list_sessions(self, show_all: bool = False) -> None:
        """
        List available sessions.

        Args:
            show_all: Show all sessions (raw and processed)
        """
        print("\n" + "=" * 70)
        print("SESSIONS DISPONIBLES")
        print("=" * 70)

        # Unconverted sessions
        unconverted = self.converter.list_unconverted_sessions()
        if unconverted:
            print(f"\nSessions brutes non converties ({len(unconverted)}):")
            for session_id in unconverted:
                print(f"  • {session_id}")

        # Processed sessions
        processed = self.storage.list_processed_sessions()
        if processed:
            print(f"\nSessions converties ({len(processed)}):")
            for session_id in processed:
                print(f"  • {session_id}")

        if not unconverted and not processed:
            print("\nAucune session trouvée.")

        print("=" * 70)

    def convert_all(self, force: bool = False) -> None:
        """
        Convert all unconverted sessions.

        Args:
            force: Force conversion even if already processed
        """
        print("\n" + "=" * 70)
        print("CONVERSION DE SESSIONS")
        print("=" * 70)

        converted = self.converter.convert_all_sessions(force=force)

        print(f"\n✓ {len(converted)} session(s) convertie(s)")
        print("=" * 70)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Classifier - Annotation de sessions audio"
    )

    parser.add_argument("session_id", nargs="?", help="ID de la session à classifier")

    parser.add_argument(
        "--input-dir",
        default="data/raw",
        help="Répertoire des sessions brutes (défaut: data/raw)",
    )

    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Répertoire des sessions traitées (défaut: data/processed)",
    )

    parser.add_argument(
        "--list", action="store_true", help="Lister toutes les sessions disponibles"
    )

    parser.add_argument(
        "--convert-all",
        action="store_true",
        help="Convertir toutes les sessions non converties",
    )

    parser.add_argument(
        "--force-convert",
        action="store_true",
        help="Forcer la conversion même si déjà traitée",
    )

    parser.add_argument(
        "--no-auto-convert",
        action="store_true",
        help="Ne pas convertir automatiquement les sessions",
    )

    parser.add_argument("--config", help="Chemin vers le fichier de configuration YAML")

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Load configuration
    config = ConfigLoader.load_classifier_config(
        config_file=args.config, input_dir=args.input_dir, output_dir=args.output_dir
    )

    # Create app
    app = ClassifierApp(config)

    # Handle commands
    if args.list:
        app.list_sessions()
        return

    if args.convert_all:
        app.convert_all(force=args.force_convert)
        return

    if args.session_id:
        app.run(
            session_id=args.session_id,
            auto_convert=not args.no_auto_convert,
            force_convert=args.force_convert,
        )
    else:
        # No session specified, show help
        print("Erreur: Veuillez spécifier un ID de session ou utiliser --list")
        print("\nExemples:")
        print("  python -m src.classifier.main --list")
        print("  python -m src.classifier.main session_2026-01-28_14-30-00")
        print("  python -m src.classifier.main --convert-all")


if __name__ == "__main__":
    main()
