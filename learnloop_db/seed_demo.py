"""Create deterministic LearnLoop demo data for dashboards and live walkthroughs."""

import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [
    str(ROOT_DIR),
    *[path for path in sys.path if Path(path or ".").resolve() != SCRIPT_DIR],
]

from learnloop_db.db import DB_PATH, init_db  # noqa: E402


STUDENTS = {
    "test-user1": "test-user1",
    "test-user2": "test-user2",
    "test-user3": "test-user3",
}

TOPICS = [
    ("Math", "Equations", "Quadratic Equations", "Solve x² - 5x + 6 = 0.", "homework"),
    ("Math", "Algebra", "Factoring", "Factor x² + 7x + 12.", "homework"),
    ("English", "Writing", "Thesis Statements", "Help me improve this essay thesis.", "essay"),
    ("English", "Writing", "Paragraph Structure", "How should I organize this body paragraph?", "essay"),
    ("Computer Science", "Programming", "Python Basics", "How do I write a Python loop?", "coding"),
    ("Math", "Calculus", "Basic Derivatives", "Find the derivative of x² + 3x.", "conceptual_question"),
]

# Each tuple is (outcome, coaching turns). The first three are earlier sessions.
LEARNING_PATHS = {
    "test-user1": [("full", 2), ("full", 2), ("solved", 2), ("solved", 1), ("solved", 1), ("solved", 1)],
    "test-user2": [("solved", 2), ("solved", 1), ("solved", 1), ("solved", 1), ("solved", 1), ("solved", 1)],
    "test-user3": [("solved", 1), ("full", 2), ("full", 2), ("full", 2), ("full", 2), ("solved", 2)],
}

INITIAL_STRATEGIES = ["hint", "socratic_question", "worked_example", "reveal_next_step"]


def insert_agent_event(conn, **event):
    columns = [
        "student_id", "subject", "concept", "sub_concept", "intent", "difficulty",
        "strategy", "is_repeat_struggle", "event_type", "hint_count", "question_id",
        "question_text", "turn_number", "coach_excerpt", "assessor_understood",
        "assessor_correct", "outcome", "note", "timestamp",
    ]
    conn.execute(
        f"INSERT INTO agent_log ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
        tuple(event.get(column) for column in columns),
    )


def clear_database(conn):
    for table in ("agent_log", "conversation_log", "mastery", "students"):
        conn.execute(f"DELETE FROM {table}")
    conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('agent_log', 'conversation_log')")


def seed_demo_data():
    """Reset local data and create a dashboard-ready, repeatable demo dataset."""
    init_db()
    mastery = defaultdict(lambda: {"score": 0.0, "attempts": 0})
    start_time = datetime(2026, 7, 1, 9, 0, 0)

    with sqlite3.connect(DB_PATH) as conn:
        clear_database(conn)
        conn.executemany(
            "INSERT INTO students (id, name) VALUES (?, ?)",
            STUDENTS.items(),
        )

        question_number = 0
        # Interleave students so the class-level earlier/recent trend is meaningful.
        for round_number in range(6):
            for student_id in STUDENTS:
                outcome, turns = LEARNING_PATHS[student_id][round_number]
                subject, concept, sub_concept, question_text, intent = TOPICS[round_number]
                strategy = INITIAL_STRATEGIES[round_number % len(INITIAL_STRATEGIES)]
                question_id = f"demo-{student_id}-{round_number + 1}"
                timestamp = start_time + timedelta(hours=question_number)
                timestamp_text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                difficulty = "easy" if round_number < 2 else "medium"

                insert_agent_event(
                    conn,
                    student_id=student_id, subject=subject, concept=concept,
                    sub_concept=sub_concept, intent=intent, difficulty=difficulty,
                    strategy=strategy, is_repeat_struggle=round_number > 1,
                    event_type="question_plan", hint_count=0, question_id=question_id,
                    question_text=question_text, turn_number=0, timestamp=timestamp_text,
                )

                for turn in range(1, turns + 1):
                    turn_strategy = strategy if turn == 1 else "reveal_next_step"
                    turn_time = timestamp + timedelta(minutes=turn * 3)
                    insert_agent_event(
                        conn,
                        student_id=student_id, subject=subject, concept=concept,
                        sub_concept=sub_concept, intent=intent, difficulty=difficulty,
                        strategy=turn_strategy, is_repeat_struggle=round_number > 1,
                        event_type="coach_turn", hint_count=turn, question_id=question_id,
                        question_text=question_text, turn_number=turn,
                        coach_excerpt="A focused coaching step toward the final answer.",
                        timestamp=turn_time.strftime("%Y-%m-%d %H:%M:%S"),
                    )

                final_time = timestamp + timedelta(minutes=(turns + 1) * 3)
                if outcome == "solved":
                    insert_agent_event(
                        conn,
                        student_id=student_id, subject=subject, concept=concept,
                        sub_concept=sub_concept, intent=intent, difficulty=difficulty,
                        strategy="reveal_next_step", is_repeat_struggle=round_number > 1,
                        event_type="assessment", hint_count=turns, question_id=question_id,
                        question_text=question_text, assessor_understood=True,
                        assessor_correct=True, outcome="solved_independently",
                        timestamp=final_time.strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    score_gain = 0.30 if turns == 1 else 0.15
                    mastery[(student_id, subject, concept, sub_concept)]["score"] += score_gain
                else:
                    insert_agent_event(
                        conn,
                        student_id=student_id, subject=subject, concept=concept,
                        sub_concept=sub_concept, intent=intent, difficulty=difficulty,
                        strategy="full_answer", is_repeat_struggle=round_number > 1,
                        event_type="full_reveal", hint_count=turns, question_id=question_id,
                        question_text=question_text,
                        coach_excerpt="Complete solution shown after guided coaching steps.",
                        assessor_understood=False, assessor_correct=False,
                        outcome="needed_full_reveal",
                        note="Demo student needed a full reveal after guided coaching.",
                        timestamp=final_time.strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    mastery[(student_id, subject, concept, sub_concept)]["score"] += 0.05

                mastery[(student_id, subject, concept, sub_concept)]["attempts"] += 1
                conn.execute(
                    "INSERT INTO conversation_log (student_id, role, message, timestamp) VALUES (?, ?, ?, ?)",
                    (student_id, "user", question_text, timestamp_text),
                )
                conn.execute(
                    "INSERT INTO conversation_log (student_id, role, message, timestamp) VALUES (?, ?, ?, ?)",
                    (student_id, "assistant", "Demo coaching response recorded.", final_time.strftime("%Y-%m-%d %H:%M:%S")),
                )
                question_number += 1

        for (student_id, subject, concept, sub_concept), values in mastery.items():
            conn.execute(
                """
                INSERT INTO mastery (student_id, subject, concept, sub_concept, score, attempts, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id, subject, concept, sub_concept,
                    min(1.0, values["score"]), values["attempts"],
                    "2026-07-02 12:00:00",
                ),
            )

    print(f"Seeded {len(STUDENTS)} students and {question_number} completed learning questions in {DB_PATH}.")


if __name__ == "__main__":
    seed_demo_data()
