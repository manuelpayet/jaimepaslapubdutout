"""
Interactive console annotator for classifying audio blocks.
"""

import sqlite3
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class Annotator:
    """
    Interactive console interface for annotating audio blocks.
    Low CPU usage, keyboard-driven interface.
    """

    # Available categories
    CATEGORIES = {
        "1": "A classifier",
        "2": "Publicité",
        "3": "Radio",
        "4": "Impossible à classifier",
    }

    def __init__(self, session_db_path: str):
        """
        Initialize annotator.

        Args:
            session_db_path: Path to processed session database
        """
        self.db_path = Path(session_db_path)

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {session_db_path}")

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        # Current state
        self.current_block_number = 0
        self.total_blocks = self._get_total_blocks()
        self.session_id = self._get_session_id()

        logger.info(f"Annotator initialized for session: {self.session_id}")

    def start(self) -> None:
        """
        Start the interactive annotation interface.
        """
        logger.info("Starting annotation interface")

        try:
            self._show_welcome()

            # Find first unannotated block
            self.current_block_number = self._find_first_unannotated()

            if self.current_block_number is None:
                print("\n✓ All blocks have been annotated!")
                return

            # Main loop
            while True:
                self._clear_screen()
                self._display_block(self.current_block_number)

                # Get user input
                command = input("\nCommande: ").strip().lower()

                if not self._handle_command(command):
                    break

            self._show_summary()

        except KeyboardInterrupt:
            print("\n\nAnnotation interrupted by user")
        finally:
            self.conn.close()
            logger.info("Annotation session ended")

    def _handle_command(self, command: str) -> bool:
        """
        Handle user command.

        Args:
            command: User input

        Returns:
            True to continue, False to quit
        """
        # Category selection
        if command in self.CATEGORIES:
            category = self.CATEGORIES[command]
            self._classify_block(self.current_block_number, category)
            self._next_block()
            return True

        # Navigation
        elif command in ["n", "next", "s", "suivant"]:
            self._next_block()
            return True

        elif command in ["p", "prev", "previous", "precedent"]:
            self._previous_block()
            return True

        elif command.startswith("g"):
            # Go to specific block: g42
            try:
                block_num = int(command[1:])
                self._go_to_block(block_num)
            except (ValueError, IndexError):
                print("Format invalide. Utilisez: g<numéro> (ex: g42)")
                input("Appuyez sur Entrée pour continuer...")
            return True

        # Notes
        elif command in ["note", "n"]:
            note = input("Note: ")
            self._add_note(self.current_block_number, note)
            return True

        # Help
        elif command in ["h", "help", "?"]:
            self._show_help()
            input("\nAppuyez sur Entrée pour continuer...")
            return True

        # Statistics
        elif command in ["stats", "stat"]:
            self._show_statistics()
            input("\nAppuyez sur Entrée pour continuer...")
            return True

        # Quit
        elif command in ["q", "quit", "exit"]:
            return False

        else:
            print(f"Commande inconnue: {command}")
            input("Appuyez sur Entrée pour continuer...")
            return True

    def _display_block(self, block_number: int) -> None:
        """
        Display current block information.

        Args:
            block_number: Block number to display
        """
        block = self._get_block(block_number)

        if not block:
            print(f"Bloc {block_number} non trouvé")
            return

        # Progress
        progress = self._get_progress()

        # Header
        print("╔" + "═" * 78 + "╗")
        print(f"║ Classifier - {self.session_id:^60} ║")
        print(
            f"║ Progression: {progress['annotated']}/{progress['total']} ({progress['percent']:.1f}%)".ljust(
                79
            )
            + "║"
        )
        print("╠" + "═" * 78 + "╣")

        # Block info
        print(f"║ Bloc #{block_number:04d} - {block['timestamp'][:19]}".ljust(79) + "║")
        print("║" + " " * 78 + "║")

        # Transcription
        print("║ Transcription:".ljust(79) + "║")
        transcription = block["transcription"] or "(vide)"
        lines = self._wrap_text(transcription, 76)
        for line in lines[:10]:  # Limit to 10 lines
            print(f"║ {line}".ljust(79) + "║")

        print("║" + " " * 78 + "║")

        # Current category
        current_category = block["category"]
        category_color = self._colorize_category(current_category)
        print(f"║ Catégorie actuelle: {category_color}".ljust(89) + "║")

        # Notes
        if block["notes"]:
            print(f"║ Note: {block['notes'][:70]}".ljust(79) + "║")

        print("╠" + "═" * 78 + "╣")

        # Categories
        print("║ Catégories:".ljust(79) + "║")
        for key, category in self.CATEGORIES.items():
            marker = "→" if category == current_category else " "
            print(f"║ {marker} [{key}] {category}".ljust(79) + "║")

        print("║" + " " * 78 + "║")

        # Commands
        print(
            "║ [N]ext | [P]rev | [G]oto | Note | [H]elp | [S]tats | [Q]uit".ljust(79)
            + "║"
        )
        print("╚" + "═" * 78 + "╝")

    def _classify_block(self, block_number: int, category: str) -> None:
        """
        Classify a block.

        Args:
            block_number: Block number
            category: Category to assign
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE blocks
            SET category = ?
            WHERE block_number = ?
        """,
            (category, block_number),
        )
        self.conn.commit()

        logger.debug(f"Block {block_number} classified as: {category}")

    def _add_note(self, block_number: int, note: str) -> None:
        """
        Add a note to a block.

        Args:
            block_number: Block number
            note: Note text
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE blocks
            SET notes = ?
            WHERE block_number = ?
        """,
            (note, block_number),
        )
        self.conn.commit()

        logger.debug(f"Note added to block {block_number}")

    def _get_block(self, block_number: int) -> Optional[sqlite3.Row]:
        """
        Get block from database.

        Args:
            block_number: Block number

        Returns:
            Block row or None
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM blocks WHERE block_number = ?
        """,
            (block_number,),
        )
        return cursor.fetchone()

    def _get_total_blocks(self) -> int:
        """Get total number of blocks."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM blocks")
        return cursor.fetchone()[0]

    def _get_session_id(self) -> str:
        """Get session ID from metadata."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key = 'session_id'")
        row = cursor.fetchone()
        return row[0] if row else "Unknown"

    def _find_first_unannotated(self) -> Optional[int]:
        """Find the first block that hasn't been annotated."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT block_number FROM blocks
            WHERE category = 'A classifier'
            ORDER BY block_number
            LIMIT 1
        """)
        row = cursor.fetchone()
        return row[0] if row else None

    def _next_block(self) -> None:
        """Move to next block."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT block_number FROM blocks
            WHERE block_number > ?
            ORDER BY block_number
            LIMIT 1
        """,
            (self.current_block_number,),
        )
        row = cursor.fetchone()

        if row:
            self.current_block_number = row[0]
        else:
            print("\nDernier bloc atteint!")
            input("Appuyez sur Entrée pour continuer...")

    def _previous_block(self) -> None:
        """Move to previous block."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT block_number FROM blocks
            WHERE block_number < ?
            ORDER BY block_number DESC
            LIMIT 1
        """,
            (self.current_block_number,),
        )
        row = cursor.fetchone()

        if row:
            self.current_block_number = row[0]
        else:
            print("\nPremier bloc atteint!")
            input("Appuyez sur Entrée pour continuer...")

    def _go_to_block(self, block_number: int) -> None:
        """Go to specific block."""
        if 0 <= block_number < self.total_blocks:
            self.current_block_number = block_number
        else:
            print(f"Bloc invalide. Valeurs acceptées: 0 à {self.total_blocks - 1}")
            input("Appuyez sur Entrée pour continuer...")

    def _get_progress(self) -> Dict[str, any]:
        """Get annotation progress."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM blocks WHERE category != 'A classifier'
        """)
        annotated = cursor.fetchone()[0]

        return {
            "annotated": annotated,
            "total": self.total_blocks,
            "percent": (annotated / self.total_blocks * 100)
            if self.total_blocks > 0
            else 0,
        }

    def _show_statistics(self) -> None:
        """Show annotation statistics."""
        cursor = self.conn.cursor()

        print("\n" + "=" * 60)
        print("STATISTIQUES D'ANNOTATION")
        print("=" * 60)

        for category in [
            "A classifier",
            "Publicité",
            "Radio",
            "Impossible à classifier",
        ]:
            cursor.execute(
                """
                SELECT COUNT(*) FROM blocks WHERE category = ?
            """,
                (category,),
            )
            count = cursor.fetchone()[0]
            percent = (count / self.total_blocks * 100) if self.total_blocks > 0 else 0
            print(f"{category:20s}: {count:4d} ({percent:5.1f}%)")

        print("=" * 60)
        print(f"{'TOTAL':20s}: {self.total_blocks:4d}")
        print("=" * 60)

    def _show_help(self) -> None:
        """Show help message."""
        print("\n" + "=" * 60)
        print("AIDE - COMMANDES DISPONIBLES")
        print("=" * 60)
        print("\nCatégories:")
        for key, category in self.CATEGORIES.items():
            print(f"  {key} - {category}")
        print("\nNavigation:")
        print("  n, next, s, suivant - Bloc suivant")
        print("  p, prev, precedent  - Bloc précédent")
        print("  g<num>              - Aller au bloc (ex: g42)")
        print("\nAutres:")
        print("  note                - Ajouter une note")
        print("  stats               - Voir les statistiques")
        print("  h, help, ?          - Afficher cette aide")
        print("  q, quit, exit       - Quitter")
        print("=" * 60)

    def _show_welcome(self) -> None:
        """Show welcome message."""
        print("\n" + "=" * 60)
        print("CLASSIFICATEUR DE SESSIONS AUDIO")
        print("=" * 60)
        print(f"\nSession: {self.session_id}")
        print(f"Total de blocs: {self.total_blocks}")
        print("\nAppuyez sur 'h' pour voir l'aide")
        print("=" * 60)
        input("\nAppuyez sur Entrée pour commencer...")

    def _show_summary(self) -> None:
        """Show summary at the end."""
        print("\n" + "=" * 60)
        print("RÉSUMÉ DE LA SESSION")
        print("=" * 60)
        self._show_statistics()
        print("\nMerci d'avoir utilisé le classificateur!")

    def _wrap_text(self, text: str, width: int) -> list:
        """Wrap text to specified width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1
            if current_length + word_length > width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    lines.append(word[:width])
                    current_line = []
                    current_length = 0
            else:
                current_line.append(word)
                current_length += word_length

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _colorize_category(self, category: str) -> str:
        """Add color to category name."""
        colors = {
            "A classifier": "\033[93m",  # Yellow
            "Publicité": "\033[91m",  # Red
            "Radio": "\033[92m",  # Green
            "Impossible à classifier": "\033[90m",  # Gray
        }
        reset = "\033[0m"
        color = colors.get(category, "")
        return f"{color}{category}{reset}"

    def _clear_screen(self) -> None:
        """Clear terminal screen."""
        print("\033[2J\033[H", end="")
