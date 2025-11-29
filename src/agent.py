# src/agent.py

import json
import sys
from typing import Dict, List, Optional

from .config import AppConfig
from .ui import ConsoleUI
from .gemini_service import GeminiService
from .file_handler import FileAnalysisHandler
from .exceptions import (
    ConfigError,
    AgentError,
    LLMServiceError,
    FileAnalysisError,
    CommandError,
)
from .input_handler import InputHandler


class TerminalAgent:
    """
    The main orchestrator class for the terminal agent.
    It ties together the UI, LLM service, and file analysis components, managing the application state and command dispatch.
    """

    def __init__(self, ui: ConsoleUI):
        self.ui = ui  # UI object is injected from main.py
        self.config = AppConfig()

        try:
            api_key = self.config.get_api_key()
            # Initialize Service (passes mode instructions implicitly)
            self.gemini_service = GeminiService(api_key=api_key)
        except ValueError as e:
            raise ConfigError(f"Initialization failed: {e}") from e

        # Initialize File Handler (Injects the service layer)
        self.file_handler = FileAnalysisHandler(gemini_service=self.gemini_service)

        # Initialize State Variables
        self.agent_name = self.config.get_agent_name()
        self.ui = ConsoleUI(self.agent_name)
        self.available_models = self.config.get_available_models()
        self.mode_instructions = self.config.MODE_INSTRUCTIONS

        self.current_mode_name: str = "core"
        self.current_system_instruction: str = self.config.get_mode_instruction("core")
        self.current_model_id: str = ""

        self.input_handler = InputHandler(self.ui)

        self._init_agent_state()

    def _init_agent_state(self):
        """Initializes the agent's model and chat session."""
        try:
            self._select_model_interface()
        except AgentError as e:
            self.ui.print_error(f"Agent initialization failed: {e}")
            self.ui.exit_app()

    def _select_model_interface(self):
        """Displays models and lets the user select one, then initializes the chat."""
        selected_model_id = self.ui.select_from_list(
            title="Select AI Model",
            items=self.available_models,
            display_key="name",
            id_key="id",
        )
        if selected_model_id:
            self.current_model_id = selected_model_id
            selected_model_name = next(
                (
                    m["name"]
                    for m in self.available_models
                    if m["id"] == selected_model_id
                ),
                selected_model_id,
            )
            self.ui.print_system_message(
                f"Switched to {selected_model_name}", style="bold yellow"
            )
            self.gemini_service.initialize_chat(
                self.current_model_id,
                self.current_system_instruction,
                self.gemini_service.get_history(),
            )
        else:
            raise AgentError("No model selected. Exiting.")

    def _display_header(self):
        """Displays the application header."""
        self.ui.clear_screen()
        self.ui.display_panel(
            content=f"Agent: [bold cyan]{self.agent_name}[/bold cyan]\nModel: [magenta]{self.current_model_id}[/magenta]\nMode: [yellow]{self.current_mode_name.upper()}[/yellow]\nCommands: /model, /save, /load, /clear, /history, /system, /help, /analyze, /dir_analyze, /quit",
            title="Terminal Interface",
            border_style="blue",
            is_markup=True,
        )

    def _handle_slash_command(self, user_input: str) -> bool:
        """Processes slash commands."""
        parts = user_input.strip().split(" ", 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        try:
            if cmd in ["/quit", "/exit"]:
                self.ui.exit_app()
            elif cmd == "/model":
                self._select_model_interface()
                self._display_header()
            elif cmd in ["/history", "/hist"]:
                self.ui.display_history(
                    self.gemini_service.get_history(), self.agent_name
                )
            elif cmd == "/clear":
                self.gemini_service.initialize_chat(
                    self.current_model_id, self.current_system_instruction, []
                )
                self.ui.print_system_message("Memory wiped.", style="yellow")
            elif cmd == "/save":
                filename = arg if arg else "chat_history.json"
                self._save_history(filename)
            elif cmd == "/load":
                filename = arg if arg else "chat_history.json"
                self._load_history(filename)
            elif cmd == "/analyze":
                self._handle_analyze_command(arg, is_directory=False)
            elif cmd == "/dir_analyze":
                self._handle_analyze_command(arg, is_directory=True)
            elif cmd == "/help":
                self._display_help()
            elif cmd == "/system":
                self._handle_system_command(arg)
            elif cmd == "/status":  # Added back for manual refresh capability
                self._display_header()
            else:
                self.ui.print_error(f"Unknown command: {cmd}")
            return True
        except (AgentError, CommandError, LLMServiceError, FileAnalysisError) as e:
            self.ui.print_error(str(e))
            return True
        except Exception as e:
            self.ui.print_error(
                f"An unexpected error occurred during command execution: {e}"
            )
            return True
        return False

    def _handle_analyze_command(self, arg: Optional[str], is_directory: bool):
        """Handles /analyze and /dir_analyze commands."""
        command_name = "/dir_analyze" if is_directory else "/analyze"

        if not arg or len(arg.split(" ", 1)) < 2:
            raise CommandError(f"Usage: {command_name} [path] [prompt]")

        path_str, prompt = arg.split(" ", 1)

        self.ui.print_info(
            f"Analyzing {('directory' if is_directory else 'file')} {path_str}...",
            style="dim",
        )

        # Pass self.ui down to the file handler for correct logging/error display
        if is_directory:
            response_stream = self.file_handler.analyze_directory(
                self, path_str, prompt, self.current_model_id, self.ui
            )
        else:
            response_stream = self.file_handler.analyze_file(
                self, path_str, prompt, self.current_model_id, self.ui
            )

        self.ui.display_markdown_stream(response_stream)

    def _save_history(self, filename: str):
        """Saves the current chat history to a JSON file."""
        try:
            history_data = self.gemini_service.get_history()
            with open(filename, "w") as f:
                json.dump(history_data, f, indent=2)
            self.ui.print_info(f"History saved to {filename}")
        except Exception as e:
            raise AgentError(f"Failed to save history: {e}") from e

    def _load_history(self, filename: str):
        """Loads history from a JSON file and initializes the chat with it."""
        try:
            with open(filename, "r") as f:
                data = json.load(f)

            if not all(
                isinstance(item, dict)
                and "role" in item
                and ("content" in item or "parts" in item)
                for item in data
            ):
                raise ValueError("Loaded history has an invalid format.")

            self.gemini_service.set_history(data)
            self.ui.print_system_message(
                f"History loaded from {filename}", style="green"
            )
        except FileNotFoundError:
            raise AgentError(f"File {filename} not found.")
        except json.JSONDecodeError:
            raise AgentError(f"Invalid JSON format in {filename}.")
        except Exception as e:
            raise AgentError(f"Failed to load history: {e}") from e

    def _display_help(self):
        """Displays the list of available commands."""
        commands = [
            ("/help", "Displays this list of commands."),
            ("/status", "Redraws the header with current agent status."),
            ("/model", "Switch the active Gemini model (retains history)."),
            (
                "/system [mode/text]",
                "Switch modes (core/quant/debate) or set custom instruction.",
            ),
            ("/history | /hist", "Display all previous messages in styled panels."),
            ("/clear", "Wipe the conversation history from memory."),
            ("/save [file]", "Save current chat history to a JSON file."),
            ("/load [file]", "Load chat history from a JSON file."),
            (
                "/analyze [filepath] [prompt]",
                "Upload and analyze a single file with a prompt.",
            ),
            (
                "/dir_analyze [dirpath] [prompt]",
                "Upload and analyze all relevant files in a directory.",
            ),
            ("/quit | /exit", "Exit the terminal agent."),
        ]
        columns = ["Command", "Description"]
        self.ui.print_table("Available Slash Commands", columns, commands)

    def _handle_system_command(self, arg: Optional[str]):
        """Handles the /system command to change modes or set custom instructions."""
        if arg:
            mode_key = arg.lower().strip()
            if mode_key in self.mode_instructions:
                self.current_system_instruction = self.config.get_mode_instruction(
                    mode_key
                )
                self.current_mode_name = mode_key
                self.ui.print_system_message(
                    f"Mode switched to: {mode_key.upper()}", style="bold green"
                )
            else:
                self.current_system_instruction = arg
                self.current_mode_name = "custom"
                self.ui.print_system_message(
                    "System instruction set to CUSTOM.", style="bold yellow"
                )

            self.gemini_service.initialize_chat(
                self.current_model_id,
                self.current_system_instruction,
                self.gemini_service.get_history(),
            )
        else:
            self.ui.print_warning(
                "No argument provided for /system. Current system instruction will be displayed."
            )

        self.ui.display_panel(
            self.current_system_instruction,
            title=f"[yellow]Current System Instruction (Mode: {self.current_mode_name.upper()})[/yellow]",
            border_style="yellow",
        )
        self.ui.print_system_message(
            f"Quick Switch Modes: /system {' | '.join(self.config.get_all_mode_names())}"
        )

    # --- Main Run Loop ---
    def run(self):
        """Main application loop."""
        self._display_header()

        while True:
            try:
                user_input = self.input_handler.get_user_input_with_history()

                if user_input.strip() == "":
                    continue

                if user_input.startswith("/"):
                    if self._handle_slash_command(user_input):
                        continue

                if user_input.strip() == "":
                    continue

                # If not a command, send as chat message
                self.ui.show_status(f"{self.agent_name} is thinking...", spinner="dots")

                # Pass self.ui to the service call!
                response_stream = self.gemini_service.send_message_stream(
                    user_input, self.ui
                )

                # Display stream output
                self.ui.display_markdown_stream(response_stream)

            except KeyboardInterrupt:
                self.ui.print_warning("Interrupted. Type /quit to exit.")
            except AgentError as e:
                self.ui.print_error(str(e))
            except Exception as e:
                self.ui.print_error(f"An unhandled error occurred: {e}")
