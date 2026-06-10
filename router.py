import re
from config import MODEL_HAIKU, MODEL_SONNET, MODEL_FABLE
from budget import is_deep_allowed, is_sonnet_allowed

FABLE_PREFIXES = ["/deep", "/plan", "/research", "/analyze", "/fable"]

HAIKU_PATTERNS = [
    r"(τι|what).{0,20}(calendar|ημερολόγιο|event|meeting|ραντεβού|γεγονός)",
    r"(τι ώρα|πότε|when).{0,30}(event|meeting|αύριο|σήμερα|tomorrow|today)",
    r"\b(υπενθύμισε|remind|reminder)\b",
    r"\b(γρήγορα|quick|σύντομα|briefly)\b",
    r"^(ναι|όχι|οκ|ok|yes|no|thanks|ευχαριστώ)[\.\!]?$",
    r"(πόσο|how much).{0,20}(κοστίζει|costs|budget|credits)",
    r"^/status$",
    r"^/budget$",
]


def _matches_haiku(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in HAIKU_PATTERNS)


def route(message: str) -> tuple[str, str]:
    text = message.strip()

    for prefix in FABLE_PREFIXES:
        if text.lower().startswith(prefix):
            if not is_deep_allowed():
                if is_sonnet_allowed():
                    return MODEL_SONNET, "budget critical — downgraded from fable5 to sonnet"
                return MODEL_HAIKU, "budget lockdown — downgraded to haiku"
            return MODEL_FABLE, f"explicit {prefix} trigger"

    if not is_sonnet_allowed():
        return MODEL_HAIKU, "budget lockdown — haiku only"

    if _matches_haiku(text):
        return MODEL_HAIKU, "haiku pattern match (quick/calendar task)"

    return MODEL_SONNET, "default"
