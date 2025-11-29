from pathlib import Path
from typing import List, Generator, Optional
from google.genai import types
from .gemini_service import GeminiService
from .exceptions import FileAnalysisError, LLMServiceError

# Note: ConsoleUI is passed as an argument (Dependency Injection)


class FileAnalysisHandler:
    """
    Handles the logic for analyzing local files and directories,
    delegating the actual API interactions to GeminiService.
    """

    EXCLUDE_DIRS = [
        "venv",
        ".venv",
        ".git",
        "__pycache__",
        "node_modules",
        "dist",
        ".idea",
        ".vscode",
        "build",
        "target",
    ]
    INCLUDE_EXTENSIONS = [
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".md",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".csv",
        ".xml",
        ".java",
        ".go",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".sh",
        ".bash",
        ".env",
        ".toml",
        ".ini",
        ".log",
    ]

    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

    def _is_excluded(self, path: Path) -> bool:
        """Checks if a path or any of its ancestors are in the exclude list."""
        return any(part in self.EXCLUDE_DIRS for part in path.parts)

    def analyze_file(
        self, agent, file_path_str: str, prompt: str, model_id: str, ui
    ) -> Generator[str, None, None]:
        """
        Uploads a single file and sends its content to the model for analysis.
        Yields chunks of the model's response.
        """
        p = Path(file_path_str)
        if not p.exists():
            raise FileAnalysisError(f"File not found: {file_path_str}")
        if not p.is_file():
            raise FileAnalysisError(f"Path is not a file: {file_path_str}")

        uploaded_file: Optional[types.File] = None
        ui.print_info(f"Uploading file: {p.name}...", style="dim")

        try:
            uploaded_file = self.gemini_service.upload_file(p)
            ui.print_info(
                f"File uploaded successfully. Sent for analysis.", style="dim"
            )

            # Pass UI object to the service layer for logging errors/retries
            yield from self.gemini_service.generate_content_with_files_stream(
                model_id=model_id, prompt=prompt, uploaded_files=[uploaded_file], ui=ui
            )
        except LLMServiceError as e:
            raise FileAnalysisError(
                f"LLM service error during file analysis: {e}"
            ) from e
        finally:
            if uploaded_file:
                self.gemini_service.delete_file(uploaded_file.name, ui)

    def analyze_directory(
        self, agent, directory_path_str: str, prompt: str, model_id: str, ui
    ) -> Generator[str, None, None]:
        """
        Reads all text-based files in a specified directory, uploads them,
        and sends the contents to the model for analysis.
        """
        p = Path(directory_path_str)
        if not p.is_dir():
            raise FileAnalysisError(f"Directory not found: {directory_path_str}")

        files_to_upload: List[Path] = []
        for item in p.rglob("*"):
            if item.is_file() and item.suffix.lower() in self.INCLUDE_EXTENSIONS:
                if not self._is_excluded(item):
                    files_to_upload.append(item)

        if not files_to_upload:
            raise FileAnalysisError(
                f"No relevant files found in directory {p.name}. (Check exclusion list and file extensions.)"
            )

        uploaded_files: List[types.File] = []
        try:
            # 1. Upload all files sequentially
            for file_path in files_to_upload:
                ui.print_info(f"Uploading: {file_path.name}...", style="dim")
                uploaded_files.append(self.gemini_service.upload_file(file_path))

            ui.print_info(
                f"Successfully uploaded {len(uploaded_files)} files. Preparing prompt.",
                style="dim",
            )

            # 2. Build the combined prompt with context
            context_prompt = (
                f"Analyze the following {len(uploaded_files)} files from the project '{p.name}'. "
                f"The user wants you to perform the following task: {prompt}\n\n"
                f"File                                                                  contents are provided below."
            )

            # 3. Stream the analysis response
            yield from self.gemini_service.generate_content_with_files_stream(
                model_id=model_id,
                prompt=context_prompt,
                uploaded_files=uploaded_files,
                ui=ui,  # Pass UI object for logging/retries
            )
        except LLMServiceError as e:
            raise FileAnalysisError(
                f"LLM service error during directory analysis: {e}"
            ) from e
        finally:
            # 4. Cleanup all uploaded file objects from the service
            for uploaded_file in uploaded_files:
                self.gemini_service.delete_file(
                    uploaded_file.name, ui
                )  # Pass UI object for cleanup logging
            ui.print_info(
                f"Clean up complete: Deleted {len(uploaded_files)} files from service.",
                style="dim",
            )
