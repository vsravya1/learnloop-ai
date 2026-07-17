CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    name TEXT
);

CREATE TABLE IF NOT EXISTS mastery (
    student_id TEXT,
    subject TEXT,
    concept TEXT,
    sub_concept TEXT,
    score REAL DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    last_updated TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    role TEXT,
    message TEXT,
    timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    subject TEXT,
    concept TEXT,
    sub_concept TEXT,
    intent TEXT,
    difficulty TEXT,
    strategy TEXT,
    is_repeat_struggle BOOLEAN,
    event_type TEXT DEFAULT 'question_plan',
    hint_count INTEGER DEFAULT 0,
    question_id TEXT,
    question_text TEXT,
    turn_number INTEGER,
    coach_excerpt TEXT,
    assessor_understood BOOLEAN,
    assessor_correct BOOLEAN,
    outcome TEXT,
    note TEXT,
    timestamp TIMESTAMP
);
