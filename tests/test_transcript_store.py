import threading
from transcript_store import TranscriptStore


def test_new_store_is_empty():
    store = TranscriptStore()
    assert store.is_empty()
    assert store.get_full_transcript() == ""


def test_append_single_segment():
    store = TranscriptStore()
    store.append("這是第一段發言。")
    assert not store.is_empty()
    assert "這是第一段發言。" in store.get_full_transcript()


def test_append_multiple_segments_preserves_order():
    store = TranscriptStore()
    store.append("第一段。")
    store.append("第二段。")
    transcript = store.get_full_transcript()
    assert transcript.index("第一段") < transcript.index("第二段")


def test_clear_resets_store():
    store = TranscriptStore()
    store.append("有內容了。")
    store.clear()
    assert store.is_empty()
    assert store.get_full_transcript() == ""


def test_empty_string_not_appended():
    store = TranscriptStore()
    store.append("   ")
    assert store.is_empty()


def test_thread_safety_no_crash():
    store = TranscriptStore()

    def append_many():
        for i in range(50):
            store.append(f"段落 {i}")

    threads = [threading.Thread(target=append_many) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not store.is_empty()
