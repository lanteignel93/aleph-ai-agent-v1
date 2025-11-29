# Aleph Terminal Agent 🧠

The **Aleph Terminal Agent** is a highly efficient, command-line interface (CLI) application built with Python. It leverages the Google Gemini API to serve as a specialized assistant for **Coding, Philosophy, and Quantitative Finance**.

The agent is designed for terminal power users, featuring stable history recall (up/down arrows), a clean Rich-based UI, and modular architecture.

## ✨ Features

* **Three Operational Modes:** Quickly switch the agent's persona and instruction set between **Core**, **Quant Analyst**, and **Philosophical Debater**.
* **Local File Analysis:** Use `/dir_analyze` to securely upload and analyze the contents of an entire directory (skipping virtual environments and build files).
* **Robust I/O:** Stable input/output handling via `prompt-toolkit` and `rich`, ensuring history recall and clean, styled output.
* **Modular Design:** Built with clear separation of concerns into dedicated layers (`service`, `ui`, `file_handler`).

---

## 🚀 Setup and Installation

This guide assumes you have Python >= 3.10, Git, and the ability to install Python packages (via `pip`).

### 1. Clone the Repository

```bash
git clone git@github.com:lanteignel93/aleph-ai-agent-v1.git
cd aleph-terminal-agent
````

### 2\. Create and Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/macOS
# venv\Scripts\activate.bat # On Windows CMD
```

### 3\. Install Dependencies (Editable Mode)

Install all necessary libraries and link the project using the configuration defined in `pyproject.toml`:

```bash
pip install -e .
```

### 4\. Configure API Key

Create a file named `.env` in the root directory and add your Gemini API key:

```ini
# .env
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```

-----

## ▶️ Usage

The project is configured to run via a console script defined in `pyproject.toml`.

### 1\. Launch the Agent

If your environment is active, simply type the console script command:

```bash
aleph
```

### 2\. Key Commands

| Command | Purpose |
| :--- | :--- |
| `/system [mode]` | Switch persona: **core** (default), **quant**, or **debate**. |
| `/dir_analyze [path] [prompt]` | Analyze contents of an entire directory (e.g., `/dir_analyze . "Find bugs"`). |
| `/model` | Select a different Gemini model (e.g., Pro vs. Flash). |
| `/history` | View the conversation history. |
| `/quit` | Exit the application. |

-----

## ⚙️ Project Structure

The project follows a standard modular pattern for clarity and maintainability:

```
aleph-terminal-agent/
├── src/
│   ├── agent.py          # The main orchestrator/controller logic.
│   ├── ui.py             # Rich UI rendering and input handling.
│   ├── gemini_service.py # LLM API communication and retry logic.
│   ├── file_handler.py   # File system traversal and analysis logic.
│   └── config.py         # Static configuration (modes, models).
├── pyproject.toml        # Project metadata, dependencies, and entry point.
└── .gitignore            # Files ignored by Git.
```
------
