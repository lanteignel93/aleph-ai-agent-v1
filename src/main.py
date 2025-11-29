import sys

# Importing the classes needed for instantiation and exceptions
from .agent import TerminalAgent
from .exceptions import AgentError, ConfigError
from .ui import ConsoleUI


def main():
    """Initializes and runs the Aleph Terminal Agent."""

    # 1. Initialize UI first to ensure we have a styled console for all output
    ui = ConsoleUI()

    try:
        # 2. Initialize Agent (This is where API key checks and model selection happen)
        agent = TerminalAgent(ui)

        # 3. Start the main application loop
        agent.run()

    except ConfigError as e:
        # Catches errors related to missing API key, etc.
        ui.print_error(f"Configuration Error: {e}")
        sys.exit(1)
    except AgentError as e:
        # Catches general application errors (chat init failure, etc.)
        ui.print_error(f"Application Error: {e}")
        sys.exit(1)
    except Exception as e:
        # Catches any unexpected Python runtime errors
        ui.print_error(f"An unexpected fatal error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
