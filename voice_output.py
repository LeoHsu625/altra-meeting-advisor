import asyncio
import tempfile
import subprocess
import sys
import os
import edge_tts

VOICE = "zh-TW-HsiaoChenNeural"


async def _speak_async(text: str) -> None:
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    try:
        communicate = edge_tts.Communicate(text, voice=VOICE)
        await communicate.save(tmp_path)
        if sys.platform == "darwin":
            subprocess.run(["afplay", tmp_path], check=True)
        else:
            from playsound import playsound
            playsound(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def speak(text: str) -> None:
    try:
        asyncio.run(_speak_async(text))
    except Exception as e:
        print(f"[語音錯誤] {e}")
