import asyncio
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from audio_recorder import AudioRecorder
from transcriber import transcribe
from transcript_store import TranscriptStore
from ai_client import AIClient
from voice_output import speak
from meeting_memory import load_recent_history, save_meeting, list_meetings

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(application: FastAPI):
    global _event_loop, _recorder, _history
    _event_loop = asyncio.get_running_loop()
    _history = load_recent_history()
    _recorder = AudioRecorder(on_chunk_ready=_handle_new_chunk, on_chunk_started=_on_chunk_started)
    _recorder.start()
    yield
    if _recorder:
        _recorder.stop()
        _recorder.cleanup()


app = FastAPI(title="AI 即時會議顧問", lifespan=lifespan)

_store = TranscriptStore()
_ai = AIClient()
_is_processing = threading.Lock()
_chunk_count_lock = threading.Lock()
_recorder: AudioRecorder | None = None
_websockets: list[WebSocket] = []
_event_loop: asyncio.AbstractEventLoop | None = None
_history = ""
_chunk_count = 0
_stopped = False
_paused = False
_voice_enabled = False
_current_rec_seq = 0
_in_flight = 0          # number of transcriptions currently running
_in_flight_lock = threading.Lock()


async def _broadcast(message: dict) -> None:
    dead = []
    for ws in list(_websockets):
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _websockets:
            _websockets.remove(ws)


def _sync_broadcast(message: dict) -> None:
    if _event_loop and _event_loop.is_running():
        asyncio.run_coroutine_threadsafe(_broadcast(message), _event_loop)


def _on_chunk_started() -> None:
    global _current_rec_seq
    _current_rec_seq += 1
    seq = _current_rec_seq
    now = datetime.now().strftime("%H:%M:%S")
    _sync_broadcast({"type": "recording_start", "seq": seq, "time": now})


def _transcribe_chunk(audio_file: str, seq: int) -> None:
    global _chunk_count, _in_flight
    with _in_flight_lock:
        _in_flight += 1
    try:
        _sync_broadcast({"type": "transcribing", "seq": seq})
        text = transcribe(audio_file)
        if text:
            with _chunk_count_lock:
                _chunk_count += 1
                count = _chunk_count
            _store.append(text)
            _sync_broadcast({
                "type": "transcript",
                "seq": seq,
                "text": text,
                "full": _store.get_full_transcript(),
                "count": count,
            })
        else:
            _sync_broadcast({"type": "silent", "seq": seq})
    finally:
        with _in_flight_lock:
            _in_flight -= 1


def _handle_new_chunk(audio_file: str) -> None:
    seq = _current_rec_seq
    threading.Thread(target=_transcribe_chunk, args=(audio_file, seq), daemon=True).start()



@app.get("/")
async def index() -> FileResponse:
    return FileResponse("web_static/index.html")


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    _websockets.append(websocket)
    await websocket.send_json({
        "type": "init",
        "transcript": _store.get_full_transcript(),
        "history_loaded": bool(_history),
        "voice_enabled": _voice_enabled,
    })
    try:
        while True:
            await asyncio.sleep(20)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        if websocket in _websockets:
            _websockets.remove(websocket)


@app.post("/cue")
async def cue() -> dict:
    if not _is_processing.acquire(blocking=False):
        return {"status": "busy"}

    def _run() -> None:
        try:
            transcript = _store.get_full_transcript()
            advice = _ai.get_advice(transcript, history=_history)
            if _voice_enabled:
                speak(advice)
            _sync_broadcast({"type": "advice", "text": advice})
        finally:
            _is_processing.release()

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "processing"}


@app.post("/stop")
async def stop_meeting() -> dict:
    global _stopped, _history, _recorder
    if _stopped:
        return {"status": "already_stopped"}
    _stopped = True

    if _recorder:
        _recorder.stop()
        _recorder.cleanup()
        _recorder = None

    # Wait for any in-flight transcriptions to finish (last chunk)
    for _ in range(30):
        with _in_flight_lock:
            if _in_flight == 0:
                break
        await asyncio.sleep(1)

    transcript = _store.get_full_transcript()
    if not transcript:
        return {"status": "empty"}

    summary = _ai.get_summary(transcript)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    out_file = OUTPUT_DIR / f"meeting_summary_{timestamp}.md"
    out_file.write_text(
        f"# 會議摘要\n\n{summary}\n\n---\n\n## 完整逐字稿\n\n{transcript}",
        encoding="utf-8",
    )
    save_meeting(summary, transcript)
    _history = load_recent_history()
    speak("會議摘要已產出，請查看螢幕。")
    _sync_broadcast({"type": "summary", "text": summary, "file": str(out_file)})
    return {"status": "done", "summary": summary, "file": str(out_file)}


@app.get("/history")
async def history() -> list[dict]:
    return list_meetings()


@app.get("/status")
async def status() -> dict:
    can_acquire = _is_processing.acquire(blocking=False)
    if can_acquire:
        _is_processing.release()
    return {
        "segments": _chunk_count,
        "is_processing": not can_acquire,
        "history_loaded": bool(_history),
        "paused": _paused,
        "voice_enabled": _voice_enabled,
    }


@app.post("/voice/toggle")
async def toggle_voice() -> dict:
    global _voice_enabled
    _voice_enabled = not _voice_enabled
    _sync_broadcast({"type": "voice_changed", "enabled": _voice_enabled})
    return {"voice_enabled": _voice_enabled}


@app.post("/pause")
async def pause_recording() -> dict:
    global _paused
    if _paused or not _recorder:
        return {"status": "already_paused"}
    _paused = True
    _recorder.stop()
    _sync_broadcast({"type": "paused"})
    return {"status": "paused"}


@app.post("/resume")
async def resume_recording() -> dict:
    global _paused
    if not _paused or not _recorder:
        return {"status": "not_paused"}
    _paused = False
    _recorder.start()
    _sync_broadcast({"type": "resumed"})
    return {"status": "resumed"}
