"""LearnLoop chat UI with transparent, question-level agent activity."""

from pathlib import Path
from uuid import uuid4

import streamlit as st

from agents.assessor import assess_response
from agents.chat import regular_chat_response
from agents.coach import coach_response
from agents.planner import plan_response
from db.db import (
    get_student_memory,
    init_db,
    log_agent_decision,
    log_conversation,
    update_mastery,
)
from ui import inject_product_css


init_db()
st.set_page_config(
    page_title="Chat | LearnLoop",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_product_css()

ASSETS_DIR = Path(__file__).with_name("assets")
GREETING_MESSAGES = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}


def get_avatar(role):
    """Use an optional local avatar, or Streamlit's default when none exists."""
    filename = "student-avatar.png" if role == "user" else "learnloop-avatar.png"
    avatar_path = ASSETS_DIR / filename
    return str(avatar_path) if avatar_path.exists() else None


def make_excerpt(text, word_limit=10):
    words = text.split()
    return " ".join(words[:word_limit]) + ("..." if len(words) > word_limit else "")


def activity_details(plan, hint_count, strategy=None, assessment=None, outcome=None):
    return {
        "intent": plan["intent"],
        "difficulty": plan["difficulty"],
        "strategy": strategy or plan["strategy"],
        "subject": plan["subject"],
        "concept": plan["concept"],
        "sub_concept": plan["sub_concept"],
        "hint_count": hint_count,
        "assessment": assessment,
        "outcome": outcome,
    }


def close_active_question_as_skipped(plan, question_id, question_text, hint_count):
    """Close an abandoned coaching session before starting a distinct question."""
    log_agent_decision(
        st.session_state.student_id,
        plan["subject"], plan["concept"], plan["sub_concept"],
        plan["intent"], plan["difficulty"], plan["strategy"], plan["is_repeat_struggle"],
        note="Student started a distinct new learning question before completing this one.",
        event_type="question_closed", hint_count=hint_count,
        question_id=question_id, question_text=question_text,
        outcome="skipped",
    )


def start_coaching_session(plan, student_message, student_memory):
    """Open and log a genuine new learning question."""
    question_id = uuid4().hex
    log_agent_decision(
        st.session_state.student_id,
        plan["subject"], plan["concept"], plan["sub_concept"],
        plan["intent"], plan["difficulty"], plan["strategy"], plan["is_repeat_struggle"],
        event_type="question_plan", question_id=question_id,
        question_text=student_message, turn_number=0,
    )
    with st.spinner("Preparing your response..."):
        reply = coach_response(plan["strategy"], student_message, student_memory, student_message)
    log_agent_decision(
        st.session_state.student_id,
        plan["subject"], plan["concept"], plan["sub_concept"],
        plan["intent"], plan["difficulty"], plan["strategy"], plan["is_repeat_struggle"],
        event_type="coach_turn", hint_count=1, question_id=question_id,
        question_text=student_message, turn_number=1, coach_excerpt=make_excerpt(reply),
    )
    st.session_state.active_question = student_message
    st.session_state.active_plan = plan
    st.session_state.hint_count = 1
    st.session_state.active_question_id = question_id
    return reply, activity_details(plan, 1)


def show_activity(details):
    """Show the recorded planner, assessor, and coach actions for this turn."""
    with st.expander("See agent activity", expanded=False):
        st.write("**Planner**")
        st.write(f"Intent: {details['intent']} | Difficulty: {details['difficulty']}")
        st.write(f"Strategy selected: {details['strategy']}")
        st.write(
            "Topic: "
            f"{details['subject']} > {details['concept']} > {details['sub_concept']}"
        )
        if details.get("assessment"):
            assessment = details["assessment"]
            st.write("**Assessor**")
            st.write(
                "Understood: "
                f"{'yes' if assessment['understood'] else 'no'} | Final answer correct: "
                f"{'yes' if assessment['correct_this_turn'] else 'no'}"
            )
        st.write("**Coach**")
        st.write(f"Response strategy: {details['strategy']} | Coaching turn: {details['hint_count']}")
        if details.get("outcome"):
            st.write(f"Outcome: {details['outcome']}")


