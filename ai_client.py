import os
import anthropic
from prompts import CHIEF_OF_STAFF_PROMPT, MEETING_SUMMARY_PROMPT


class AIClient:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self._model = "claude-sonnet-4-6"
        self._cached_transcript: str = ""
        self._cached_response: str = ""

    def get_advice(self, transcript: str, history: str = "") -> str:
        if not transcript or not transcript.strip():
            return "目前逐字稿尚無內容，請稍後再試。"

        messages = []

        # History context — cached across all F9 calls in this session
        if history:
            messages.append({
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": f"== 背景：過去會議摘要 ==\n{history}",
                    "cache_control": {"type": "ephemeral"},
                }],
            })
            messages.append({
                "role": "assistant",
                "content": "了解，我已掌握過去的會議背景。",
            })

        # If transcript grew since last F9, replay cached portion + delta only
        if self._cached_transcript and transcript.startswith(self._cached_transcript):
            messages.append({
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": f"以下是今天會議的逐字稿（前段）：\n\n{self._cached_transcript}",
                    "cache_control": {"type": "ephemeral"},
                }],
            })
            messages.append({
                "role": "assistant",
                "content": self._cached_response,
            })
            delta = transcript[len(self._cached_transcript):]
            messages.append({
                "role": "user",
                "content": (
                    f"會議繼續進行，新增對話如下：\n\n{delta}\n\n"
                    "請就當前討論給出你的策略建議。"
                ),
            })
        else:
            # First F9 call, or transcript was reset
            messages.append({
                "role": "user",
                "content": (
                    f"以下是今天會議的完整逐字稿：\n\n{transcript}\n\n"
                    "請就當前討論給出你的策略建議。"
                ),
            })

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=[{
                "type": "text",
                "text": CHIEF_OF_STAFF_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=messages,
        )

        result = response.content[0].text

        # Log cache performance
        usage = response.usage
        cache_read = getattr(usage, "cache_read_input_tokens", 0)
        cache_write = getattr(usage, "cache_creation_input_tokens", 0)
        billed = usage.input_tokens
        if cache_read or cache_write:
            print(
                f"[Token] 讀取快取={cache_read} | 寫入快取={cache_write} | 新計費={billed}"
            )

        # Update cache for next F9 call
        self._cached_transcript = transcript
        self._cached_response = result
        return result

    def get_summary(self, transcript: str) -> str:
        if not transcript or not transcript.strip():
            return "無會議內容可供摘要。"
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=[{
                "type": "text",
                "text": MEETING_SUMMARY_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{
                "role": "user",
                "content": f"會議逐字稿：\n\n{transcript}",
            }],
        )
        return response.content[0].text
