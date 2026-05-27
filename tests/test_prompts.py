from prompts import CHIEF_OF_STAFF_PROMPT, MEETING_SUMMARY_PROMPT


def test_chief_of_staff_prompt_contains_key_concepts():
    assert "幕僚長" in CHIEF_OF_STAFF_PROMPT
    assert "訂單" in CHIEF_OF_STAFF_PROMPT
    assert "停" in CHIEF_OF_STAFF_PROMPT  # Exit Condition 概念，以口語表達


def test_chief_of_staff_prompt_contains_altra_context():
    assert "益瑞" in CHIEF_OF_STAFF_PROMPT
    assert "AVL" in CHIEF_OF_STAFF_PROMPT
    assert "G3" in CHIEF_OF_STAFF_PROMPT


def test_summary_prompt_contains_format():
    assert "決議事項" in MEETING_SUMMARY_PROMPT
    assert "待辦" in MEETING_SUMMARY_PROMPT
    assert "下一步" in MEETING_SUMMARY_PROMPT
