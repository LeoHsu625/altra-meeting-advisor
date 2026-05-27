import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_ai():
    with patch("ai_client.anthropic.Anthropic") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="建議下一步安排技術拜訪，確認 AVL 認證時程。")]
        mock_instance.messages.create.return_value = mock_response

        from ai_client import AIClient
        yield AIClient()


def test_get_advice_returns_string(mock_ai):
    result = mock_ai.get_advice("G3 計畫討論中，目前卡在第一個案例。")
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_advice_empty_transcript_returns_fallback(mock_ai):
    result = mock_ai.get_advice("")
    assert "尚無內容" in result


def test_get_advice_whitespace_transcript_returns_fallback(mock_ai):
    result = mock_ai.get_advice("   ")
    assert "尚無內容" in result


def test_get_summary_returns_string(mock_ai):
    mock_ai._client.messages.create.return_value.content[0].text = "## 決議事項\n- 下週完成提案"
    result = mock_ai.get_summary("09:00 決定推進 G3，Leo 負責。")
    assert isinstance(result, str)


def test_get_summary_empty_returns_fallback(mock_ai):
    result = mock_ai.get_summary("")
    assert "無會議內容" in result


def test_get_advice_uses_cached_system_prompt(mock_ai):
    mock_ai.get_advice("今天討論 G3 進度。")
    call_kwargs = mock_ai._client.messages.create.call_args.kwargs
    system = call_kwargs["system"]
    assert isinstance(system, list), "system 應為 list（caching 格式）"
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from prompts import CHIEF_OF_STAFF_PROMPT
    assert system[0]["text"] == CHIEF_OF_STAFF_PROMPT


def test_get_summary_uses_cached_system_prompt(mock_ai):
    mock_ai._client.messages.create.return_value.content[0].text = "## 決議事項\n- 無"
    mock_ai.get_summary("今天討論 G3 進度。")
    call_kwargs = mock_ai._client.messages.create.call_args.kwargs
    system = call_kwargs["system"]
    assert isinstance(system, list)
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from prompts import MEETING_SUMMARY_PROMPT
    assert system[0]["text"] == MEETING_SUMMARY_PROMPT


def test_get_advice_with_history_injects_prefill_turns(mock_ai):
    transcript = "今天討論低介電 PI 材料進度。"
    history = "上次決定推進技術驗證，目標 Q2 完成。"
    mock_ai.get_advice(transcript, history=history)
    call_kwargs = mock_ai._client.messages.create.call_args.kwargs
    messages = call_kwargs["messages"]
    assert len(messages) == 3, f"history 非空時 messages 應有 3 個，實際為 {len(messages)}"
    # History message must use list format with cache_control
    assert messages[0]["role"] == "user"
    history_content = messages[0]["content"]
    assert isinstance(history_content, list), "history content 應為 list（含 cache_control）"
    assert history_content[0]["cache_control"] == {"type": "ephemeral"}
    assert f"== 背景：過去會議摘要 ==\n{history}" in history_content[0]["text"]
    assert messages[1] == {
        "role": "assistant",
        "content": "了解，我已掌握過去的會議背景。",
    }
    assert messages[2]["role"] == "user"


def test_get_advice_second_call_uses_cached_transcript(mock_ai):
    t1 = "Leo 說要推進 G3 計畫。"
    t2 = t1 + "\nMichelle 說需要先確認會計師意願。"

    mock_ai.get_advice(t1)
    mock_ai.get_advice(t2)

    call_kwargs = mock_ai._client.messages.create.call_args.kwargs
    messages = call_kwargs["messages"]

    # Second call: cached t1 message + assistant prefill + delta message
    assert len(messages) == 3, f"第二次 F9 應有 3 個 messages，實際為 {len(messages)}"
    cached_msg = messages[0]
    assert cached_msg["role"] == "user"
    assert isinstance(cached_msg["content"], list)
    assert cached_msg["content"][0]["cache_control"] == {"type": "ephemeral"}
    assert t1 in cached_msg["content"][0]["text"]

    delta_msg = messages[2]
    assert delta_msg["role"] == "user"
    assert "Michelle" in delta_msg["content"]


def test_get_advice_no_cache_if_transcript_changed(mock_ai):
    mock_ai.get_advice("第一段逐字稿。")
    # Completely different transcript (e.g. store was reset)
    mock_ai.get_advice("全新的逐字稿，與前次無關。")

    call_kwargs = mock_ai._client.messages.create.call_args.kwargs
    messages = call_kwargs["messages"]
    # Should fall back to single full-transcript message
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert isinstance(messages[0]["content"], str)
    assert "全新的逐字稿" in messages[0]["content"]
