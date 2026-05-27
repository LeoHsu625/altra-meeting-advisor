"""測試 transcriber 的雙後端邏輯（mlx / openai），不實際呼叫 API。"""
import os
import wave
import struct
import tempfile
import pytest
from unittest.mock import MagicMock, patch
import transcriber


def _make_wav(rms_value: int = 500) -> str:
    """產生一個有聲音的假 WAV 檔（非靜音）。"""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    samples = [rms_value] * 16000  # 1 秒
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return tmp.name


def _make_silent_wav() -> str:
    """產生靜音 WAV 檔（RMS ≈ 0）。"""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    samples = [0] * 16000
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return tmp.name


# ── mlx 後端 ────────────────────────────────────────────────────
def test_mlx_backend_returns_transcribed_text():
    mock_mlx = MagicMock()
    mock_mlx.transcribe.return_value = {"text": "G3 計畫需要第一個成功案例。"}

    wav = _make_wav()
    with patch.object(transcriber, "WHISPER_BACKEND", "mlx"), \
         patch.dict("sys.modules", {"mlx_whisper": mock_mlx}):
        result = transcriber.transcribe(wav)

    assert result == "G3 計畫需要第一個成功案例。"


def test_mlx_backend_silent_returns_empty():
    mock_mlx = MagicMock()

    wav = _make_silent_wav()
    with patch.object(transcriber, "WHISPER_BACKEND", "mlx"), \
         patch.dict("sys.modules", {"mlx_whisper": mock_mlx}):
        result = transcriber.transcribe(wav)

    assert result == ""
    mock_mlx.transcribe.assert_not_called()


# ── openai 後端 ──────────────────────────────────────────────────
def test_openai_backend_returns_transcribed_text():
    mock_openai = MagicMock()
    mock_client = MagicMock()
    mock_openai.OpenAI.return_value = mock_client
    mock_client.audio.transcriptions.create.return_value = MagicMock(
        text="AVL 認證還沒過，客戶說要等 HDI 驗證完。"
    )

    wav = _make_wav()
    with patch.object(transcriber, "WHISPER_BACKEND", "openai"), \
         patch.dict("sys.modules", {"openai": mock_openai}):
        result = transcriber.transcribe(wav)

    assert result == "AVL 認證還沒過，客戶說要等 HDI 驗證完。"
    mock_client.audio.transcriptions.create.assert_called_once()


def test_openai_backend_sends_correct_params():
    mock_openai = MagicMock()
    mock_client = MagicMock()
    mock_openai.OpenAI.return_value = mock_client
    mock_client.audio.transcriptions.create.return_value = MagicMock(text="測試")

    wav = _make_wav()
    with patch.object(transcriber, "WHISPER_BACKEND", "openai"), \
         patch.dict("sys.modules", {"openai": mock_openai}):
        transcriber.transcribe(wav)

    kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
    assert kwargs["model"] == "whisper-1"
    assert kwargs["language"] == "zh"
    assert "益瑞電子" in kwargs["prompt"]


# ── 共用邏輯（與後端無關）────────────────────────────────────────
def test_corrections_applied():
    mock_mlx = MagicMock()
    mock_mlx.transcribe.return_value = {"text": "利奧說這個方向對。"}

    wav = _make_wav()
    with patch.object(transcriber, "WHISPER_BACKEND", "mlx"), \
         patch.dict("sys.modules", {"mlx_whisper": mock_mlx}):
        result = transcriber.transcribe(wav)

    assert "Leo" in result
    assert "利奧" not in result


def test_hallucination_filtered():
    mock_mlx = MagicMock()
    mock_mlx.transcribe.return_value = {"text": "吉吉吉吉吉吉吉吉吉吉吉吉"}

    wav = _make_wav()
    with patch.object(transcriber, "WHISPER_BACKEND", "mlx"), \
         patch.dict("sys.modules", {"mlx_whisper": mock_mlx}):
        result = transcriber.transcribe(wav)

    assert result == ""
