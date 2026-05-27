import json
from pathlib import Path
from datetime import datetime
from config import MEMORY_DIR as _MEMORY_DIR_NAME, MAX_HISTORY_COUNT as _DEFAULT_MAX


def _memory_dir() -> Path:
    return Path(_MEMORY_DIR_NAME)


def save_meeting(summary: str, transcript: str) -> Path:
    mem_dir = _memory_dir()
    mem_dir.mkdir(exist_ok=True)
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
    data = {
        "timestamp": timestamp,
        "date": now.strftime("%Y-%m-%d %H:%M"),
        "summary": summary,
        "transcript_chars": len(transcript),
    }
    out = mem_dir / f"{timestamp}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def load_recent_history(n: int = _DEFAULT_MAX) -> str:
    mem_dir = _memory_dir()
    mem_dir.mkdir(exist_ok=True)
    files = sorted(mem_dir.glob("*.json"), reverse=True)[:n]
    if not files:
        return ""
    parts = []
    for f in reversed(files):  # oldest → newest，讓 AI 按時間順序理解脈絡
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            date_label = data.get("date", data["timestamp"])
            parts.append(f"【{date_label}】\n{data['summary']}")
        except (json.JSONDecodeError, KeyError):
            continue
    return "\n\n---\n\n".join(parts)


def list_meetings(n: int = _DEFAULT_MAX) -> list[dict]:
    """回傳最近 n 筆會議的摘要資訊，供 Web UI 顯示（最新在前）。"""
    mem_dir = _memory_dir()
    mem_dir.mkdir(exist_ok=True)
    files = sorted(mem_dir.glob("*.json"), reverse=True)[:n]
    result = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            result.append({
                "filename": f.name,
                "date": data.get("date", data["timestamp"]),
                "summary_preview": data["summary"][:100],
                "transcript_chars": data.get("transcript_chars", 0),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return result
