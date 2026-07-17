"""Regular chat responses that stay outside LearnLoop's learning analytics."""

from openai import OpenAI


def regular_chat_response(message, active_question=None):
    """Respond conversationally without creating a tutoring or database event."""
    context = (
        f"The student currently has this open learning question: {active_question}\n\n"
        if active_question
        else ""
    )
    instructions = """
You are LearnLoop in regular conversation mode. Respond warmly and briefly to the
student's casual message. Do not start a lesson, ask a coaching question, create a
worked example, or claim that an answer is correct. If there is an open learning
question, politely say they can continue it whenever they are ready.
"""
    try:
        response = OpenAI().responses.create(
            model="gpt-5.6",
            instructions=instructions,
            input=f"{context}Student message: {message}",
        )
        return response.output_text.strip()
    except (AttributeError, TypeError, ValueError):
        return "Hi! Whenever you're ready, share a learning question and we'll work through it together."
