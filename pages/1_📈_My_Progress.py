"""Student-facing progress dashboard backed by LearnLoop's SQLite data."""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from db.db import init_db
from ui import inject_product_css


DB_PATH = Path(__file__).resolve().parents[1] / "db" / "learnloop.db"


def query_dataframe(query, parameters=()):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=parameters)


def calculate_independence_trend(questions):
    """Compare recent question outcomes with an equally sized earlier set."""
    completed_questions = questions[
        (questions["solved_independently"] == 1)
        | (questions["needed_full_reveal"] == 1)
    ]
    if len(completed_questions) < 6:
        return None

    midpoint = len(completed_questions) // 2
    earlier = completed_questions.iloc[:midpoint]
    recent = completed_questions.iloc[midpoint:]

    def snapshot(question_set):
        return {
            "independence_rate": 100 * question_set["solved_independently"].mean(),
            "average_turns": question_set["hint_count"].mean(),
        }

    earlier_snapshot, recent_snapshot = snapshot(earlier), snapshot(recent)
    if not earlier_snapshot or not recent_snapshot:
        return None
    return earlier_snapshot, recent_snapshot


init_db()
st.set_page_config(page_title="My Progress | LearnLoop", page_icon="📈", layout="wide")
inject_product_css()
st.title("My Progress")

student_id = st.session_state.get("student_id")
if not student_id:
    st.info("Start in LearnLoop Chat and enter your student ID to see your progress.")
    st.stop()

question_history = query_dataframe(
    """
    SELECT planned.id, planned.question_id, planned.timestamp,
           COALESCE(MAX(CASE WHEN event.event_type = 'coach_turn' THEN event.hint_count END), 0) AS hint_count,
           MAX(CASE WHEN event.outcome = 'solved_independently' THEN 1 ELSE 0 END) AS solved_independently,
           MAX(CASE WHEN event.outcome = 'needed_full_reveal' THEN 1 ELSE 0 END) AS needed_full_reveal
    FROM agent_log AS planned
    LEFT JOIN agent_log AS event ON event.question_id = planned.question_id
    WHERE planned.student_id = ?
      AND planned.event_type = 'question_plan'
      AND planned.question_id IS NOT NULL
      AND NOT (LOWER(planned.subject) = 'general' AND LOWER(planned.concept) = 'conversation')
      AND LOWER(TRIM(COALESCE(planned.question_text, ''))) NOT IN
          ('hi', 'hello', 'hey', 'thanks', 'thank you', 'ok', 'okay', 'cool', 'great', 'got it')
    GROUP BY planned.id, planned.question_id, planned.timestamp
    ORDER BY planned.timestamp ASC, planned.id ASC
    """,
    (student_id,),
)
independence_trend = calculate_independence_trend(question_history)
st.subheader("Learning independence")
if independence_trend is None:
    st.info("Keep practicing to see your independence trend.")
else:
    earlier, recent = independence_trend
    rate_change = recent["independence_rate"] - earlier["independence_rate"]
    turns_change = recent["average_turns"] - earlier["average_turns"]
    improved = rate_change > 0 and turns_change <= 0
    declined = rate_change < 0 or turns_change > 0
    rate_column, turns_column = st.columns(2)
    rate_column.metric(
        "Learning independence (recent sessions)",
        f"{recent['independence_rate']:.0f}%",
    )
    turns_column.metric(
        "Average coaching turns",
        f"{earlier['average_turns']:.1f} → {recent['average_turns']:.1f}",
    )
    if improved:
        st.caption(f"↑ {rate_change:.0f} percentage points from earlier sessions, with fewer coaching turns.")
        st.caption("You're needing fewer hints to solve problems on your own compared to when you started.")
    elif declined:
        st.caption("↓ Recent sessions are requiring more support than earlier sessions.")
    else:
        st.caption("→ Your independence is about the same as in earlier sessions.")
    st.caption("This rate includes only completed learning questions, not greetings or skipped questions.")

mastery = query_dataframe(
    """
    SELECT subject, concept, sub_concept, score, attempts, last_updated
    FROM mastery
    WHERE student_id = ?
    ORDER BY subject, concept, sub_concept
    """,
    (student_id,),
)

question_total = query_dataframe(
    """
    SELECT COUNT(*) AS total
    FROM agent_log
    WHERE student_id = ? AND event_type = 'question_plan'
      AND NOT (LOWER(subject) = 'general' AND LOWER(concept) = 'conversation')
    """,
    (student_id,),
).iloc[0]["total"]

outcomes = query_dataframe(
    """
    SELECT outcome, COUNT(*) AS question_count
    FROM agent_log
    WHERE student_id = ?
      AND outcome IN ('solved_independently', 'needed_full_reveal')
    GROUP BY outcome
    """,
    (student_id,),
)
outcome_counts = dict(zip(outcomes["outcome"], outcomes["question_count"]))
completed_questions = sum(outcome_counts.values())
if completed_questions:
    solved_percent = 100 * outcome_counts.get("solved_independently", 0) / completed_questions
    reveal_percent = 100 * outcome_counts.get("needed_full_reveal", 0) / completed_questions
    total_column, solved_column, reveal_column = st.columns(3)
    total_column.metric("Total questions asked", int(question_total))
    solved_column.metric("Overall independent resolution", f"{solved_percent:.0f}%")
    reveal_column.metric("Needed full reveal", f"{reveal_percent:.0f}%")
    st.caption("Overall independent resolution covers all completed learning questions; the headline metric covers only recent completed sessions.")
else:
    st.metric("Total questions asked", int(question_total))
    st.caption("Completion outcome percentages appear once a question is solved or reaches a full reveal.")

if mastery.empty:
    st.info("No assessed attempts yet. Work through a coaching question to start tracking mastery.")
else:
    chart_data = mastery.copy()
    chart_data["topic"] = (
        chart_data["subject"]
        + " › "
        + chart_data["concept"]
        + " › "
        + chart_data["sub_concept"]
    )
    st.subheader("Mastery by topic")
    st.bar_chart(chart_data.set_index("topic")["score"])

subjects = query_dataframe(
    """
    SELECT subject, COUNT(*) AS question_count
    FROM agent_log
    WHERE student_id = ? AND event_type = 'question_plan'
      AND NOT (LOWER(subject) = 'general' AND LOWER(concept) = 'conversation')
    GROUP BY subject
    ORDER BY question_count DESC, subject ASC
    """,
    (student_id,),
)
st.subheader("Subjects explored")
if subjects.empty:
    st.caption("Subject exploration will appear after the first question.")
else:
    st.bar_chart(subjects.set_index("subject")["question_count"])

agent_log = query_dataframe(
    """
    SELECT subject, concept, sub_concept, strategy, timestamp
    FROM agent_log
    WHERE student_id = ? AND event_type = 'question_plan'
    ORDER BY timestamp DESC, id DESC
    LIMIT 5
    """,
    (student_id,),
)

st.subheader("Recent questions")
if agent_log.empty:
    st.caption("No coaching decisions recorded yet.")
else:
    st.dataframe(agent_log, use_container_width=True, hide_index=True)

st.subheader("Coaching strategy glossary")
st.write("**hint:** A partial clue, not the full method.")
st.write("**socratic_question:** A guiding question that leads you to the answer yourself.")
st.write("**worked_example:** A similar solved example, not the exact answer to your question.")
st.write("**reveal_next_step:** Just the next step, not the full solution.")
