"""Deterministic rules for closing a LearnLoop coaching session."""

from settings import MAX_COACHING_TURNS


FULL_ANSWER_REQUESTS = (
    "full answer",
    "full solution",
    "reveal full",
    "reveal the answer",
    "show the answer",
    "give me the answer",
)

NON_ANSWER_DEFLECTIONS = {
    "i dont know",
    "i don't know",
    "dont know",
    "don't know",
    "not sure",
    "no idea",
    "idk",
    "i give up",
    "help",
}


def requests_full_answer(message):
    """Return true when the learner explicitly asks to stop coaching."""
    normalized = message.lower().strip()
    return any(request in normalized for request in FULL_ANSWER_REQUESTS)


def is_non_answer_deflection(message):
    """Identify a clear non-answer that should trigger a cap reveal directly."""
    normalized = message.lower().strip().strip(".!?")
    return normalized in NON_ANSWER_DEFLECTIONS


def next_turn_action(assessment, hint_count, student_message):
    """Choose the only valid next state for an active question.

    A reply is assessed before this function is called. Vague replies are not
    ignored: they receive another focused step, or the final reveal at the cap.
    """
    if assessment.get("correct_this_turn", False):
        return "solved"
    # A learner receives every permitted coaching turn before the final reveal.
    # For a two-turn cap: hint 1 -> hint 2 -> full reveal if still unresolved.
    if hint_count >= MAX_COACHING_TURNS or requests_full_answer(student_message):
        return "full_reveal"
    return "next_step"
