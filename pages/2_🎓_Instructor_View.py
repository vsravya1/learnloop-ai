"""Instructor-facing LearnLoop analytics backed by SQLite data."""

import sqlite3
from html import escape
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


def summarize_questions(question_plans, events):
    """Turn planner, coach, and assessor events into one demo-ready question row."""
    rows = []
    for _, plan in question_plans.iterrows():
        question_events = events[events["question_id"] == plan["question_id"]]
        coach_turns = question_events[question_events["event_type"] == "coach_turn"].sort_values("turn_number")
        assessments = question_events[question_events["event_type"] == "assessment"].sort_values(["timestamp", "id"])
        full_reveals = question_events[question_events["event_type"] == "full_reveal"].sort_values(["timestamp", "id"])
        skipped_questions = question_events[question_events["outcome"] == "skipped"]
        response_events = pd.concat([coach_turns, full_reveals]).sort_values(["timestamp", "id"])

        final_assessment = assessments.iloc[-1] if not assessments.empty else None
        latest_response = response_events.iloc[-1] if not response_events.empty else None
        outcome = "in progress"
        if not skipped_questions.empty:
            outcome = "skipped"
        elif not full_reveals.empty:
            outcome = "needed full reveal"
        elif final_assessment is not None and bool(final_assessment["assessor_correct"]):
            outcome = "solved independently"

        turn_strategies = {
            int(turn["turn_number"]): turn["strategy"]
            for _, turn in coach_turns.iterrows()
            if pd.notna(turn["turn_number"])
        }
        assessor = "pending"
        if not skipped_questions.empty and final_assessment is None:
            assessor = "not assessed (skipped)"
        elif final_assessment is not None:
            assessor = (
                f"correct: {'yes' if bool(final_assessment['assessor_correct']) else 'no'}; "
                f"understood: {'yes' if bool(final_assessment['assessor_understood']) else 'no'}"
            )

        rows.append(
            {
                "student_id": plan["student_id"],
                "concept": f"{plan['subject']} > {plan['concept']} > {plan['sub_concept']}",
                "question": plan["question_text"],
                "Planner": f"{plan['strategy']}, {plan['intent']}, {plan['difficulty']}",
                "Coach": latest_response["coach_excerpt"] if latest_response is not None else "pending",
                "Assessor": assessor,
                "turn_1_decision": turn_strategies.get(1, ""),
                "turn_2_decision": turn_strategies.get(2, ""),
                "turn_3_decision": turn_strategies.get(3, ""),
                "hint_count": int(coach_turns["hint_count"].max()) if not coach_turns.empty else 0,
                "outcome": outcome,
                "timestamp": plan["timestamp"],
            }
        )
    return pd.DataFrame(rows)


