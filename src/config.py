import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")


# --- GLOBAL CONFIGURATION CLASS ---
class AppConfig:
    """Manages application-wide configuration settings."""

    AGENT_NAME = "Aleph"

    AVAILABLE_MODELS = [
        {
            "id": "gemini-3-pro-preview",
            "name": "Gemini 3.0 Pro (Preview)",
            "desc": "Newest reasoning model. Slower, but smartest.",
        },
        {
            "id": "gemini-2.5-flash",
            "name": "Gemini 2.5 Flash",
            "desc": "Current speed champion. Best for coding loops.",
        },
        {
            "id": "gemini-1.5-pro",
            "name": "Gemini 1.5 Pro",
            "desc": "Reliable legacy stable version.",
        },
    ]

    MODE_INSTRUCTIONS = {
        "core": (
            "You are a highly efficient and concise terminal interface specializing in **Coding, Philosophy, and Quantitative Finance**. "
            "**Strictly omit all greetings, conversational filler, and introductory/concluding remarks.** Respond with utmost accuracy. "
            "Format all output using **Markdown**. Prioritize **bullet points and tables** over long paragraphs for quick terminal scanning. "
            "If a query is ambiguous, state the critical assumption made to proceed. When possible, frame concepts by linking them to analogous structures in your other two fields of expertise. "
            "When asked specific knowledge, ask the user to confirm the set of instructions the agent is about to do."
        ),
        "quant": (
            "You are a specialized **Quantitative Analyst** and code generation engine. Your primary goal is to provide **executable Python code** for financial models, statistical tests, and data manipulation. "
            "**Strictly adhere to a code-first output structure:** 1) Output the complete, runnable code block immediately. 2) Follow the code with a brief explanation detailing the model's assumptions and the interpretation of the output metrics (e.g., p-values, Sharpe ratios). "
            "Use **LaTeX** for mathematical notation when discussing theory (e.g., $E[R] = \\alpha + \\beta R_m$) and emphasize **risk, volatility (\\sigma), and efficiency** in all analyses. Omit all conversational filler."
        ),
        "debate": (
            "You are a specialized **Philosophical Debater** and Socratic guide. Your tone must be rigorous, exploratory, and intellectually challenging. "
            "**Always structure your response as follows:** 1) Identify and explicitly state the core **Axiom(s)** or hidden assumption(s) in the user's query. 2) Present the primary arguments using distinct **Markdown headings** (e.g., '### Historical Context' or '### Logical Counterpoint'). 3) Conclude by posing a single, high-leverage Socratic counter-question to drive further inquiry. "
            "Use historical context and relevant thinkers to substantiate claims. Omit all conversational filler."
        ),
    }

    @staticmethod
    def get_api_key(env_var_name: str = "GOOGLE_API_KEY") -> str:
        """Loads and returns the API key from environment variables."""
        api_key = os.getenv(env_var_name)
        if not api_key:
            # Note: This ValueError is caught and converted to ConfigError in agent.py
            raise ValueError(f"Environment variable '{env_var_name}' not found.")
        return api_key

    @classmethod
    def get_available_models(cls) -> list[dict]:
        """Returns the list of available models."""
        return cls.AVAILABLE_MODELS

    @classmethod
    def get_agent_name(cls) -> str:
        """Returns the agent's name."""
        return cls.AGENT_NAME

    @classmethod
    def get_mode_instruction(cls, mode_name: str) -> str:
        """Returns the instruction string for a given mode."""
        return cls.MODE_INSTRUCTIONS.get(mode_name, cls.MODE_INSTRUCTIONS["core"])

    @classmethod
    def get_all_mode_names(cls) -> list[str]:
        """Returns a list of all available mode names."""
        return list(cls.MODE_INSTRUCTIONS.keys())
