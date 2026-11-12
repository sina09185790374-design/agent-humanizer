"""Two-pass humanizer core.

Pass 1 — strip the tells: run the EN + FA catalogs over the text.
Pass 2 — rebuild toward controlled English (STE80, 80% of the way):
split long multi-idea sentences, break em-dash flourishes into plain
sentences, and rewrite the safe passives (was/were + participle + by)
into active voice.

`check()` scores a text without rewriting it: the same report the CLI
prints, so `humanize()` can show before/after numbers.
"""

import re

from .tells import TELLS

MAX_WORDS = 22          # STE80: one idea per sentence, ~20 words max
GOOD_SCORE = 70         # `check` exit code flips below this

_SENTENCE_END = re.compile(r"(?<=[.!؟])\s+")
_WORD = re.compile(r"\S+")
_FA_CHAR = re.compile(r"[\u0600-\u06FF]")

# Passive: "was written by Sara" / "will be automatically restarted by the kubelet".
# The optional -ly adverb is captured so it can be kept after the verb.
_PASSIVE = re.compile(
    r"\b([\w][\w ]*?)\s+"
    r"(was|were|is|are|will be|would be|can be|could be|should be|has been|have been)"
    r"\s+(?:([a-z]+ly)\s+)?(\w+)\s+by\s+([^.,;]+)",
    re.IGNORECASE,
)

_IRREGULAR = {
    "written": ("write", "wrote"),
    "built": ("build", "built"),
    "made": ("make", "made"),
    "done": ("do", "did"),
    "taken": ("take", "took"),
    "given": ("give", "gave"),
    "sent": ("send", "sent"),
    "chosen": ("choose", "chose"),
    "broken": ("break", "broke"),
    "driven": ("drive", "drove"),
    "found": ("find", "found"),
    "kept": ("keep", "kept"),
    "left": ("leave", "left"),
    "paid": ("pay", "paid"),
    "seen": ("see", "saw"),
    "told": ("tell", "told"),
    "brought": ("bring", "brought"),
    "bought": ("buy", "bought"),
    "caught": ("catch", "caught"),
    "taught": ("teach", "taught"),
    "sold": ("sell", "sold"),
    "spoken": ("speak", "spoke"),
    "held": ("hold", "held"),
    "read": ("read", "read"),
    "set": ("set", "set"),
    "cut": ("cut", "cut"),
}

_PLURAL_SUBJECTS = {"they", "we", "you"}

# Subject pronoun -> object pronoun, for passive -> active rewrites
# ("They are paid by X" -> "X pays them", not "X pays they").
_OBJECT_PRONOUN = {
    "they": "them", "we": "us", "i": "me",
    "he": "him", "she": "her", "it": "it",
}


def detect_lang(text):
    """'fa' when the text carries Persian/Arabic script, else 'en'."""
    return "fa" if _FA_CHAR.search(text) else "en"


def split_sentences(text):
    """Split on sentence terminators, keeping the terminator attached."""
    parts = _SENTENCE_END.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def word_count(text):
    return len(_WORD.findall(text))


def _base_form(participle):
    """Participle -> (base, past). None when it is not a participle."""
    low = participle.lower()
    if low in _IRREGULAR:
        return _IRREGULAR[low]
    if low.endswith("ied"):
        base = low[:-3] + "y"
        return base, base + "ed"
    if low.endswith("ed"):
        if low.endswith("eed"):
            return low[:-1], low
        if len(low) > 3 and low[-3] == "e":
            base = low[:-1]  # created -> create, used -> use
        else:
            base = low[:-2]  # worked -> work
        if len(base) > 2 and base[-1] == base[-2]:
            base = base[:-1]  # stopped -> stop
        return base, base + "ed"
    if low.endswith("en"):
        return None
    return None


def _third_person(base):
    """Base verb -> 3rd-person singular present (pays, watches, tries)."""
    if base.endswith(("s", "x", "z", "ch", "sh")):
        return base + "es"
    if len(base) > 1 and base.endswith("y") and base[-2] not in "aeiou":
        return base[:-1] + "ies"
    return base + "s"


