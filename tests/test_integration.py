"""
整合測試：驗證完整會議流程
（逐字稿 → AI 建議 → 結束 → 摘要儲存 → 歷史跨 session 保留）
"""
import importlib
import json
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

MOCK_ADVICE = "這個方向值得推進，先確認會計師的決策時程。"
MOCK_SUMMARY = (
    "## 決議事項\n- G3 計畫下週提案\n\n"
    "## 待辦清單\n| 任務 | 負責人 | 期限 |\n|---|---|---|\n| 準備提案 | Leo | 2026-06-03 |"
)


def _setup(tmp_path, monkeypatch, advice=MOCK_ADVICE, summary=MOCK_SUMMARY):
    """重置 web_app module 並注入所有 mock，回傳 (client, module)。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "web_static").mkdir(exist_ok=True)
    (tmp_path / "web_static" / "index.html").write_text(
        "<html>Meeting Advisor</html>", encoding="utf-8"
    )
    import web_app
    importlib.reload(web_app)
    web_app.AudioRecorder = MagicMock(return_value=MagicMock())
    web_app.speak = MagicMock()
    web_app._ai.get_advice = MagicMock(return_value=advice)
    web_app._ai.get_summary = MagicMock(return_value=summary)
    return TestClient(web_app.app), web_app


def _wait_for(condition_fn, timeout=2.0, interval=0.05):
    """輪詢等待條件成立（避免 sleep 硬等造成 flaky test）。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition_fn():
            return True
        time.sleep(interval)
    return False


# ── 1. 靜態頁面正常提供 ────────────────────────────────────────────
def test_index_html_served(tmp_path, monkeypatch):
    client, _ = _setup(tmp_path, monkeypatch)
    with client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Meeting Advisor" in resp.text


# ── 2. 初始狀態正確 ────────────────────────────────────────────────
def test_initial_status(tmp_path, monkeypatch):
    client, _ = _setup(tmp_path, monkeypatch)
    with client:
        data = client.get("/status").json()
        assert data["segments"] == 0
        assert data["is_processing"] is False
        assert data["paused"] is False


# ── 3. 逐字稿 → F9 → AI 建議完整流程 ─────────────────────────────
def test_transcript_to_advice_flow(tmp_path, monkeypatch):
    client, app = _setup(tmp_path, monkeypatch)
    with client:
        # 模擬音訊轉錄結果寫入 store
        app._store.append("Leo 說 G3 計畫需要第一個成功案例。")
        app._store.append("Michelle 問是否有合適的會計師可以合作。")

        # 按 F9
        resp = client.post("/cue")
        assert resp.status_code == 200
        assert resp.json()["status"] in ("processing", "busy")

        # 等待後台執行緒完成 AI 呼叫
        called = _wait_for(lambda: app._ai.get_advice.called)
        assert called, "AI get_advice 在 2 秒內未被呼叫"

        # 驗證傳給 AI 的逐字稿包含兩段內容
        transcript_sent = app._ai.get_advice.call_args[0][0]
        assert "G3" in transcript_sent
        assert "Michelle" in transcript_sent


# ── 4. F10 → 摘要儲存至檔案 ───────────────────────────────────────
def test_stop_saves_summary_file(tmp_path, monkeypatch):
    client, app = _setup(tmp_path, monkeypatch)
    with client:
        app._store.append("今天決定推進 G3 計畫，目標下週提案。")

        resp = client.post("/stop")
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"

        files = list((tmp_path / "output").glob("meeting_summary_*.md"))
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8")
        assert "決議事項" in content
        assert "逐字稿" in content


# ── 5. F10 → 歷史記憶 JSON 正確儲存 ──────────────────────────────
def test_stop_saves_memory_json(tmp_path, monkeypatch):
    client, app = _setup(tmp_path, monkeypatch)
    with client:
        app._store.append("確認 G3 計畫方向。")

        client.post("/stop")

        history_files = list((tmp_path / "meeting_history").glob("*.json"))
        assert len(history_files) == 1

        saved = json.loads(history_files[0].read_text(encoding="utf-8"))
        assert saved["summary"] == MOCK_SUMMARY
        assert "date" in saved  # 人可讀格式（非 timestamp）
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", saved["date"])


# ── 6. 歷史記憶跨 session 保留 ───────────────────────────────────
def test_history_persists_across_sessions(tmp_path, monkeypatch):
    # Session 1：完成一次會議
    client1, app1 = _setup(tmp_path, monkeypatch)
    with client1:
        app1._store.append("第一次會議：確認 G3 計畫方向。")
        client1.post("/stop")

    # Session 2：模擬重新啟動（reload module）
    import web_app
    importlib.reload(web_app)
    web_app.AudioRecorder = MagicMock(return_value=MagicMock())
    web_app.speak = MagicMock()
    web_app._ai.get_advice = MagicMock(return_value=MOCK_ADVICE)
    web_app._ai.get_summary = MagicMock(return_value=MOCK_SUMMARY)

    with TestClient(web_app.app) as client2:
        # /history 應回傳 session 1 的記錄
        meetings = client2.get("/history").json()
        assert len(meetings) == 1
        assert "date" in meetings[0]

        # /status 應顯示 history_loaded=True（lifespan 自動載入）
        status = client2.get("/status").json()
        assert status["history_loaded"] is True


# ── 7. 暫停 / 繼續循環 ─────────────────────────────────────────────
def test_pause_resume_cycle(tmp_path, monkeypatch):
    client, _ = _setup(tmp_path, monkeypatch)
    with client:
        assert client.get("/status").json()["paused"] is False

        client.post("/pause")
        assert client.get("/status").json()["paused"] is True

        client.post("/resume")
        assert client.get("/status").json()["paused"] is False


# ── 8. 空會議不產出摘要 ─────────────────────────────────────────────
def test_stop_with_empty_transcript_returns_empty(tmp_path, monkeypatch):
    client, _ = _setup(tmp_path, monkeypatch)
    with client:
        resp = client.post("/stop")
        assert resp.status_code == 200
        assert resp.json()["status"] == "empty"

        # 不應產生任何 output 檔
        output_files = list((tmp_path / "output").glob("*.md")) if (tmp_path / "output").exists() else []
        assert len(output_files) == 0
