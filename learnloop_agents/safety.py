"""Minimal local safety screen for clearly non-learning harmful requests."""

SELF_HARM_PHRASES = (
    "kill myself",
    "hurt myself",
    "end my life",
    "suicide plan",
)
EXPLICIT_CONTENT_PHRASES = (
    "send nudes",
    "porn",
    "explicit sexual",
)
VIOLENCE_PHRASES = (
    "how to kill",
    "make a bomb",
    "build a bomb",
    "hurt someone",
    "shoot someone",
)

SAFE_RESPONSE = (
    "I’m sorry you’re dealing with this. I can’t help with that, but if you or "
    "someone is in immediate danger, please contact local emergency services or "
    "a trusted person right now."
)


def safety_response(message):
    """Return a brief safety message for clearly harmful, non-learning content."""
    normalized = message.lower()
    phrases = SELF_HARM_PHRASES + EXPLICIT_CONTENT_PHRASES + VIOLENCE_PHRASES
    return SAFE_RESPONSE if any(phrase in normalized for phrase in phrases) else None
