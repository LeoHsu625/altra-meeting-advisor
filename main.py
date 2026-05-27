import threading
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from audio_recorder import AudioRecorder
from transcriber import transcribe
from transcript_store import TranscriptStore
from ai_client import AIClient
from voice_output import speak
from hotkeys import start_hotkey_listener
from meeting_memory import load_recent_history, save_meeting

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

store = TranscriptStore()
ai = AIClient()
_is_processing = threading.Lock()
_stop_event = threading.Event()
recorder: AudioRecorder | None = None
_chunk_count = 0
_history = ""


def handle_new_chunk(audio_file: str) -> None:
    global _chunk_count
    print("[⏳ 轉錄中...]")
    text = transcribe(audio_file)
    if text:
        _chunk_count += 1
        store.append(text)
        print(f"[逐字稿] {text[:60]}...")
        print(f"[✅ 逐字稿已更新（第 {_chunk_count} 段）｜可按 F9 詢問 AI]\n")
    else:
        print("[靜音片段，略過]\n")


def handle_cue() -> None:
    if not _is_processing.acquire(blocking=False):
        print("[AI] 正在處理中，請稍候...")
        return

    def _run():
        try:
            transcript = store.get_full_transcript()
            print("[AI] 生成建議中...")
            advice = ai.get_advice(transcript, history=_history)
            print(f"\n[AI 建議]\n{advice}\n")
            speak(advice)
        finally:
            _is_processing.release()

    threading.Thread(target=_run, daemon=True).start()


def handle_stop() -> None:
    print("\n[系統] 會議結束，產出摘要中...")
    recorder.stop()

    transcript = store.get_full_transcript()
    summary = ai.get_summary(transcript)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    out_file = OUTPUT_DIR / f"meeting_summary_{timestamp}.md"
    out_file.write_text(
        f"# 會議摘要\n\n{summary}\n\n---\n\n## 完整逐字稿\n\n{transcript}",
        encoding="utf-8",
    )

    global _history
    save_meeting(summary, transcript)
    _history = load_recent_history()

    print(f"\n[摘要]\n{summary}")
    print(f"\n[已儲存至] {out_file}")
    speak("會議摘要已產出，請查看螢幕。")
    _stop_event.set()


if __name__ == "__main__":
    _history = load_recent_history()
    if _history:
        session_count = _history.count("\n\n---\n\n") + 1
        print(f"[記憶] 已載入過去 {session_count} 次會議摘要\n")

    print("=" * 50)
    print("  AI 即時會議顧問系統")
    print("  F9 = 呼叫 AI 建議（語音播放）")
    print("  F10 = 結束會議 + 產出摘要")
    print("=" * 50 + "\n")

    recorder = AudioRecorder(on_chunk_ready=handle_new_chunk)
    recorder.start()

    listener = start_hotkey_listener(on_cue=handle_cue, on_stop=handle_stop)

    try:
        _stop_event.wait()
    finally:
        listener.stop()
        recorder.cleanup()
        print("[系統] 已結束。")
