# src/ui.py

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import IntPrompt
from rich.table import Table
from rich import rule
import sys
from typing import List, Dict, Optional
from prompt_toolkit.patch_stdout import patch_stdout  # FIX: Imports patch_stdout


class ConsoleUI:
    """
    Handles all interactions with the terminal using the Rich library.
    Separates UI logic from business logic.
    """

    def __init__(self, agent_name: str = "default"):
        # Force visible color and set default style for better readability
        self.console = Console(style="white", force_terminal=True)
        self.agent_name = agent_name

    def print_error(self, message: str):
        """Prints an error message."""
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def print_warning(self, message: str):
        """Prints a warning message."""
        self.console.print(f"[yellow]Warning:[/yellow] {message}")

    def print_info(self, message: str, style: str = "dim"):
        """Prints an informational message."""
        self.console.print(f"[{style}]{message}[/{style}]")

    def print_system_message(self, message: str, style: str = "bold green"):
        """Prints a general system message."""
        self.console.print(f"[{style}]{message}[/{style}]")

    def get_user_input(self, prompt: str = "You") -> str:
        # This method is now obsolete and should not be called directly
        # (It is replaced by InputHandler.get_user_input_with_history)
        pass

    def select_from_list(
        self, title: str, items: List[Dict], display_key: str, id_key: str = "id"
    ) -> Optional[str]:
        """Displays a list of items in a table and prompts the user to select one."""
        self.clear_screen()
        table = Table(title=title, border_style="cyan")
        table.add_column("Index", justify="center", style="cyan", no_wrap=True)
        table.add_column(display_key, style="magenta")

        has_desc = items and "desc" in items[0]
        if has_desc:
            table.add_column("Description", style="green")

        for idx, item in enumerate(items):
            row_content = [str(idx + 1), item[display_key]]
            if has_desc:
                row_content.append(item.get("desc", ""))
            table.add_row(*row_content)

        self.console.print(table)

        choices = [str(i + 1) for i in range(len(items))]
        try:
            choice_idx = IntPrompt.ask("Choose an option", choices=choices)
            selected_item = items[int(choice_idx) - 1]
            return selected_item[id_key]
        except (ValueError, IndexError):
            self.print_error("Invalid selection. Please try again.")
            return None

    def display_markdown_stream(self, stream_generator):
        full_response = ""

        self.console.print(
            f"\n[bold cyan]{self.agent_name} $[/bold cyan]", end=" ", markup=True
        )

        try:
            for chunk in stream_generator:
                # print(chunk, end="", flush=True)
                full_response += chunk
        except Exception as e:
            self.print_error(f"Streaming failed: {e}")

        self.console.print()
        self.console.print(Markdown(full_response))
        return full_response

    def display_panel(
        self,
        content: str,
        title: str,
        border_style: str = "blue",
        title_align: str = "left",
        is_markup: bool = False,
    ):
        """Displays content within a Rich Panel."""
        renderable = content if is_markup else Markdown(content)

        self.console.print(
            Panel(
                renderable,
                title=title,
                border_style=border_style,
                title_align=title_align,
                padding=(1, 2),
            ),
            markup=is_markup,
        )

    def display_history(self, history: List[Dict], agent_name: str):
        """Prints the conversation history using styled Panels."""
        if not history:
            self.print_info("No conversation history yet.")
            return

        self.console.rule("[bold blue]Conversation History[/bold blue]")

        for i, message in enumerate(history):
            role = message["role"]
            content = message["content"]

            if role == "user":
                title = f"You > ({i + 1})"
                border_style = "green"
            else:  # agent role
                title = f"{agent_name} $ ({i + 1})"
                border_style = "magenta"

            self.console.print(
                Panel(
                    Markdown(content),
                    title=title,
                    border_style=border_style,
                    title_align="left",
                    padding=(1, 2),
                )
            )
        self.console.rule()

    def show_status(self, message: str, spinner: str = "dots"):
        """Displays a temporary status message with a spinner."""
        with self.console.status(
            f"[bold green]{message}[/bold green]", spinner=spinner
        ):
            pass

    def clear_screen(self):
        """Clears the terminal screen."""
        self.console.clear()

    def exit_app(self, message: str = "[bold blue]Goodbye![/bold blue]"):
        """Prints an exit message and terminates the application."""
        self.console.print(message)
        sys.exit(0)

    def print_table(
        self,
        title: str,
        columns: List[str],
        rows: List[List[str]],
        title_style: str = "bold blue",
    ):
        """Prints a generic table."""
        table = Table(title=title, title_style=title_style)
        for col in columns:
            table.add_column(col, justify="left")
        for row in rows:
            table.add_row(*row)
        self.console.print(table)
