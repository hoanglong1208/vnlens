from vnlens.utils.lines import merge_wrapped_lines


def test_mid_sentence_wrap_is_joined():
    text = "I've been waiting\nfor you, Senpai."
    assert merge_wrapped_lines(text) == "I've been waiting for you, Senpai."


def test_sentence_breaks_are_kept():
    text = "It was a long night.\nNobody came to the shrine."
    assert merge_wrapped_lines(text) == text


def test_mixed_wrap_and_sentence_break():
    text = "He opened the door\nand stepped inside.\nThe room was dark."
    expected = "He opened the door and stepped inside.\nThe room was dark."
    assert merge_wrapped_lines(text) == expected


def test_question_and_exclamation_end_lines():
    text = "Who are you?\nAnswer me!"
    assert merge_wrapped_lines(text) == text


def test_closing_quote_keeps_break():
    text = '"Wait for me."\nShe ran after him.'
    assert merge_wrapped_lines(text) == text


def test_japanese_wrap_joined_without_space():
    text = "ずっと待って\nいたよ。"
    assert merge_wrapped_lines(text, lang="ja") == "ずっと待っていたよ。"


def test_japanese_sentence_break_kept():
    text = "おはよう。\n元気ですか？"
    assert merge_wrapped_lines(text, lang="ja") == text


def test_blank_lines_dropped():
    text = "Hello.\n\n  \nGoodbye."
    assert merge_wrapped_lines(text) == "Hello.\nGoodbye."


def test_empty_input():
    assert merge_wrapped_lines("") == ""
    assert merge_wrapped_lines("  \n  ") == ""


def test_single_line_unchanged():
    assert merge_wrapped_lines("Just one line") == "Just one line"
