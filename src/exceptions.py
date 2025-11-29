class AgentError(Exception):
    """Base exception for all agent-related errors."""

    pass


class ConfigError(AgentError):
    """Error related to configuration issues (e.g., missing API key)."""

    pass


class LLMServiceError(AgentError):
    """Error related to the LLM service interaction (API errors, retries failed)."""

    pass


class FileAnalysisError(AgentError):
    """Error during file or directory analysis (e.g., file not found, upload failed)."""

    pass


class CommandError(AgentError):
    """Error when parsing or executing a command."""

    pass
