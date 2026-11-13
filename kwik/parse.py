"""Turn raw replies into answers, confidences and abstentions. Every rule here is reported in the paper."""
import re
import unicodedata

_ANSWER_LINE = re.compile(r"^\s*(?:final\s+)?answer\s*[:：]\s*\(?\s*([ABCD])\s*\)?(?![A-Za-z])", re.I | re.M)
_ANSWER = re.compile(r"answer\s*[:：]\s*\(?\s*([ABCD])\s*\)?(?![A-Za-z])", re.I)
_CONF = re.compile(r"confidence\s*[:：]\s*(\d{1,3}(?:\.\d+)?)\s*(%?)", re.I)
_FINAL = re.compile(r"final answer\s*[:：]\s*(.+)", re.I)

# Used only when the model writes a final answer without the ABSTAIN token. Counted separately.
ABSTAIN_PHRASES = [
    "abstain", "i don't know", "i do not know", "cannot be determined", "can't be determined",
    "cannot determine", "not enough information", "insufficient information", "cannot be answered",
    "can't be answered", "unable to determine", "unable to answer", "no such", "does not exist",
    "doesn't exist", "not a real", "fictional", "no information", "unknown", "not possible to determine",
    "cannot be calculated", "missing information", "information is missing", "not specified",
]


def _clean(text: str) -> str:
    return (text or "").replace("*", "").replace("`", "")


def parse_mc(text: str) -> dict:
    """Last 'Answer: X' and last 'Confidence: N' in the visible reply."""
    t = _clean(text)
    a = _ANSWER_LINE.findall(t) or _ANSWER.findall(t)
    c = _CONF.findall(t)
    answer = a[-1].upper() if a else None
    conf = None
    conf_note = None
    if c:
        val, pct = c[-1]
        v = float(val)
        if v <= 1.0 and "." in val and not pct:
            v, conf_note = v * 100, "fraction_scaled"
        if 0 <= v <= 100:
            conf = v
        else:
            conf_note = "out_of_range"
    return {"answer": answer, "confidence": conf, "conf_note": conf_note}


def parse_final(text: str) -> dict:
    """Final answer line, and whether it abstains (ABSTAIN token first, phrase list second)."""
    t = _clean(text).strip()
    m = _FINAL.findall(t)
    final = m[-1].strip() if m else None
    target = (final if final is not None else t[-400:]).lower()
    if "abstain" in target:
        how = "token"
    elif any(p in target for p in ABSTAIN_PHRASES):
        how = "phrase"
    else:
        how = None
    return {"final": final, "abstained": how is not None, "abstain_how": how, "format_ok": final is not None}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def matches_gold(final: str | None, aliases: list[str]) -> bool:
    """Lenient: any gold alias appears as whole words inside the final answer."""
    if not isinstance(final, str) or not final:
        return False
    f = f" {_norm(final)} "
    return any(_norm(a) and f" {_norm(a)} " in f for a in aliases)
