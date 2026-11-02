"""Combined MCP server: personal notes and current weather."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import httpx
from mcp.server.fastmcp import FastMCP

DATA_DIR = Path(__file__).parent / "data"
NOTES_FILE = DATA_DIR / "notes.json"
mcp = FastMCP("groq-mcp-assistant")

STOPWORDS = {
    "a", "an", "the", "i", "me", "my", "we", "you", "is", "are", "was", "were",
    "do", "did", "does", "what", "when", "where", "which", "who", "how", "about",
    "say", "said", "tell", "of", "to", "in", "on", "for", "and", "or", "that",
    "this", "it", "with", "have", "had", "remember", "find", "show",
}


def _load_notes() -> list[dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not NOTES_FILE.exists():
        return []
    try:
        data = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Notes file must contain a JSON list.")
        return data
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        raise RuntimeError(f"Could not read notes storage: {exc}") from exc


def _save_notes(notes: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = NOTES_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_file.replace(NOTES_FILE)


def _clean_text(value: str, field: str, limit: int = 4000) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field} cannot be empty.")
    if len(value) > limit:
        raise ValueError(f"{field} must be {limit} characters or fewer.")
    return value


def _keywords(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOPWORDS]


def _format_note(note: dict) -> str:
    tags = ", ".join(note.get("tags", [])) or "none"
    return f"[{note['id']}] {note['content']} (tags: {tags}; saved: {note['created_at']})"


@mcp.tool()
def save_note(content: str, tags: list[str] | None = None) -> str:
    """Save a note. Tags are optional short labels."""
    try:
        content = _clean_text(content, "content")
        clean_tags = []
        for tag in (tags or [])[:10]:
            clean = _clean_text(tag, "tag", 40).lower()
            if clean not in clean_tags:
                clean_tags.append(clean)
        notes = _load_notes()
        note = {
            "id": uuid.uuid4().hex[:8],
            "content": content,
            "tags": clean_tags,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        notes.append(note)
        _save_notes(notes)
        return f"Saved note {note['id']}: {note['content']}"
    except (ValueError, RuntimeError) as exc:
        return f"ERROR: {exc}"


@mcp.tool()
def search_notes(query: str) -> str:
    """Search saved notes by words in their content and tags."""
    words = _keywords(query)
    if not words:
        return "Enter at least one meaningful search word."
    try:
        scored = []
        for note in _load_notes():
            content = note.get("content", "").lower()
            tags = note.get("tags", [])
            score = sum(2 for word in words if word in tags) + sum(word in content for word in words)
            if score:
                scored.append((score, note))
        scored.sort(key=lambda item: item[0], reverse=True)
        return "\n".join(_format_note(note) for _, note in scored[:10]) or f"No notes found for: {query}"
    except RuntimeError as exc:
        return f"ERROR: {exc}"


@mcp.tool()
def list_notes() -> str:
    """List all saved notes."""
    try:
        notes = _load_notes()
        return "\n".join(_format_note(note) for note in notes) if notes else "No notes saved yet."
    except RuntimeError as exc:
        return f"ERROR: {exc}"


@mcp.tool()
def update_note(note_id: str, content: str) -> str:
    """Replace the content of a note using its ID."""
    try:
        content = _clean_text(content, "content")
        notes = _load_notes()
        for note in notes:
            if note.get("id") == note_id:
                note["content"] = content
                _save_notes(notes)
                return f"Updated note {note_id}."
        return f"No note with id {note_id}."
    except (ValueError, RuntimeError) as exc:
        return f"ERROR: {exc}"


@mcp.tool()
def delete_note(note_id: str) -> str:
    """Delete a note by its ID."""
    try:
        notes = _load_notes()
        kept = [note for note in notes if note.get("id") != note_id]
        if len(kept) == len(notes):
            return f"No note with id {note_id}."
        _save_notes(kept)
        return f"Deleted note {note_id}."
    except RuntimeError as exc:
        return f"ERROR: {exc}"


@mcp.tool()
def get_current_weather(location: str) -> str:
    """Get current weather for a city or place using wttr.in."""
    try:
        location = _clean_text(location, "location", 120)
        url = f"https://wttr.in/{quote(location, safe='')}"
        response = httpx.get(
            url,
            params={"format": "j1"},
            timeout=10.0,
            headers={"User-Agent": "groq-mcp-assistant/1.0"},
        )
        response.raise_for_status()
        payload = response.json()
        current = payload["current_condition"][0]
        area = payload["nearest_area"][0]
        place = f"{area['areaName'][0]['value']}, {area['country'][0]['value']}"
        return (
            f"Location: {place}\n"
            f"Condition: {current['weatherDesc'][0]['value']}\n"
            f"Temperature: {current['temp_C']} C (feels like {current['FeelsLikeC']} C)\n"
            f"Humidity: {current['humidity']}%\n"
            f"Wind: {current['windspeedKmph']} km/h {current['winddir16Point']}\n"
            f"Precipitation: {current['precipMM']} mm\n"
            f"Visibility: {current['visibility']} km\n"
            f"UV index: {current['uvIndex']}"
        )
    except httpx.TimeoutException:
        return f"ERROR: Weather lookup timed out for '{location}'."
    except httpx.HTTPStatusError as exc:
        return f"ERROR: Weather service returned HTTP {exc.response.status_code}."
    except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
        return f"ERROR: Could not retrieve valid weather data ({exc})."


if __name__ == "__main__":
    mcp.run(transport="stdio")
