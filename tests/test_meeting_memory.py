import json
import pytest
from pathlib import Path
from unittest.mock import patch
import tempfile
import os


@pytest.fixture
def tmp_memory_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_save_creates_json_file(tmp_memory_dir):
    from meeting_memory import save_meeting
    path = save_meeting("## 決議\n- 推進 G3", "逐字稿內容...")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "summary" in data
    assert data["summary"] == "## 決議\n- 推進 G3"


def test_load_empty_returns_empty_string(tmp_memory_dir):
    from meeting_memory import load_recent_history
    result = load_recent_history()
    assert result == ""


def test_load_returns_chronological_order(tmp_memory_dir):
    from meeting_memory import save_meeting, load_recent_history
    import time
    save_meeting("第一次摘要", "逐字稿 A")
    time.sleep(0.01)
    save_meeting("第二次摘要", "逐字稿 B")
    result = load_recent_history()
    # 時間順序：舊 → 新，讓 AI 能追蹤執行脈絡
    assert result.index("第一次") < result.index("第二次")


def test_save_includes_human_readable_date(tmp_memory_dir):
    from meeting_memory import save_meeting
    import re
    path = save_meeting("測試摘要", "逐字稿")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "date" in data
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", data["date"]), \
        f"date 格式應為 YYYY-MM-DD HH:MM，實際為 {data['date']}"


def test_load_shows_human_readable_date(tmp_memory_dir):
    from meeting_memory import save_meeting, load_recent_history
    import re
    save_meeting("測試摘要", "逐字稿")
    result = load_recent_history()
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", result), \
        "歷史記錄應顯示可讀日期，不應出現 20260527_... 格式"


def test_list_meetings_returns_metadata(tmp_memory_dir):
    from meeting_memory import save_meeting, list_meetings
    save_meeting("這是一段超過一百字的摘要內容，用來測試 summary_preview 是否正確截斷。" * 3, "逐字稿內容")
    meetings = list_meetings()
    assert len(meetings) == 1
    m = meetings[0]
    assert "date" in m
    assert "summary_preview" in m
    assert len(m["summary_preview"]) <= 100
    assert m["transcript_chars"] == len("逐字稿內容")


def test_load_respects_max_count(tmp_memory_dir):
    from meeting_memory import save_meeting, load_recent_history
    import time
    for i in range(7):
        save_meeting(f"摘要 {i}", f"逐字稿 {i}")
        time.sleep(0.01)
    result = load_recent_history(n=5)
    assert "摘要 0" not in result
    assert "摘要 1" not in result
    assert "摘要 6" in result