def _passive_rewrite(match):
    """Rewrite one passive match to active voice, or leave it alone.

    Past passives (was/were) always rewrite: the past tense is
    deterministic. Present passives rewrite only for plural subjects
    ("they are paid by ..."), where the base form is unambiguous.
    Anything else is left for the report to flag, not silently mangled.
    """
    subject, aux, adverb, participle, agent = match.groups()
    forms = _base_form(participle)
    if forms is None:
        return match.group(0)
    base, past = forms
    agent = agent.strip()
    # Only rewrite when the by-phrase is a short agent at the end of the
    # sentence; anything longer ("by the company every month") would put
    # the adverbial in the wrong place.
    if len(agent.split()) > 3:
        return match.group(0)
    aux = aux.lower()
    if aux in ("was", "were"):
        verb = past
    elif aux in ("is", "are"):
        subj = subject.strip().lower()
        if subj in _PLURAL_SUBJECTS or subj.endswith("s"):
            verb = base
        else:
            return match.group(0)
        # Present tense: conjugate the verb for the new subject (the agent).
        agent_low = agent.lower()
        if agent_low in _PLURAL_SUBJECTS or agent_low.endswith("s"):
            verb = base
        else:
            verb = _third_person(base)
    elif aux in ("will be", "would be", "can be", "could be", "should be"):
        verb = aux.split()[0] + " " + base
    elif aux in ("has been", "have been"):
        verb = aux.split()[0] + " " + past
    else:
        return match.group(0)
    subject_out = _OBJECT_PRONOUN.get(subject.strip().lower(),
                                      subject.strip().lower())
    tail = f" {adverb}" if adverb else ""
    return f"{agent} {verb} {subject_out}{tail}"


def _capitalize_sentences(text):
    """Capitalize the first letter of every sentence (Latin script only)."""
    def cap(match):
        return match.group(1) + match.group(2).upper()

    return re.sub(r"(^|[.!؟]\s+)([a-z])", cap, text)


def _split_long_sentence(sentence):
    """Split one over-long sentence at conjunctions, recursively."""
    if word_count(sentence) <= MAX_WORDS:
        return [sentence]
    # Semicolons and em-dashes are the cleanest breaks.
    for sep, joiner in [("; ", ". "), (" — ", ". "), (" – ", ". ")]:
        if sep in sentence:
            left, right = sentence.split(sep, 1)
            if word_count(left) >= 3 and word_count(right) >= 3:
                left = left.strip()
                if left and left[-1].isalnum():
                    left += "."
                return _split_long_sentence(left) + _split_long_sentence(
                    right.strip()
                )
    # Then coordinating conjunctions, with or without a comma.
    for conj in [", and ", ", but ", ", so ", ", because ", " and ", " but ",
                 " so ", " because "]:
        if conj in sentence:
            left, right = sentence.split(conj, 1)
            if word_count(left) >= 4 and word_count(right) >= 4:
                left = left.strip()
                if left and left[-1].isalnum():
                    left += "."
                return _split_long_sentence(left) + _split_long_sentence(
                    right.strip()
                )
    return [sentence]


def _fix_spacing(text):
    text = re.sub(r"\s+([,.!؟:;])", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _strip_tells(text):
    """Pass 1. Returns (text, [matched tell strings])."""
    found = []
    for pattern, repl, _lang in TELLS:
        found.extend(m.group(0) for m in pattern.finditer(text))
        text = pattern.sub(repl, text)
    return _fix_spacing(text), found


def _count_passives(text):
    return len(_PASSIVE.findall(text))


def _count_hedges(text):
    return len(re.findall(r"\b(could|may|might|perhaps|possibly|potentially)\b",
                          text, re.IGNORECASE))


def check(text):
    """Score a text without rewriting it."""
    sentences = split_sentences(text)
    words = word_count(text)
    long_sentences = sum(1 for s in sentences if word_count(s) > MAX_WORDS)
    _, tells = _strip_tells(text)
    passives = _count_passives(text)
    hedges = _count_hedges(text)
    avg = round(words / max(len(sentences), 1), 1)
    score = max(0, 100 - 4 * min(len(tells), 10) - 3 * long_sentences
                - 2 * passives - hedges - (2 if avg > MAX_WORDS else 0))
    return {
        "words": words,
        "sentences": len(sentences),
        "avg_words_per_sentence": avg,
        "long_sentences": long_sentences,
        "tell_hits": sorted(set(t.lower() for t in tells)),
        "tell_count": len(tells),
        "passives": passives,
        "hedges": hedges,
        "score": score,
    }


def humanize(text):
    """Two-pass rewrite. Returns (rewritten_text, before, after)."""
    before = check(text)
    text, _ = _strip_tells(text)
    # Em-dash flourish -> plain sentence break, when both sides stand alone.
    text = re.sub(r"\s+—\s+", ". ", text)
    text = _PASSIVE.sub(_passive_rewrite, text)
    sentences = split_sentences(text)
    rebuilt = []
    for sentence in sentences:
        rebuilt.extend(_split_long_sentence(sentence))
    text = " ".join(rebuilt)
    text = _fix_spacing(text)
    text = _capitalize_sentences(text)
    if text and text[-1].isalnum():
        text += "."
    after = check(text)
    return text, before, after
