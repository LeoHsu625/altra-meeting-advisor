"""
手動準確度測試腳本
執行方式：python3 tests/test_transcription_accuracy.py
每句話會錄音 8 秒，念完後等待轉錄結果，逐句比對。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyaudio, wave, tempfile, os, time

TEST_SENTENCES = [
    "我們討論一下 G3 計畫目前的進度",
    "AVL 認證還沒過，客戶說要等 HDI 驗證完才能決定",
    "這個 PCB 材料在 5G 跟 AI Server 的市場有機會",
    "下週三下午兩點開會，預計討論三個議題",
    "我們的 Dk 值是 2.9，比 LCP 的優勢在加工性",
]

RECORD_SECONDS = 8


def record_audio(seconds: int) -> str:
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                    input=True, frames_per_buffer=1024)
    frames = []
    for i in range(int(16000 / 1024 * seconds)):
        frames.append(stream.read(1024, exception_on_overflow=False))
    stream.stop_stream()
    stream.close()
    p.terminate()

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"".join(frames))
    return tmp.name


def main():
    from transcriber import transcribe

    print("=" * 60)
    print("  語音轉文字準確度測試")
    print("  每句錄音 8 秒，請清楚念出提示的句子")
    print("=" * 60)

    results = []

    for i, sentence in enumerate(TEST_SENTENCES):
        print(f"\n【第 {i+1}/{len(TEST_SENTENCES)} 句】")
        print(f"  請念：「{sentence}」")
        print()
        input("  按 Enter 開始錄音...")

        print(f"  🎙  錄音中（{RECORD_SECONDS} 秒）...")
        audio_file = record_audio(RECORD_SECONDS)

        print("  ⏳ 轉錄中...")
        result = transcribe(audio_file)

        print(f"\n  ✏️  原文：{sentence}")
        print(f"  🔤  轉錄：{result if result else '（空白）'}")

        match = input("\n  準確嗎？(y/n/p 部分正確) ").strip().lower()
        results.append({
            "expected": sentence,
            "got": result,
            "match": match
        })

    print("\n" + "=" * 60)
    print("  測試結果摘要")
    print("=" * 60)
    for i, r in enumerate(results):
        icon = "✅" if r["match"] == "y" else ("⚠️" if r["match"] == "p" else "❌")
        print(f"  {icon} 第 {i+1} 句：{r['expected'][:25]}...")
        if r["match"] != "y":
            print(f"       轉錄結果：{r['got']}")

    correct = sum(1 for r in results if r["match"] == "y")
    partial = sum(1 for r in results if r["match"] == "p")
    print(f"\n  準確：{correct}/5  部分：{partial}/5  錯誤：{5-correct-partial}/5")

    if correct < 3:
        print("\n  ⚠️  準確度偏低，建議調整設定（見下方說明）")
    else:
        print("\n  ✅  準確度可接受，可繼續下一個任務")


if __name__ == "__main__":
    main()
