# Groq MCP Assistant

A compact Model Context Protocol (MCP) assistant powered by Groq. It combines persistent personal notes and live weather lookup in one server, with a Streamlit chat UI that displays tool calls and results.

This is an independently written learning project informed by the examples in [Xalibur1/mcp_groq](https://github.com/Xalibur1/mcp_groq). See [ATTRIBUTION.md](ATTRIBUTION.md) for provenance and licensing notes.

## Features

- MCP tools to save, search, list, update, and delete notes.
- Current weather lookup through wttr.in (no weather API key required).
- Groq chat completions with OpenAI-compatible tool calling.
- Streamlit interface with visible tool-call and tool-result events.
- Configurable model through environment variables.
- Input validation, bounded tool-call loops, and actionable error messages.
- Local JSON note storage; no database required.

## Requirements

- Python 3.10+
- A Groq API key

## Setup

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `GROQ_API_KEY`. Optionally set `GROQ_MODEL` to a model available in your Groq account.

## Run

```bash
streamlit run app.py
```

## Example prompts

- "Remember that my project demo is on 15 November" — saves a note.
- "What is my project demo date?" — searches notes.
- "What's the weather in Chennai?" — calls the weather tool.
- "Show all my notes" — lists saved notes.

## MCP server

The server can also run independently over stdio:

```bash
python server.py
```

Available tools: `save_note`, `search_notes`, `list_notes`, `update_note`, `delete_note`, and `get_current_weather`.

## Data and privacy

Notes are stored locally in `data/notes.json`. Do not commit personal notes or API keys. The supplied `.gitignore` excludes local environment files and note data. Weather queries are sent to wttr.in. Chat prompts are sent to Groq.

## Project layout

```
.
├── app.py
├── server.py
├── requirements.txt
├── .env.example
├── .gitignore
├── data/
│   └── .gitkeep
└── tests/
    └── test_notes.py
```

## License

No license is granted by this repository unless a LICENSE file is added. Review the upstream project's licensing status before redistributing copied implementation code.
