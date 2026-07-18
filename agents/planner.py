"""Planning agent for selecting a safe tutoring response strategy."""

import json

from dotenv import load_dotenv
from openai import OpenAI
from agents.runtime import run_with_timeout


load_dotenv()

DEFAULT_PLAN = {
    "subject": "Other",
    "concept": "Other",
    "sub_concept": "Other",
    "intent": "other",
    "difficulty": "medium",
    "is_repeat_struggle": False,
    "strategy": "hint",
    "requires_coaching": True,
    "starts_new_question": False,
}

CASUAL_MESSAGES = {
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "thanks", "thank you", "ok", "okay", "cool", "great", "got it",
}

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "concept": {"type": "string"},
        "sub_concept": {"type": "string"},
        "intent": {
            "type": "string",
            "enum": ["homework", "essay", "coding", "conceptual_question", "other"],
        },
        "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
        "is_repeat_struggle": {"type": "boolean"},
        "requires_coaching": {"type": "boolean"},
        "starts_new_question": {"type": "boolean"},
        "strategy": {
            "type": "string",
            "enum": [
                "hint",
                "socratic_question",
                "worked_example",
                "reveal_next_step",
            ],
        },
    },
    "required": [
        "subject",
        "concept",
        "sub_concept",
        "intent",
        "difficulty",
        "is_repeat_struggle",
        "strategy",
        "requires_coaching",
        "starts_new_question",
    ],
    "additionalProperties": False,
}

PLANNER_INSTRUCTIONS = """
You are the LearnLoop planning agent. Classify the student's request and choose
one teaching strategy. Prefer guiding the student with a hint, Socratic question,
worked example, or next step. Never provide or choose a full answer. Classify every
question with a concise subject, concept, and sub_concept. Use consistent Title Case
labels; for example, an essay question can be English > Writing > Essay Writing.
Reuse the same label for equivalent topics whenever possible. Return only the JSON
object that matches the supplied schema. Set is_repeat_struggle to true only when
the supplied student memory contains prior evidence that the student is struggling
with the same topic. If the memory has no prior conversations or mastery records,
it must be false.
Set requires_coaching to true only for a genuine learning request: a problem to
solve, a concept to understand, a writing/coding task, or a request for help
learning. Set it to false for greetings, thanks, acknowledgements such as "ok",
small talk, or other casual conversation. When false, use intent "other" and a
general conversation classification; the strategy is ignored.
When an active question is supplied, set starts_new_question to true only if the
student message introduces a distinct learning task or topic. Set it to false for
an answer attempt, a request about the active question, or casual conversation.
"""


def plan_response(student_message, student_memory, active_question=None):
    """Return a structured tutoring plan, falling back to a hint when needed."""
    if student_message.strip().lower().strip(".!?") in CASUAL_MESSAGES:
        casual_plan = DEFAULT_PLAN.copy()
        casual_plan.update(
            {
                "subject": "General",
                "concept": "Conversation",
                "sub_concept": "Casual Chat",
                "requires_coaching": False,
            }
        )
        return casual_plan
    is_fresh_learner = not student_memory.get("mastery") and not student_memory.get(
        "recent_conversations"
    )
    try:
        client = OpenAI(timeout=20.0, max_retries=0)
        response = run_with_timeout(
            lambda: client.responses.create(
                model="gpt-5.6",
                instructions=PLANNER_INSTRUCTIONS,
                input=(
                    f"Student message:\n{student_message}\n\n"
                    f"Active question (if any):\n{active_question or 'None'}\n\n"
                    f"Student memory:\n{json.dumps(student_memory, default=str)}"
                ),
            )
        )
        if response is None:
            return DEFAULT_PLAN.copy()
        plan = json.loads((response.output_text or "").strip().removeprefix("```json").removesuffix("```").strip())
        if set(plan) != set(DEFAULT_PLAN):
            return DEFAULT_PLAN.copy()
        if is_fresh_learner:
            plan["is_repeat_struggle"] = False
        return plan
    except Exception as error:
        print(f"Planner response failed: {error}")
        return DEFAULT_PLAN.copy()
