from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from .ui import ConsoleUI  # For accessing rich console object
from .config import AppConfig  # For getting the agent name

# Define the custom style for prompt_toolkit to match Rich's colors
# This ensures the input text area appears consistent with the rest of the UI.
PTK_STYLE = Style.from_dict(
    {
        "prompt": "ansigreen bold",
        "text": "#ffffff",
    }
)


class InputHandler:
    def __init__(self, ui: ConsoleUI):
        self.ui = ui
        # Load history from a file for persistence across sessions
        agent_name_lower = AppConfig.get_agent_name().lower()
        self.history = FileHistory(f".{agent_name_lower}_command_history")

    def get_user_input_with_history(self) -> str:
        """
        Uses prompt_toolkit to capture input, enabling UP/DOWN arrow history recall.
        Returns the user's input string.
        """

        prompt_text = f"\nYou > "

        try:
            return prompt(
                message=prompt_text,  # PASS THE PROMPT HERE
                history=self.history,
                style=PTK_STYLE,
                mouse_support=False,
                vi_mode=False,
            ).strip()
        except EOFError:
            return "/quit"
        except KeyboardInterrupt:
            return ""
