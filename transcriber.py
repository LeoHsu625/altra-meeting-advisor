import os
import re
import struct
import wave
import math
from config import TRANSCRIPT_CORRECTIONS, WHISPER_BACKEND, WHISPER_MODEL, OPENAI_API_KEY

INITIAL_PROMPT = (
    "以下是益瑞電子的業務會議，"
    "可能涉及 PCB、HDI、AVL 認證、G3、低介電 PI 材料等專業術語。"
)
SILENCE_THRESHOLD = 150  # RMS 低於此值視為靜音，不送 Whisper


def _is_silent(audio_file: str) -> bool:
    try:
        with wave.open(audio_file, "r") as wf:
            frames = wf.readframes(wf.getnframes())
        samples = struct.unpack(f"<{len(frames) // 2}h", frames)
        rms = math.sqrt(sum(s * s for s in samples) / len(samples))
        return rms < SILENCE_THRESHOLD
    except Exception:
        return False


def _is_hallucination(text: str) -> bool:
    if not text or len(text.strip()) < 4:
        return True
    if re.search(r"(.)\1{9,}", text):
        return True
    clean = text.replace(" ", "").replace("　", "").replace("\n", "")
    if clean:
        for char in set(clean):
            if clean.count(char) / len(clean) > 0.4:
                return True
    return False


def _apply_corrections(text: str) -> str:
    for wrong, correct in TRANSCRIPT_CORRECTIONS.items():
        text = text.replace(wrong, correct)
    return text


def _transcribe_with_mlx(audio_file: str) -> str:
    import mlx_whisper  # lazy import：僅 Apple Silicon 可用
    result = mlx_whisper.transcribe(
        audio_file,
        path_or_hf_repo=WHISPER_MODEL,
        language="zh",
        initial_prompt=INITIAL_PROMPT,
    )
    return result.get("text", "").strip()


def _transcribe_with_openai(audio_file: str) -> str:
    import openai  # lazy import：需安裝 openai 套件
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    with open(audio_file, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="zh",
            prompt=INITIAL_PROMPT,
        )
    return result.text.strip()


def transcribe(audio_file: str) -> str:
    try:
        if _is_silent(audio_file):
            return ""
        if WHISPER_BACKEND == "openai":
            text = _transcribe_with_openai(audio_file)
        else:
            text = _transcribe_with_mlx(audio_file)
        if _is_hallucination(text):
            return ""
        return _apply_corrections(text)
    except Exception as e:
        print(f"[轉錄錯誤] {e}")
        return ""
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)
