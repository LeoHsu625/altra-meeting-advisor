import pyaudio
import wave
import tempfile
import threading
from typing import Callable

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 30


class AudioRecorder:
    def __init__(
        self,
        on_chunk_ready: Callable[[str], None],
        on_chunk_started: Callable[[], None] | None = None,
    ):
        self._on_chunk_ready = on_chunk_ready
        self._on_chunk_started = on_chunk_started
        self._recording = False
        self._thread: threading.Thread | None = None
        self._p = pyaudio.PyAudio()

    def start(self) -> None:
        self._recording = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._recording = False

    def cleanup(self) -> None:
        self._p.terminate()

    def _record_loop(self) -> None:
        while self._recording:
            if self._on_chunk_started:
                self._on_chunk_started()
            print("[🎙 錄音中（30 秒）...]")
            audio_file = self._record_chunk()
            if audio_file:  # always send, even if stopped mid-chunk
                self._on_chunk_ready(audio_file)

    def _record_chunk(self) -> str | None:
        try:
            stream = self._p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
            )
            frames = []
            total_frames = int(RATE / CHUNK * RECORD_SECONDS)
            for _ in range(total_frames):
                if not self._recording:
                    break
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            stream.stop_stream()
            stream.close()

            if not frames:
                return None

            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            with wave.open(tmp.name, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self._p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b"".join(frames))
            return tmp.name
        except Exception as e:
            print(f"[錄音錯誤] {e}")
            return None
