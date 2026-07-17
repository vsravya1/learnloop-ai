"""Assess whether a student reply demonstrates understanding."""

import json

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

DEFAULT_ASSESSMENT = {
    "is_answer_attempt": False,
    "understood": False,
    "correct_this_turn": False,
}

ASSESSMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "is_answer_attempt": {"type": "boolean"},
        "understood": {"type": "boolean"},
        "correct_this_turn": {"type": "boolean"},
    },
    "required": ["is_answer_attempt", "understood", "correct_this_turn"],
    "additionalProperties": False,
}


def assess_response(
    student_reply, original_question, subject, concept, sub_concept, hint_count
):
    """Assess a reply against the current learning concept."""
    instructions = """
You are the LearnLoop assessment agent. Decide whether the student's reply
fully answers the original question after coaching. Be conservative:
correct_this_turn is true only when the reply represents the final answer to the
original question, not merely a correct intermediate calculation or sub-step.
Set is_answer_attempt to false for acknowledgements, greetings, thanks, or social
messages such as "ok" that do not attempt the original question. In that case,
both understood and correct_this_turn must be false.
Return only JSON matching the supplied schema.
"""
    try:
        client = OpenAI()
        response = client.responses.create(
            model="gpt-5.6",
            instructions=instructions,
            input=(
                f"Original question:\n{original_question}\n\n"
                f"Student reply:\n{student_reply}\n\n"
                f"Topic: {subject} > {concept} > {sub_concept}\n"
                f"Coaching turns so far: {hint_count}"
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "student_assessment",
                    "strict": True,
                    "schema": ASSESSMENT_SCHEMA,
                }
            },
        )
        assessment = json.loads(response.output_text)
        if set(assessment) != set(DEFAULT_ASSESSMENT):
            return DEFAULT_ASSESSMENT.copy()
        return assessment
    except (json.JSONDecodeError, TypeError, ValueError):
        return DEFAULT_ASSESSMENT.copy()
