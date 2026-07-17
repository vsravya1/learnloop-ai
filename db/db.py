"""Small SQLite persistence helpers for LearnLoop."""

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("learnloop.db")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _connect():
    """Return a connection to LearnLoop's local SQLite database."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create learnloop.db and its tables when they do not already exist."""
    with _connect() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        agent_log_columns = {row[1] for row in conn.execute("PRAGMA table_info(agent_log)")}
        event_type_added = "event_type" not in agent_log_columns
        columns_to_add = {
            "note": "TEXT",
            "event_type": "TEXT DEFAULT 'question_plan'",
            "hint_count": "INTEGER DEFAULT 0",
            "question_id": "TEXT",
            "question_text": "TEXT",
            "turn_number": "INTEGER",
            "coach_excerpt": "TEXT",
            "assessor_understood": "BOOLEAN",
            "assessor_correct": "BOOLEAN",
            "outcome": "TEXT",
        }
        for column, definition in columns_to_add.items():
            if column not in agent_log_columns:
                conn.execute(f"ALTER TABLE agent_log ADD COLUMN {column} {definition}")
        if event_type_added:
            conn.execute(
                "UPDATE agent_log SET event_type = CASE "
                "WHEN note IS NULL THEN 'question_plan' ELSE 'full_reveal' END"
            )


def get_student_memory(student_id):
    """Return a student's mastery records and ten latest conversation entries."""
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        mastery = conn.execute(
            "SELECT subject, concept, sub_concept, score, attempts, last_updated "
            "FROM mastery WHERE student_id = ? ORDER BY last_updated DESC",
            (student_id,),
        ).fetchall()
        conversations = conn.execute(
            "SELECT role, message, timestamp FROM conversation_log "
            "WHERE student_id = ? ORDER BY timestamp DESC, id DESC LIMIT 10",
            (student_id,),
        ).fetchall()

    return {
        "mastery": [dict(row) for row in mastery],
        "recent_conversations": [dict(row) for row in conversations],
    }


def log_conversation(student_id, role, message):
    """Save one chat message for a student."""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO conversation_log (student_id, role, message, timestamp) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (student_id, role, message),
        )


def log_agent_decision(
    student_id,
    subject,
    concept,
    sub_concept,
    intent,
    difficulty,
    strategy,
    is_repeat,
    note=None,
    event_type="question_plan",
    hint_count=0,
    question_id=None,
    question_text=None,
    turn_number=None,
    coach_excerpt=None,
    assessor_understood=None,
    assessor_correct=None,
    outcome=None,
):
    """Record the tutoring agent's chosen response strategy."""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO agent_log "
            "(student_id, subject, concept, sub_concept, intent, difficulty, "
            "strategy, is_repeat_struggle, event_type, hint_count, question_id, "
            "question_text, turn_number, coach_excerpt, assessor_understood, "
            "assessor_correct, outcome, note, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (
                student_id,
                subject,
                concept,
                sub_concept,
                intent,
                difficulty,
                strategy,
                bool(is_repeat),
                event_type,
                hint_count,
                question_id,
                question_text,
                turn_number,
                coach_excerpt,
                assessor_understood,
                assessor_correct,
                outcome,
                note,
            ),
        )


def get_latest_planner_decision(student_id):
    """Return the latest initial planner decision recorded for a student."""
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        decision = conn.execute(
            "SELECT intent, difficulty, strategy, subject, concept, sub_concept "
            "FROM agent_log WHERE student_id = ? AND event_type = 'question_plan' "
            "ORDER BY timestamp DESC, id DESC LIMIT 1",
            (student_id,),
        ).fetchone()
    return dict(decision) if decision else None


def update_mastery(student_id, subject, concept, sub_concept, score_delta):
    """Add a score adjustment and count an attempt for a hierarchical concept."""
    with _connect() as conn:
        existing = conn.execute(
            "SELECT rowid FROM mastery WHERE student_id = ? AND subject = ? "
            "AND concept = ? AND sub_concept = ?",
            (student_id, subject, concept, sub_concept),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE mastery SET score = MIN(1.0, MAX(0.0, score + ?)), "
                "attempts = attempts + 1, "
                "last_updated = CURRENT_TIMESTAMP WHERE rowid = ?",
                (score_delta, existing[0]),
            )
        else:
            conn.execute(
                "INSERT INTO mastery "
                "(student_id, subject, concept, sub_concept, score, attempts, last_updated) "
                "VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)",
                (
                    student_id,
                    subject,
                    concept,
                    sub_concept,
                    min(1.0, max(0.0, score_delta)),
                ),
            )