st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        [data-testid="stAppViewContainer"] { background: #fcfcfe; }
        [data-testid="stMainBlockContainer"], section.main > div.block-container, main .block-container {
            max-width: 1200px !important; margin-left: auto !important; margin-right: auto !important;
            padding-top: 2.5rem; padding-bottom: 7rem;
        }
        h1 { font-size: 1.6rem !important; font-weight: 600 !important; letter-spacing: -0.03em; margin-bottom: 2rem !important; }
        [data-testid="stSidebar"] { background: #f7f6fb; border-right: 1px solid #e8e6f0; }
        [data-testid="stSidebar"] .block-container { padding: 1.35rem 1rem 1.75rem; }
        [data-testid="stSidebar"] h2 { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #6b6b6b; }
        [data-testid="stChatMessage"] {
            background: #ffffff !important;
            border: 1px solid #eceaf3;
            border-radius: 1rem;
            box-shadow: 0 3px 14px rgba(35, 29, 75, 0.06);
            padding: 1rem 1.1rem;
            margin: 0.8rem 0;
            gap: 0.85rem;
        }
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
            background: #f0effb !important;
            border-color: #e2def6;
        }
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
            background: #ffffff !important;
        }
        [data-testid="stChatMessage"] p { font-size: 1.04rem; line-height: 1.65; }
        [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { max-width: 1200px !important; margin-left: auto !important; margin-right: auto !important; }
        [data-testid="stChatInput"] { width: 1000px !important; max-width: 1000px; margin: 0 auto; }
        [data-testid="stChatInput"] textarea { border-radius: 1.1rem; border: 1px solid #dcd9eb; box-shadow: 0 3px 14px rgba(35, 29, 75, 0.08); padding: 0.75rem 1rem; }
        [data-testid="stSidebar"] button { width: 100%; border-radius: 0.55rem; border-color: #ddd9eb; }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: #ebe8fb;
            color: #4f3fa7;
            font-weight: 600;
            border-radius: 0.5rem;
        }
        .learnloop-welcome { color: #6b6b6b; font-size: 1.15rem; font-weight: 500; text-align: center; padding: 8rem 0 1rem; }
        .coaching-step { color: #5f52b7; font-size: 0.9rem; font-weight: 600; padding: 0.45rem 0; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("LearnLoop")

for key, value in {
    "student_id": "", "messages": [], "active_question": None,
    "active_plan": None, "hint_count": 0, "active_question_id": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

with st.sidebar:
    st.header("Student")
    st.write(f"Current student ID: `{st.session_state.student_id or 'Not set'}`")
    if st.button("Reset conversation"):
        st.session_state.messages = []
        st.session_state.active_question = None
        st.session_state.active_plan = None
        st.session_state.hint_count = 0
        st.session_state.active_question_id = None
        st.rerun()

if not st.session_state.student_id:
    student_id = st.text_input("Student name or ID", placeholder="e.g. alex-001")
    if st.button("Start learning") and student_id.strip():
        st.session_state.student_id = student_id.strip()
        st.rerun()
    st.stop()

if not st.session_state.messages:
    st.markdown('<div class="learnloop-welcome">How can I help you learn today?</div>', unsafe_allow_html=True)

for chat_message in st.session_state.messages:
    with st.chat_message(chat_message["role"], avatar=get_avatar(chat_message["role"])):
        st.markdown(chat_message["content"])
        if chat_message.get("agent_activity"):
            show_activity(chat_message["agent_activity"])

if st.session_state.active_question:
    progress_column, action_column = st.columns([5, 1])
    with progress_column:
        current_step = min(st.session_state.hint_count, 3)
        st.markdown(
            f'<div class="coaching-step">Coaching step {current_step} of 3</div>',
            unsafe_allow_html=True,
        )
    with action_column:
        if st.button("New question", use_container_width=True):
            close_active_question_as_skipped(
                st.session_state.active_plan,
                st.session_state.active_question_id,
                st.session_state.active_question,
                st.session_state.hint_count,
            )
            st.session_state.active_question = None
            st.session_state.active_plan = None
            st.session_state.hint_count = 0
            st.session_state.active_question_id = None
            st.rerun()

if message := st.chat_input("Ask LearnLoop anything"):
    st.session_state.messages.append({"role": "user", "content": message})
    student_memory = get_student_memory(st.session_state.student_id)
    should_log_interaction = False

    with st.chat_message("user", avatar=get_avatar("user")):
        st.markdown(message)

    with st.chat_message("assistant", avatar=get_avatar("assistant")):
        if st.session_state.active_question and st.session_state.active_plan:
            plan = st.session_state.active_plan
            question_id = st.session_state.active_question_id
            original_question = st.session_state.active_question
            current_hint_count = st.session_state.hint_count

            with st.spinner("Understanding your message..."):
                incoming_plan = plan_response(message, student_memory, original_question)

            if not incoming_plan["requires_coaching"]:
                if message.strip().lower().strip(".!?") in GREETING_MESSAGES:
                    close_active_question_as_skipped(
                        plan, question_id, original_question, current_hint_count
                    )
                    st.session_state.active_question = None
                    st.session_state.active_plan = None
                    st.session_state.hint_count = 0
                    st.session_state.active_question_id = None
                reply = regular_chat_response(message, original_question)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()

            if incoming_plan["starts_new_question"]:
                close_active_question_as_skipped(
                    plan, question_id, original_question, current_hint_count
                )
                reply, reply_activity = start_coaching_session(
                    incoming_plan, message, student_memory
                )
                st.markdown(reply)
                show_activity(reply_activity)
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply, "agent_activity": reply_activity}
                )
                log_conversation(st.session_state.student_id, "user", message)
                log_conversation(st.session_state.student_id, "assistant", reply)
                st.rerun()

            with st.spinner("Checking your response..."):
                assessment = assess_response(message, original_question, plan["subject"], plan["concept"], plan["sub_concept"], current_hint_count)

            score_delta = 0.0
            if assessment["is_answer_attempt"] and assessment["correct_this_turn"]:
                score_delta = 0.3 if current_hint_count == 1 else (0.15 if current_hint_count <= 3 else 0.05)
            if assessment["is_answer_attempt"]:
                should_log_interaction = True
                update_mastery(st.session_state.student_id, plan["subject"], plan["concept"], plan["sub_concept"], score_delta)
                log_agent_decision(
                    st.session_state.student_id, plan["subject"], plan["concept"], plan["sub_concept"],
                    plan["intent"], plan["difficulty"], plan["strategy"], plan["is_repeat_struggle"],
                    event_type="assessment", hint_count=current_hint_count, question_id=question_id,
                    question_text=original_question, assessor_understood=assessment["understood"],
                    assessor_correct=assessment["correct_this_turn"],
                    outcome="solved_independently" if assessment["correct_this_turn"] else None,
                )

            if not assessment["is_answer_attempt"]:
                reply = regular_chat_response(message, original_question)
                reply_activity = None
            elif assessment["correct_this_turn"]:
                reply = "Nice work — that shows you understand it. Send your next question when you're ready."
                reply_activity = activity_details(
                    plan, current_hint_count, assessment=assessment,
                    outcome="solved independently",
                )
                st.session_state.active_question = None
                st.session_state.active_plan = None
                st.session_state.hint_count = 0
                st.session_state.active_question_id = None
            elif current_hint_count >= 3:
                with st.spinner("Showing the complete solution..."):
                    reply = coach_response("full_answer", message, student_memory, original_question, current_hint_count)
                log_agent_decision(
                    st.session_state.student_id, plan["subject"], plan["concept"], plan["sub_concept"],
                    plan["intent"], plan["difficulty"], "full_answer", plan["is_repeat_struggle"],
                    note="Coaching limit reached; full solution revealed before independent completion.",
                    event_type="full_reveal", hint_count=current_hint_count, question_id=question_id,
                    question_text=original_question, coach_excerpt=make_excerpt(reply),
                    assessor_understood=assessment["understood"], assessor_correct=assessment["correct_this_turn"],
                    outcome="needed_full_reveal",
                )
                reply_activity = activity_details(
                    plan, current_hint_count, "full_answer", assessment,
                    "needed full reveal",
                )
                st.session_state.active_question = None
                st.session_state.active_plan = None
                st.session_state.hint_count = 0
                st.session_state.active_question_id = None
            else:
                with st.spinner("Preparing your next coaching step..."):
                    next_strategy = "reveal_next_step"
                    reply = coach_response(
                        next_strategy,
                        message,
                        student_memory,
                        original_question,
                        current_hint_count,
                        assessment,
                    )
                next_turn = current_hint_count + 1
                log_agent_decision(
                    st.session_state.student_id, plan["subject"], plan["concept"], plan["sub_concept"],
                    plan["intent"], plan["difficulty"], next_strategy, plan["is_repeat_struggle"],
                    event_type="coach_turn", hint_count=next_turn, question_id=question_id,
                    question_text=original_question, turn_number=next_turn, coach_excerpt=make_excerpt(reply),
                )
                st.session_state.hint_count = next_turn
                reply_activity = activity_details(plan, next_turn, next_strategy, assessment)
        else:
            with st.spinner("Planning a tutoring response..."):
                plan = plan_response(message, student_memory)
            if not plan["requires_coaching"]:
                reply = regular_chat_response(message)
                reply_activity = None
            else:
                should_log_interaction = True
                question_id = uuid4().hex
                log_agent_decision(
                    st.session_state.student_id, plan["subject"], plan["concept"], plan["sub_concept"],
                    plan["intent"], plan["difficulty"], plan["strategy"], plan["is_repeat_struggle"],
                    event_type="question_plan", question_id=question_id, question_text=message, turn_number=0,
                )
                with st.spinner("Preparing your response..."):
                    reply = coach_response(plan["strategy"], message, student_memory, message)
                log_agent_decision(
                    st.session_state.student_id, plan["subject"], plan["concept"], plan["sub_concept"],
                    plan["intent"], plan["difficulty"], plan["strategy"], plan["is_repeat_struggle"],
                    event_type="coach_turn", hint_count=1, question_id=question_id, question_text=message,
                    turn_number=1, coach_excerpt=make_excerpt(reply),
                )
                st.session_state.active_question = message
                st.session_state.active_plan = plan
                st.session_state.hint_count = 1
                st.session_state.active_question_id = question_id
                reply_activity = activity_details(plan, 1)

        st.markdown(reply)
        if reply_activity:
            show_activity(reply_activity)

    st.session_state.messages.append({"role": "assistant", "content": reply, "agent_activity": reply_activity})
    if should_log_interaction:
        log_conversation(st.session_state.student_id, "user", message)
        log_conversation(st.session_state.student_id, "assistant", reply)
    st.rerun()
