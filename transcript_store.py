import threading
from datetime import datetime
from typing import List, Dict


class TranscriptStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._segments: List[Dict] = []

    def append(self, text: str) -> int | None:
        if not text or not text.strip():
            return None
        with self._lock:
            self._segments.append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "text": text.strip(),
            })
            return len(self._segments) - 1

    def update_segment(self, index: int, text: str) -> bool:
        with self._lock:
            if 0 <= index < len(self._segments):
                self._segments[index]["text"] = text.strip()
                return True
            return False

    def get_full_transcript(self) -> str:
        with self._lock:
            return "\n".join(
                f"[{seg['timestamp']}] {seg['text']}"
                for seg in self._segments
            )

    def clear(self) -> None:
        with self._lock:
            self._segments = []

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._segments) == 0
