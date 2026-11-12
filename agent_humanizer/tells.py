"""Tell catalogs: the AI-writing fingerprints the humanizer removes.

Two catalogs, English and Persian. Each entry is (pattern, replacement).
Replacement "" means "delete the phrase". Patterns are matched
case-insensitively with word boundaries where the language allows it.

The English list is the working set from Wikipedia's "Signs of AI
writing" tradition (the 26-tell catalog behind ste80-humanizer) plus the
hedges and filler openers every AI draft leans on. The Persian list is
the same idea for Persian copy: the stock openers and superlatives that
mark a text as machine-written in a shop caption or a blog post.

Pattern only — every rule here is original wording of the rule itself.
"""

import re

# (regex source, replacement) — EN
EN_TELLS = [
    # Filler openers: delete the whole opener, keep the sentence.
    (r"in today'?s fast-paced world,?\s*", ""),
    (r"in today'?s digital age,?\s*", ""),
    (r"in the ever-evolving world of\s+", "in "),
    (r"in the ever-evolving landscape of\s+", "in "),
    (r"it'?s important to note that\s+", ""),
    (r"it is important to note that\s+", ""),
    (r"it should be noted that\s+", ""),
    (r"it'?s worth noting that\s+", ""),
    (r"needless to say,?\s*", ""),
    (r"at the end of the day,?\s*", ""),
    (r"in a nutshell,?\s*", ""),
    (r"the fact of the matter is (that\s+)?", ""),
    (r"great question!?\s*", ""),
    (r"in conclusion,?\s*", ""),
    (r"to sum up,?\s*", ""),
    (r"as an ai language model,?\s*", ""),
    # Hedges and filler verbs.
    (r"\bcould potentially\b", "could"),
    (r"\bmay possibly\b", "may"),
    (r"\bmight possibly\b", "might"),
    (r"\bdue to the fact that\b", "because"),
    (r"\bin light of the fact that\b", "because"),
    (r"\bin order to\b", "to"),
    # "not only X but also Y" -> "X and Y" (paired rule runs first).
    (r"not only\s+(.+?)\s+but also\s+", r"\1 and "),
    (r"\bnot only\b", ""),
    (r"\bbut also\b", "and"),
    (r"\bfirst and foremost\b", "first"),
    (r"\bvery unique\b", "unique"),
    # Stock AI verbs and adjectives -> plain words.
    (r"\bdelve into\b", "look at"),
    (r"\bdelve\b", "explore"),
    (r"\bdive into\b", "look at"),
    (r"\bembark on\b", "start"),
    (r"\bleverage\b", "use"),
    (r"\butilize\b", "use"),
    (r"\bfacilitate\b", "help"),
    (r"\bharness\b", "use"),
    (r"\belevate\b", "raise"),
    (r"\bunlock\b", "open"),
    (r"\bsupercharge\b", "speed up"),
    (r"\bboasts\b", "has"),
    (r"\bspearhead\w*\b", "lead"),
    (r"\bmoreover\b", ""),
    (r"\bfurthermore\b", ""),
    (r"\badditionally\b", "also"),
    (r"\bwhen it comes to\b", "for"),
    (r"\bin the realm of\b", "in"),
    (r"\ba testament to\b", "proof of"),
    (r"\bcutting-edge\b", "new"),
    (r"\bstate-of-the-art\b", "latest"),
    (r"\bgame-changer\b", "big change"),
    (r"\bseamless\b", "smooth"),
    (r"\bcrucial\b", "key"),
    (r"\bvital\b", "key"),
    (r"\bpivotal\b", "key"),
    (r"\bparadigm\b", "model"),
    (r"\bholistic\b", "whole"),
    (r"\bsynergy\b", "teamwork"),
    (r"\brobust\b", "strong"),
    (r"\bnestled\b", "in"),
    (r"\btapestry\b", "mix"),
    (r"\bthe ai landscape\b", "the AI field"),
    (r"\ba wide range of\b", "many"),
]

# Intensifiers dropped outright (STE80: one idea, no decoration).
EN_INTENSIFIERS = [r"\bvery\b", r"\breally\b"]

# (regex source, replacement) — FA
FA_TELLS = [
    (r"در دنیای پرسرعت امروز،?\s*", ""),
    (r"در دنیای امروز،?\s*", ""),
    (r"در عصر دیجیتال،?\s*", ""),
    (r"لازم به ذکر است که\s*", ""),
    (r"شایان ذکر است که\s*", ""),
    (r"مهم است بدانید که\s*", ""),
    (r"توجه داشته باشید که\s*", ""),
    (r"ناگفته نماند که\s*", ""),
    (r"به عبارت دیگر،?\s*", ""),
    (r"در یک کلام،?\s*", ""),
    (r"به طور خلاصه،?\s*", ""),
    (r"به طور کلی،?\s*", ""),
    (r"در نتیجه،?\s*", ""),
    (r"در پایان،?\s*", ""),
    (r"در واقع،?\s*", ""),
    (r"بدون شک،?\s*", ""),
    (r"به عنوان\s+", ""),
    (r"بی‌نظیر", "خوب"),
    (r"فوق‌العاده", "خوب"),
    (r"جادویی", ""),
    (r"انقلابی", "جدید"),
    (r"شگفت‌انگیز", "خوب"),
]


def compile_tells():
    """Compile every catalog entry to (regex, replacement, label)."""
    compiled = []
    for source, repl in EN_TELLS:
        compiled.append((re.compile(source, re.IGNORECASE), repl, "en"))
    for source in EN_INTENSIFIERS:
        compiled.append((re.compile(source, re.IGNORECASE), "", "en"))
    for source, repl in FA_TELLS:
        compiled.append((re.compile(source), repl, "fa"))
    return compiled


TELLS = compile_tells()
