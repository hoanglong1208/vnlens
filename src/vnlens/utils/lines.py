# Characters that mark a line as deliberately ended; a break after them is kept.
# Covers Latin and CJK sentence punctuation plus closing quotes.
_SENTENCE_END = tuple('.!?…:"’”」』。！？')


def merge_wrapped_lines(text: str, lang: str = "auto") -> str:
    """Collapse soft line wraps in OCR output while keeping intentional breaks.

    Game text boxes wrap long sentences mid-way; translating those fragments
    separately ruins quality. A line ending without sentence punctuation is
    treated as a wrap and joined to the next line; anything else keeps its
    break so the structure survives translation.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""

    separator = "" if lang == "ja" else " "
    merged = [lines[0]]
    for line in lines[1:]:
        if merged[-1].endswith(_SENTENCE_END):
            merged.append(line)
        else:
            merged[-1] = merged[-1] + separator + line
    return "\n".join(merged)
