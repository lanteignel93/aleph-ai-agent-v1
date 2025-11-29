# src/gemini_service.py

import time
import sys
from google import genai
from google.genai import types
from google.genai.errors import APIError
from typing import List, Dict, Generator, Optional
from pathlib import Path
from prompt_toolkit.patch_stdout import patch_stdout  # FIX: Imports patch_stdout

from .exceptions import LLMServiceError

# Constants for retry logic
MAX_RETRIES = 3
DELAY = 2


class GeminiService:
    """
    Manages all interactions with the Google Gemini API, handling client state,
    history conversion, file management, and robust content generation.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise LLMServiceError("API Key is required for GeminiService.")
        self.client = genai.Client(api_key=api_key)
        self.chat: Optional[types.ChatSession] = None
        self.current_model: str = ""
        self.system_instruction: str = ""
        self._history: List[Dict] = []

    # ... (History conversion methods remain the same) ...
    def _convert_genai_history_to_dict(
        self, genai_history: List[types.Content]
    ) -> List[Dict]:
        """Converts Gemini's history format to a list of dicts for easier serialization/display."""
        return [
            {
                "role": content.role,
                "content": content.parts[0].text
                if content.parts and content.parts[0].text
                else "",
            }
            for content in genai_history
        ]

    def _convert_dict_history_to_genai(
        self, dict_history: List[Dict]
    ) -> List[types.Content]:
        """Converts a list of dicts back to Gemini's history format."""
        return [
            types.Content(
                role=item["role"], parts=[types.Part.from_text(text=item["content"])]
            )
            for item in dict_history
        ]

    # ... (Chat State Management methods remain the same) ...
    def initialize_chat(
        self,
        model_id: str,
        system_instruction: str,
        initial_history: Optional[List[Dict]] = None,
    ):
        """Initializes or resets the chat session."""
        self.current_model = model_id
        self.system_instruction = system_instruction
        self._history = initial_history if initial_history else []

        try:
            config = types.GenerateContentConfig(
                system_instruction=self.system_instruction
            )
            genai_history = self._convert_dict_history_to_genai(self._history)

            self.chat = self.client.chats.create(
                model=self.current_model, config=config, history=genai_history
            )
        except APIError as e:
            raise LLMServiceError(f"Failed to initialize chat session: {e}") from e
        except Exception as e:
            raise LLMServiceError(
                f"An unexpected error occurred during chat initialization: {e}"
            ) from e

    def get_history(self) -> List[Dict]:
        """Returns the current conversation history in the local dict format."""
        return self._history

    def set_history(self, history: List[Dict]):
        """Sets the internal history. Requires re-initializing the chat to apply the history."""
        self._history = history
        if self.chat:
            self.initialize_chat(
                self.current_model, self.system_instruction, self._history
            )

    # --- Generation Logic (FIXED) ---
    def send_message_stream(self, user_message: str, ui) -> Generator[str, None, None]:
        """Sends a message to the chat and yields text chunks (handles retry logic)."""
        if not self.chat:
            raise LLMServiceError(
                "Chat session not initialized. Call initialize_chat first."
            )

        delay = DELAY
        for attempt in range(MAX_RETRIES):
            try:
                response_stream = self.chat.send_message_stream(user_message)

                with patch_stdout():
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text

                self._history = self._convert_genai_history_to_dict(
                    self.chat._curated_history
                )
                return

            except APIError as e:
                if attempt < MAX_RETRIES - 1:
                    ui.print_warning(
                        f"API Error on chat attempt {attempt + 1}. Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise LLMServiceError(
                        f"Fatal API Error after {MAX_RETRIES} attempts: {e}"
                    ) from e
            except Exception as e:
                raise LLMServiceError(
                    f"An unexpected error occurred during chat message: {e}"
                ) from e

    def generate_content_with_files_stream(
        self, model_id: str, prompt: str, uploaded_files: List[types.File], ui
    ) -> Generator[str, None, None]:
        """
        Generates content from the model using a prompt and uploaded files.
        This is for one-off file analysis (no chat history retained).
        """
        contents = [prompt] + uploaded_files
        delay = DELAY

        for attempt in range(MAX_RETRIES):
            try:
                response_stream = self.client.models.generate_content_stream(
                    model=model_id, contents=contents
                )
                # FIX: Wrap the yielding process for file analysis
                with patch_stdout():
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text
                return

            except APIError as e:
                if attempt < MAX_RETRIES - 1:
                    ui.print_warning(
                        f"API Error on file attempt {attempt + 1}. Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise LLMServiceError(
                        f"Fatal API Error after {MAX_RETRIES} attempts during file analysis: {e}"
                    ) from e
            except Exception as e:
                raise LLMServiceError(
                    f"An unexpected error occurred during file content generation: {e}"
                ) from e

    # --- File Management Methods ---
    def upload_file(self, file_path: Path) -> types.File:
        """Uploads a local file to the Gemini API."""
        try:
            return self.client.files.upload(file=file_path)
        except APIError as e:
            raise LLMServiceError(
                f"Failed to upload file '{file_path.name}': {e}"
            ) from e
        except Exception as e:
            raise LLMServiceError(
                f"An unexpected error occurred during file upload: {e}"
            ) from e

    def delete_file(self, file_name: str, ui):
        """Deletes an uploaded file from the Gemini API. Error logged using UI."""
        try:
            self.client.files.delete(name=file_name)
        except Exception as e:
            ui.print_warning(f"Failed to delete uploaded file '{file_name}': {e}")