def render_activity_table(question_summary):
    """Render readable question rows with a color-coded outcome badge."""
    table_data = question_summary.drop(columns=["timestamp"])
    headers = "".join(f"<th>{escape(column)}</th>" for column in table_data.columns)
    outcome_badges = {
        "solved independently": ("Solved independently", "outcome-solved"),
        "needed full reveal": ("Full reveal", "outcome-reveal"),
        "in progress": ("In progress", "outcome-progress"),
        "skipped": ("Skipped", "outcome-progress"),
    }
    body_rows = []
    for _, row in table_data.iterrows():
        cells = []
        for column in table_data.columns:
            value = "" if pd.isna(row[column]) else str(row[column])
            if column == "outcome":
                label, css_class = outcome_badges.get(value, (value, "outcome-progress"))
                cells.append(f'<td><span class="outcome-badge {css_class}">{escape(label)}</span></td>')
            else:
                cells.append(f"<td>{escape(value)}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    st.markdown(
        """
        <style>
            .activity-table-wrap { overflow-x: auto; border: 1px solid #e8e8ee; border-radius: 0.65rem; }
            .activity-table { width: 100%; min-width: 1350px; border-collapse: collapse; font-size: 0.86rem; }
            .activity-table th { background: #f7f6fb; color: #4d4d5b; font-weight: 600; text-align: left; }
            .activity-table th, .activity-table td { padding: 0.75rem; border-bottom: 1px solid #ececf1; vertical-align: top; white-space: normal; }
            .activity-table td:nth-child(3), .activity-table td:nth-child(4), .activity-table td:nth-child(5) { min-width: 220px; }
            .outcome-badge { display: inline-block; padding: 0.22rem 0.55rem; border-radius: 999px; font-size: 0.78rem; font-weight: 600; white-space: nowrap; }
            .outcome-solved { background: #dcfce7; color: #166534; }
            .outcome-reveal { background: #fef3c7; color: #92400e; }
            .outcome-progress { background: #e5e7eb; color: #4b5563; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="activity-table-wrap"><table class="activity-table"><thead><tr>'
        + headers
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table></div>",
        unsafe_allow_html=True,
    )


init_db()
st.set_page_config(page_title="Instructor View | LearnLoop", page_icon="🎓", layout="wide")
inject_product_css()
st.title("Instructor Analytics")
st.caption("Demo educator view — teacher-only in a production app.")

student_options = query_dataframe(
    "SELECT DISTINCT student_id FROM agent_log WHERE event_type = 'question_plan' ORDER BY student_id"
)["student_id"].tolist()
selected_student = st.selectbox("Student filter", ["All students", *student_options])
selected_parameters = () if selected_student == "All students" else (selected_student,)
student_filter_clause = "" if selected_student == "All students" else "WHERE student_id = ?"

class_question_history = query_dataframe(
    """
    SELECT planned.id, planned.question_id, planned.timestamp,
           COALESCE(MAX(CASE WHEN event.event_type = 'coach_turn' THEN event.hint_count END), 0) AS hint_count,
           MAX(CASE WHEN event.outcome = 'solved_independently' THEN 1 ELSE 0 END) AS solved_independently,
           MAX(CASE WHEN event.outcome = 'needed_full_reveal' THEN 1 ELSE 0 END) AS needed_full_reveal
    FROM agent_log AS planned
    LEFT JOIN agent_log AS event ON event.question_id = planned.question_id
    WHERE planned.event_type = 'question_plan'
      AND planned.question_id IS NOT NULL
      AND NOT (LOWER(planned.subject) = 'general' AND LOWER(planned.concept) = 'conversation')
      AND LOWER(TRIM(COALESCE(planned.question_text, ''))) NOT IN
          ('hi', 'hello', 'hey', 'thanks', 'thank you', 'ok', 'okay', 'cool', 'great', 'got it')
    GROUP BY planned.id, planned.question_id, planned.timestamp
    ORDER BY planned.timestamp ASC, planned.id ASC
    """
)
class_independence_trend = calculate_independence_trend(class_question_history)
st.subheader("Class learning independence")
if class_independence_trend is None:
    st.info("Keep practicing to see the class independence trend.")
else:
    earlier, recent = class_independence_trend
    rate_change = recent["independence_rate"] - earlier["independence_rate"]
    turns_change = recent["average_turns"] - earlier["average_turns"]
    improved = rate_change > 0 and turns_change <= 0
    declined = rate_change < 0 or turns_change > 0
    rate_column, turns_column = st.columns(2)
    rate_column.metric(
        "Class independence rate (recent sessions)",
        f"{recent['independence_rate']:.0f}%",
    )
    turns_column.metric(
        "Average coaching turns",
        f"{earlier['average_turns']:.1f} → {recent['average_turns']:.1f}",
    )
    if improved:
        st.caption(f"↑ {rate_change:.0f} percentage points from earlier sessions, with fewer coaching turns.")
        st.caption("Students are needing fewer hints to solve problems on their own compared to earlier sessions.")
    elif declined:
        st.caption("↓ Recent sessions are requiring more support than earlier sessions.")
    else:
        st.caption("→ Class independence is about the same as in earlier sessions.")
    st.caption("This rate includes only completed learning questions, not greetings or skipped questions.")

students = query_dataframe(
    """
    WITH active_students AS (
        SELECT DISTINCT student_id FROM agent_log
        WHERE event_type = 'question_plan'
          AND NOT (LOWER(subject) = 'general' AND LOWER(concept) = 'conversation')
        """
    + ("" if selected_student == "All students" else " AND student_id = ?")
    + """
    )
    SELECT active_students.student_id, COALESCE(AVG(mastery.score), 0) AS average_mastery_score
    FROM active_students
    LEFT JOIN mastery ON mastery.student_id = active_students.student_id
    GROUP BY active_students.student_id
    ORDER BY average_mastery_score ASC, active_students.student_id
    """,
    selected_parameters,
)

total_questions = query_dataframe(
    "SELECT COUNT(*) AS total FROM agent_log WHERE event_type = 'question_plan' "
    + "AND NOT (LOWER(subject) = 'general' AND LOWER(concept) = 'conversation') "
    + ("" if selected_student == "All students" else "AND student_id = ?"),
    selected_parameters,
).iloc[0]["total"]
students_needing_attention = int((students["average_mastery_score"] < 0.4).sum()) if not students.empty else 0

completion_outcomes = query_dataframe(
    """
    SELECT outcome, COUNT(*) AS question_count
    FROM agent_log
    WHERE outcome IN ('solved_independently', 'needed_full_reveal')
    """
    + ("" if selected_student == "All students" else " AND student_id = ?")
    + " GROUP BY outcome",
    selected_parameters,
)
completion_counts = dict(zip(completion_outcomes["outcome"], completion_outcomes["question_count"]))
completed_questions = sum(completion_counts.values())
st.subheader("Completion outcomes")
if completed_questions:
    independent_percent = 100 * completion_counts.get("solved_independently", 0) / completed_questions
    reveal_percent = 100 * completion_counts.get("needed_full_reveal", 0) / completed_questions
    total_column, attention_column, independent_column, reveal_column = st.columns(4)
    total_column.metric("Total questions asked", int(total_questions))
    attention_column.metric("Students needing attention", students_needing_attention)
    independent_column.metric("Overall independent resolution", f"{independent_percent:.0f}%")
    reveal_column.metric("Needed full reveal", f"{reveal_percent:.0f}%")
    st.caption("Overall independent resolution covers all completed learning questions; the headline metric covers only recent completed sessions.")
else:
    total_column, attention_column = st.columns(2)
    total_column.metric("Total questions asked", int(total_questions))
    attention_column.metric("Students needing attention", students_needing_attention)
    st.caption("Completion outcomes will appear after students finish questions.")

strategy_usage = query_dataframe(
    """
    SELECT strategy, COUNT(*) AS usage_count
    FROM agent_log
    WHERE event_type = 'coach_turn'
      AND strategy IN ('hint', 'socratic_question', 'worked_example', 'reveal_next_step')
      AND NOT (LOWER(subject) = 'general' AND LOWER(concept) = 'conversation')
    """
    + ("" if selected_student == "All students" else " AND student_id = ?")
    + " GROUP BY strategy ORDER BY usage_count DESC, strategy ASC",
    selected_parameters,
)
st.subheader("Coaching strategy usage")
if strategy_usage.empty:
    st.caption("Strategy usage will appear after the first coaching response.")
else:
    strategy_usage["usage_percent"] = 100 * strategy_usage["usage_count"] / strategy_usage["usage_count"].sum()
    st.bar_chart(strategy_usage.set_index("strategy")["usage_percent"])
    st.caption("Percent of all coach turns using each strategy.")

st.subheader("Student mastery overview")
if students.empty:
    st.info("No student activity recorded yet.")
else:
    students["average_mastery_score"] = students["average_mastery_score"].round(2)
    st.dataframe(students, use_container_width=True, hide_index=True)

st.subheader("Topics needing the most support")
available_subjects = query_dataframe(
    "SELECT DISTINCT subject FROM mastery "
    + student_filter_clause
    + " ORDER BY subject ASC",
    selected_parameters,
)["subject"].tolist()
selected_subject = st.selectbox("Subject", ["All Subjects", *available_subjects])

if selected_subject == "All Subjects":
    topic_filter_clause = student_filter_clause
    topic_parameters = selected_parameters
elif selected_student == "All students":
    topic_filter_clause = "WHERE subject = ?"
    topic_parameters = (selected_subject,)
else:
    topic_filter_clause = "WHERE student_id = ? AND subject = ?"
    topic_parameters = (*selected_parameters, selected_subject)

struggled_topics = query_dataframe(
    """
    SELECT subject, concept, sub_concept, AVG(score) AS average_mastery_score,
           COUNT(DISTINCT student_id) AS student_count
    FROM mastery
    """
    + topic_filter_clause
    + """
    GROUP BY subject, concept, sub_concept
    ORDER BY average_mastery_score ASC, student_count DESC
    """,
    topic_parameters,
)
if struggled_topics.empty:
    st.caption("Topic-level mastery data will appear after assessed student replies.")
else:
    if selected_subject == "All Subjects":
        struggled_topics["topic"] = (
            struggled_topics["subject"]
            + " > "
            + struggled_topics["concept"]
            + " > "
            + struggled_topics["sub_concept"]
        )
    else:
        struggled_topics["topic"] = struggled_topics["sub_concept"]
    st.bar_chart(struggled_topics.set_index("topic")["average_mastery_score"])

plans = query_dataframe(
    """
    SELECT id, student_id, subject, concept, sub_concept, intent, difficulty, strategy,
           question_id, question_text, timestamp
    FROM agent_log
    WHERE event_type = 'question_plan' AND question_id IS NOT NULL
      AND NOT (LOWER(subject) = 'general' AND LOWER(concept) = 'conversation')
    """
    + ("" if selected_student == "All students" else " AND student_id = ?")
    + " ORDER BY timestamp DESC, id DESC LIMIT 15",
    selected_parameters,
)

st.subheader("Recent Agent Activity by Question")
if plans.empty:
    st.caption("No question-level agent activity recorded yet.")
else:
    placeholders = ",".join("?" for _ in plans["question_id"])
    events = query_dataframe(
        f"SELECT * FROM agent_log WHERE question_id IN ({placeholders}) ORDER BY timestamp, id",
        tuple(plans["question_id"]),
    )
    question_summary = summarize_questions(plans, events)
    st.caption("Long question, planner, and coach text wraps in this table so it remains fully readable.")
    render_activity_table(question_summary)

st.subheader("Coaching strategy glossary")
st.write("**hint:** A partial clue, not the full method.")
st.write("**socratic_question:** A guiding question that leads the student to the answer themselves.")
st.write("**worked_example:** A similar solved example, not the exact answer to their question.")
st.write("**reveal_next_step:** Just the next step, not the full solution.")
