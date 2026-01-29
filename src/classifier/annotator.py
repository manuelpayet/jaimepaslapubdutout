"""
Interactive console annotator for classifying audio blocks.
Enhanced with Rich UI, direct key capture, and audio playback.
"""

import sqlite3
import sys
import tty
import termios
import logging
import time
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich import box

from src.classifier.audio_player import AudioPlayer

logger = logging.getLogger(__name__)
console = Console()


class Annotator:
    """
    Interactive console interface for annotating audio blocks.
    Features:
    - Direct key capture (no Enter required)
    - Rich terminal UI with colors and panels
    - Audio playback support
    """

    # Available categories
    CATEGORIES = {
        "1": "A classifier",
        "2": "Publicité",
        "3": "Radio",
        "4": "Impossible à classifier",
    }

    # Category metadata
    CATEGORY_ICONS = {
        "A classifier": "⏳",
        "Publicité": "📢",
        "Radio": "📻",
        "Impossible à classifier": "❓",
    }

    CATEGORY_COLORS = {
        "A classifier": "yellow",
        "Publicité": "red",
        "Radio": "green",
        "Impossible à classifier": "dim",
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
        self.raw_session_path = self._get_raw_session_path()

        # Audio player
        self.audio_player = AudioPlayer()

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
                console.print(
                    "\n[bold green]✓ All blocks have been annotated![/bold green]"
                )
                return

            # Main loop
            while True:
                self._display_block(self.current_block_number)

                # Get direct key press
                key = self._get_key()

                if not self._handle_key(key):
                    break

            self._show_summary()

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Annotation interrupted by user[/yellow]")
        finally:
            self.audio_player.cleanup()
            self.conn.close()
            logger.info("Annotation session ended")

    def _get_key(self) -> str:
        """
        Capture a single key press without waiting for Enter.
        Works on Linux/Mac (devcontainer).

        Returns:
            Key pressed as string
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)

            # Handle special keys (arrows, etc.)
            if key == "\x1b":  # Escape sequence
                next1 = sys.stdin.read(1)
                if next1 == "[":
                    next2 = sys.stdin.read(1)
                    if next2 == "A":
                        return "UP"
                    elif next2 == "B":
                        return "DOWN"
                    elif next2 == "C":
                        return "RIGHT"
                    elif next2 == "D":
                        return "LEFT"
                return "ESC"

            return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _handle_key(self, key: str) -> bool:
        """
        Handle key press.

        Args:
            key: Key pressed

        Returns:
            True to continue, False to quit
        """
        # Classification (1-4) - auto-advance
        if key in ["1", "2", "3", "4"]:
            category = self.CATEGORIES[key]
            self._classify_block(self.current_block_number, category)
            self._next_block()
            return True

        # Navigation
        elif key == "RIGHT" or key == " ":  # Right arrow or Space
            self._next_block()
            return True

        elif key == "LEFT":  # Left arrow
            self._previous_block()
            return True

        # Audio playback
        elif key == "p" or key == "P":
            self._play_audio()
            return True

        elif key == "r" or key == "R":
            self._replay_audio()
            return True

        # Help
        elif key == "h" or key == "H":
            self._show_help_overlay()
            return True

        # Statistics
        elif key == "s" or key == "S":
            self._show_statistics_overlay()
            return True

        # Skip to next unclassified
        elif key == "u" or key == "U":
            self._skip_to_unclassified()
            return True

        # Quit
        elif key == "q" or key == "Q":
            return False

        # Unknown key - ignore silently
        return True

    def _display_block(self, block_number: int) -> None:
        """
        Display current block with Rich interface.

        Args:
            block_number: Block number to display
        """
        block = self._get_block(block_number)

        if not block:
            console.print(f"[red]Bloc {block_number} non trouvé[/red]")
            time.sleep(1)
            return

        console.clear()

        # ═══════════════════════════════════════════════════════════
        # 1. HEADER with progress bar
        # ═══════════════════════════════════════════════════════════

        progress_data = self._get_progress()

        title = Text()
        title.append("🎵 ", style="bold yellow")
        title.append("Annotateur Audio", style="bold cyan")
        title.append(f" - {self.session_id}", style="dim")

        progress_text = f"Progression: {progress_data['annotated']}/{progress_data['total']} ({progress_data['percent']:.1f}%)"

        # Progress bar
        bar_width = 50
        filled = int(progress_data["percent"] / 100 * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        progress_display = f"{bar} {progress_data['percent']:.0f}%"

        header_content = f"[cyan]{progress_text}[/cyan]\n{progress_display}"

        header_panel = Panel(
            header_content, title=title, border_style="cyan", box=box.ROUNDED
        )

        console.print(header_panel)
        console.print()

        # ═══════════════════════════════════════════════════════════
        # 2. BLOCK INFO
        # ═══════════════════════════════════════════════════════════

        block_info = Text()
        block_info.append("Bloc #", style="bold")
        block_info.append(f"{block_number:04d}", style="bold yellow")
        block_info.append(" • ", style="dim")
        block_info.append(block["timestamp"][:19], style="cyan")

        console.print(block_info)
        console.print()

        # ═══════════════════════════════════════════════════════════
        # 3. TRANSCRIPTION
        # ═══════════════════════════════════════════════════════════

        transcription = block["transcription"] or "[dim](vide)[/dim]"
        transcription_panel = Panel(
            transcription,
            title="📝 Transcription",
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )

        console.print(transcription_panel)
        console.print()

        # ═══════════════════════════════════════════════════════════
        # 4. CURRENT CATEGORY + CHOICES (side by side)
        # ═══════════════════════════════════════════════════════════

        current_category = block["category"]
        icon = self.CATEGORY_ICONS.get(current_category, "")
        color = self.CATEGORY_COLORS.get(current_category, "white")

        category_text = Text()
        category_text.append(f"{icon} ", style=f"bold {color}")
        category_text.append(current_category, style=f"bold {color}")

        category_panel = Panel(
            category_text,
            title="🏷️  Catégorie actuelle",
            border_style=color,
            box=box.ROUNDED,
            padding=(1, 2),
        )

        # Choices table
        choices_table = Table(
            show_header=False, box=box.SIMPLE, padding=(0, 2), expand=True
        )
        choices_table.add_column("", style="bold", width=6)
        choices_table.add_column("")

        for key, category in self.CATEGORIES.items():
            cat_icon = self.CATEGORY_ICONS.get(category, "")
            cat_color = self.CATEGORY_COLORS.get(category, "white")

            if category == current_category:
                choices_table.add_row(
                    f"[{cat_color}]▶ [{key}][/{cat_color}]",
                    f"[bold {cat_color}]{cat_icon} {category}[/bold {cat_color}]",
                )
            else:
                choices_table.add_row(
                    f"[dim]  [{key}][/dim]",
                    f"[{cat_color}]{cat_icon} {category}[/{cat_color}]",
                )

        choices_panel = Panel(
            choices_table,
            title="🎯 Appuyez sur 1-4 pour classer",
            border_style="green",
            box=box.ROUNDED,
        )

        # Display side by side
        console.print(Columns([category_panel, choices_panel], expand=True))
        console.print()

        # ═══════════════════════════════════════════════════════════
        # 5. AUDIO STATUS
        # ═══════════════════════════════════════════════════════════

        audio_status = (
            "🔊 [green]Lecture en cours...[/green]"
            if self.audio_player.is_playing()
            else "🔇 [dim]Aucun audio en lecture[/dim]"
        )
        console.print(audio_status)
        console.print()

        # ═══════════════════════════════════════════════════════════
        # 6. KEYBOARD SHORTCUTS
        # ═══════════════════════════════════════════════════════════

        shortcuts_table = Table(
            show_header=False, box=None, padding=(0, 2), expand=True
        )
        shortcuts_table.add_column("", justify="center")
        shortcuts_table.add_column("", justify="center")
        shortcuts_table.add_column("", justify="center")

        shortcuts_table.add_row(
            "[cyan]←→[/cyan] Navigation",
            "[magenta]P[/magenta] 🔊 Écouter",
            "[magenta]R[/magenta] 🔁 Rejouer",
        )
        shortcuts_table.add_row(
            "[green]H[/green] ❓ Aide",
            "[blue]S[/blue] 📊 Stats",
            "[yellow]U[/yellow] ⏭️  Non-classé",
        )
        shortcuts_table.add_row("", "[red]Q[/red] ❌ Quitter", "")

        shortcuts_panel = Panel(
            shortcuts_table, title="⌨️  Raccourcis", border_style="dim", box=box.ROUNDED
        )

        console.print(shortcuts_panel)

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

        # Visual feedback
        icon = self.CATEGORY_ICONS.get(category, "")
        color = self.CATEGORY_COLORS.get(category, "white")
        console.print(
            f"\n[bold {color}]✓ Classé comme : {icon} {category}[/bold {color}]"
        )
        time.sleep(0.2)

        logger.debug(f"Block {block_number} classified as: {category}")

    def _play_audio(self) -> None:
        """Play audio for current block."""
        # Check if audio player is available
        if not self.audio_player._is_initialized:
            console.print(f"\n[yellow]⚠️  Lecture audio désactivée[/yellow]")
            console.print(f"[dim]Mode dummy activé (normal en devcontainer)[/dim]")
            console.print(
                f"[dim]Voir .devcontainer/AUDIO.md pour activer l'audio[/dim]"
            )
            time.sleep(1.5)
            return

        block = self._get_block(self.current_block_number)
        if not block:
            return

        # Construct audio file path
        audio_path = (
            self.raw_session_path
            / "blocks"
            / f"block_{self.current_block_number:04d}.wav"
        )

        if not audio_path.exists():
            console.print(f"\n[red]❌ Fichier audio introuvable: {audio_path}[/red]")
            time.sleep(1)
            return

        if self.audio_player.play(str(audio_path)):
            console.print(f"\n[green]🔊 Lecture de l'audio...[/green]")
            time.sleep(0.3)
        else:
            console.print(f"\n[red]❌ Erreur lors de la lecture audio[/red]")
            time.sleep(1)

    def _replay_audio(self) -> None:
        """Replay last audio."""
        current_file = self.audio_player.get_current_file()
        if current_file and current_file.exists():
            self.audio_player.play(str(current_file))
            console.print(f"\n[green]🔁 Rejouer l'audio...[/green]")
            time.sleep(0.3)
        else:
            self._play_audio()

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

    def _get_raw_session_path(self) -> Path:
        """Get path to raw session directory."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key = 'raw_session_path'")
        row = cursor.fetchone()
        if row:
            return Path(row[0])
        else:
            # Fallback: assume data/raw structure
            return Path("data/raw") / self.session_id

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
            console.print("\n[yellow]⚠️  Dernier bloc atteint![/yellow]")
            time.sleep(0.5)

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
            console.print("\n[yellow]⚠️  Premier bloc atteint![/yellow]")
            time.sleep(0.5)

    def _skip_to_unclassified(self) -> None:
        """Skip to next unclassified block."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT block_number FROM blocks
            WHERE block_number > ? AND category = 'A classifier'
            ORDER BY block_number
            LIMIT 1
        """,
            (self.current_block_number,),
        )
        row = cursor.fetchone()

        if row:
            self.current_block_number = row[0]
            console.print("\n[green]⏭️  Sauté au prochain non-classé[/green]")
            time.sleep(0.3)
        else:
            console.print("\n[yellow]⚠️  Aucun bloc non-classé après celui-ci[/yellow]")
            time.sleep(0.5)

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

    def _show_statistics_overlay(self) -> None:
        """Show statistics with Rich table."""
        cursor = self.conn.cursor()

        console.clear()

        stats_table = Table(
            title="📊 Statistiques d'annotation",
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            border_style="cyan",
        )

        stats_table.add_column("Catégorie", style="bold", width=25)
        stats_table.add_column("Nombre", justify="right", style="yellow", width=10)
        stats_table.add_column("Pourcentage", justify="right", style="green", width=12)
        stats_table.add_column("Barre", width=30)

        for category in [
            "A classifier",
            "Publicité",
            "Radio",
            "Impossible à classifier",
        ]:
            cursor.execute(
                "SELECT COUNT(*) FROM blocks WHERE category = ?", (category,)
            )
            count = cursor.fetchone()[0]
            percent = (count / self.total_blocks * 100) if self.total_blocks > 0 else 0

            # Visual bar
            bar_length = int(percent / 100 * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)

            icon = self.CATEGORY_ICONS[category]
            color = self.CATEGORY_COLORS[category]

            stats_table.add_row(
                f"{icon} {category}",
                str(count),
                f"{percent:.1f}%",
                f"[{color}]{bar}[/{color}]",
            )

        # Total row
        stats_table.add_section()
        stats_table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{self.total_blocks}[/bold]",
            "[bold]100.0%[/bold]",
            "█" * 20,
        )

        console.print(stats_table)
        console.print("\n[dim]Appuyez sur une touche pour continuer...[/dim]")
        self._get_key()

    def _show_help_overlay(self) -> None:
        """Show help overlay."""
        console.clear()

        help_text = """
[bold cyan]AIDE - TOUCHES RAPIDES[/bold cyan]

[bold yellow]🔢 Classification:[/bold yellow]
  [cyan]1[/cyan] - ⏳ À classifier
  [cyan]2[/cyan] - 📢 Publicité
  [cyan]3[/cyan] - 📻 Radio
  [cyan]4[/cyan] - ❓ Impossible à classifier

[bold yellow]🔄 Navigation:[/bold yellow]
  [cyan]→[/cyan] ou [cyan]Espace[/cyan] - Bloc suivant
  [cyan]←[/cyan]            - Bloc précédent
  [cyan]U[/cyan]            - Sauter au prochain non-classé

[bold yellow]🎵 Audio:[/bold yellow]
  [cyan]P[/cyan] - Écouter l'audio du bloc
  [cyan]R[/cyan] - Rejouer le dernier audio

[bold yellow]📝 Autres:[/bold yellow]
  [cyan]S[/cyan] - Voir les statistiques
  [cyan]H[/cyan] - Afficher cette aide
  [cyan]Q[/cyan] - Quitter
"""

        help_panel = Panel(
            help_text, border_style="green", box=box.ROUNDED, padding=(1, 2)
        )

        console.print(help_panel)
        console.print("\n[dim]Appuyez sur une touche pour continuer...[/dim]")
        self._get_key()

    def _show_welcome(self) -> None:
        """Show welcome message."""
        console.clear()

        welcome_text = f"""
[bold cyan]CLASSIFICATEUR DE SESSIONS AUDIO[/bold cyan]

Session: [yellow]{self.session_id}[/yellow]
Total de blocs: [yellow]{self.total_blocks}[/yellow]

[dim]Appuyez sur H pour voir l'aide[/dim]
"""

        welcome_panel = Panel(
            welcome_text, border_style="cyan", box=box.DOUBLE, padding=(1, 2)
        )

        console.print(welcome_panel)
        console.print("\n[dim]Appuyez sur une touche pour commencer...[/dim]")
        self._get_key()

    def _show_summary(self) -> None:
        """Show summary at the end."""
        console.clear()

        summary_panel = Panel(
            "[bold green]✓ Session d'annotation terminée[/bold green]",
            border_style="green",
            box=box.DOUBLE,
        )

        console.print(summary_panel)
        console.print()
        self._show_statistics_overlay()
        console.print("\n[cyan]Merci d'avoir utilisé le classificateur![/cyan]")
