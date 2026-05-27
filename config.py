import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
# "mlx"    → 本機 Apple Silicon（Leo 的 Mac，預設）
# "openai" → OpenAI Whisper API（Windows 或無 M 晶片的機器）
WHISPER_BACKEND   = os.getenv("WHISPER_BACKEND", "mlx")

AUDIO_CHUNK = 1024
AUDIO_CHANNELS = 1
AUDIO_RATE = 16000
RECORD_SECONDS = 30
WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"  # mlx 模式專用
TTS_VOICE = "zh-TW-HsiaoChenNeural"
HOTKEY_CUE = "<f9>"
HOTKEY_STOP = "<f10>"
OUTPUT_DIR = "output"

# 逐字稿自動替換表：Whisper 常見音譯錯誤 → 正確名稱
# 遇到新的錯誤直接在這裡新增即可
TRANSCRIPT_CORRECTIONS = {
    # Leo
    "利奧": "Leo", "李奧": "Leo", "里奧": "Leo",
    "利歐": "Leo", "里歐": "Leo", "李歐": "Leo",
    "利偶": "Leo", "理歐": "Leo", "黎歐": "Leo",
    # Michelle
    "米雪兒": "Michelle", "蜜雪兒": "Michelle", "密雪兒": "Michelle",
    "米謝爾": "Michelle", "蜜謝兒": "Michelle",
    # Marian
    "瑪麗安": "Marian", "馬利安": "Marian", "瑪莉安": "Marian",
    "馬莉安": "Marian", "瑪麗": "Marian",
    # Sophia
    "蘇菲亞": "Sophia", "索菲亞": "Sophia", "蘇非亞": "Sophia",
    "蘇菲": "Sophia", "索菲": "Sophia",
    # Will
    "威爾": "Will", "維爾": "Will",
    # Ken
    "肯恩": "Ken", "肯尼": "Ken",
    # 何先生（中文名不易出錯，加常見同音字保險）
    "河先生": "何先生", "賀先生": "何先生",
}

MEMORY_DIR = "meeting_history"
MAX_HISTORY_COUNT = 5
WEB_PORT = 8000
