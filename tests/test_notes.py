"""Unit tests for note storage helpers."""
import server


def test_save_and_list_note(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "NOTES_FILE", tmp_path / "notes.json")
    monkeypatch.setattr(server, "DATA_DIR", tmp_path)

    result = server.save_note("Project demo on Friday", ["Project", "deadline"])
    assert result.startswith("Saved note ")
    listed = server.list_notes()
    assert "Project demo on Friday" in listed
    assert "project, deadline" in listed


def test_search_update_and_delete_note(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "NOTES_FILE", tmp_path / "notes.json")
    monkeypatch.setattr(server, "DATA_DIR", tmp_path)

    saved = server.save_note("Submit the report tomorrow", ["university"])
    note_id = saved.split()[2].rstrip(":")
    assert "Submit the report tomorrow" in server.search_notes("report")
    assert "Updated" in server.update_note(note_id, "Submit the final report today")
    assert "final report" in server.list_notes()
    assert "Deleted" in server.delete_note(note_id)
    assert "No notes saved" in server.list_notes()


def test_empty_note_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "NOTES_FILE", tmp_path / "notes.json")
    monkeypatch.setattr(server, "DATA_DIR", tmp_path)
    assert server.save_note("   ").startswith("ERROR:")
