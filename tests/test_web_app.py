import importlib
import sys
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "web_static").mkdir()
    (tmp_path / "web_static" / "index.html").write_text(
        "<html>Meeting Advisor</html>", encoding="utf-8"
    )
    import web_app
    importlib.reload(web_app)
    mock_rec = MagicMock()
    with patch.object(web_app, "AudioRecorder", return_value=mock_rec), \
         patch.object(web_app, "speak"):
        with TestClient(web_app.app) as c:
            yield c


def test_status_returns_expected_fields(client):
    resp = client.get("/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "segments" in data
    assert "is_processing" in data
    assert "history_loaded" in data
    assert "paused" in data


def test_cue_returns_processing_or_busy(client):
    resp = client.post("/cue")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("processing", "busy")


def test_history_empty_on_fresh_start(client):
    resp = client.get("/history")
    assert resp.status_code == 200
    assert resp.json() == []


def test_history_returns_saved_meetings(client):
    from meeting_memory import save_meeting
    save_meeting("## 決議\n- G3 推進", "逐字稿內容")
    resp = client.get("/history")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "date" in data[0]
    assert "summary_preview" in data[0]
    assert "transcript_chars" in data[0]


def test_pause_changes_status(client):
    client.post("/pause")
    resp = client.get("/status")
    assert resp.json()["paused"] is True


def test_stop_empty_meeting(client):
    resp = client.post("/stop")
    assert resp.status_code == 200
    assert resp.json()["status"] == "empty"
