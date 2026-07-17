"""Student-facing teaching agent for LearnLoop."""

import json

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

STRATEGY_GUIDANCE = {
    "hint": "Give a concise hint that helps the student make progress without solving it.",
    "socratic_question": "Ask one focused guiding question. Do not answer the problem directly.",
    "worked_example": "Show a short, similar solved example, then connect it to the student's problem without solving that exact problem.",
    "reveal_next_step": "Give only the immediate next step. Do not provide later steps or the full solution.",
    "full_answer": "Give the complete solution to the original question, explaining the main steps clearly.",
}


def coach_response(
    strategy,
    student_message,
    student_memory,
    original_question=None,
    hint_count=0,
    assessment=None,
):
    """Create the student-facing response chosen by the planner's strategy."""
    if hint_count >= 3:
        strategy = "full_answer"
    strategy_guidance = STRATEGY_GUIDANCE.get(strategy, STRATEGY_GUIDANCE["hint"])
    instructions = f"""
You are LearnLoop, a supportive AI tutor. Respond directly to the student in plain
text using Markdown only when it improves readability. Follow this teaching
strategy exactly: {strategy_guidance}

Keep the response concise, encouraging, and appropriate for the student's level.
Do not mention the planner, strategy labels, JSON, or student memory.
Guide toward the final answer rather than drilling indefinitely into isolated
sub-steps. Give a full solution only when the coaching-turn count is at least 3.
When an assessment is provided and its final-answer result is false, do not praise
or confirm the student's answer. Give one concrete next step that moves directly
toward the final answer; do not repeat the earlier worked example.
"""

    try:
        client = OpenAI()
        response = client.responses.create(
            model="gpt-5.6",
            instructions=instructions,
            input=(
                f"Original question:\n{original_question or student_message}\n\n"
                f"Latest student message:\n{student_message}\n\n"
                f"Completed coaching turns: {hint_count}\n\n"
                f"Assessment of latest reply: {json.dumps(assessment or {}, default=str)}\n\n"
                f"Student memory:\n{json.dumps(student_memory, default=str)}"
            ),
        )
        return response.output_text.strip()
    except (AttributeError, TypeError, ValueError):
        return "Let's take this one step at a time. What have you tried so far?"
