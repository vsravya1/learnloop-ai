# LearnLoop

## What this is
LearnLoop is an AI learning platform where students interact with a normal chat interface, but behind the scenes, AI agents decide the best way to teach instead of simply answering questions. When a student asks something, the system first figures out what they're really asking for, checks what they've struggled with before, and chooses a teaching strategy — a hint, a guiding question, or a worked example — before generating a response.

The platform tracks learning progress over time, identifies skill gaps per concept, and provides dashboards for both students and educators to see how learning is actually going — including whether students are becoming more independent, not just how many messages were exchanged.

## Why
Today's AI assistants are optimized for speed: ask a question, get a complete answer. That's great for productivity, but it quietly removes the struggle that's often where real learning happens. LearnLoop doesn't block students from using AI — it changes what "using AI" looks like, so the AI coaches rather than just answers.

## How it works
Every student message goes through a small pipeline before a response is generated:

1. **Planner** — classifies intent, difficulty, and subject/concept, then picks a teaching strategy.
2. **Coach** — generates the actual response using that strategy (a hint, a question that nudges the student toward the answer themselves, or a worked example), always coaching rather than answering directly. Only after a capped number of coaching turns does Coach reveal the full answer, and that question is logged as resolved either "solved independently" or "needed full reveal."
3. **Assessor** — after the student responds, evaluates whether they demonstrated real understanding and updates their mastery record accordingly.

Every decision is logged, so unlike a single static system prompt, LearnLoop maintains a real, queryable history of how each student learns over time — including a **Learning Independence** metric that tracks whether a student is needing fewer hints as they practice.

A lightweight safety layer also checks for content that's inappropriate for an educational tool before it reaches the coaching pipeline, and Coach is designed to stay in its coaching role even if asked to abandon it.

## Who it's for
Students are the users. Educational institutions — universities, schools, online course providers — are the intended buyers, since they're the ones who want visibility into whether students are actually learning, not just completing assignments.

## Tech stack
- Streamlit (chat UI + dashboards)
- GPT-5.6 (reasoning + generation)
- SQLite (learning memory, mastery tracking, agent decision log)
- Built with Codex

## Built with Codex

This project was built collaboratively with **Codex**, using **GPT-5.6** to power
the Planner, Coach, and Assessor agents. We worked in a single continuous Codex
session, iterating one piece at a time: scaffold first, then one agent at a time,
tested in a terminal loop before touching the UI.

**Where Codex accelerated the workflow:** generating the initial project scaffold
and SQLite schema, writing the Planner/Coach/Assessor agent functions from
structured prompts, building the Streamlit multi-page UI and dashboards, and
implementing UI polish (custom CSS, theming).

**Key product decisions made through iteration with Codex:**
- Always-coach behavior (no bypassable "just give me the answer" mode) instead of
  a student-facing toggle, to preserve the core pedagogy
- Hierarchical concept tracking (subject > concept > sub-concept) instead of a
  fixed taxonomy, based on testing what actually stayed readable and useful
- A hard turn cap on coaching (max 3 turns) so every question resolves to either
  "solved independently" or "needed full reveal" — never an open-ended loop

**Real bugs Codex helped us find and fix:**
- A mastery-scoring bug where scores stayed at 0.0 despite attempts incrementing
  correctly
- An infinite coaching loop where the Assessor kept drilling into arithmetic
  sub-steps instead of recognizing the original question was solved
- A regression where a fix for one scenario (open-ended questions reaching the
  turn cap) broke a different scenario (math questions correctly solved on the
  capped turn)
- A deployment-only import error that only surfaced after migrating from local
  testing to Streamlit Community Cloud, tied to a safety/guardrail feature

Every fix above was verified by re-running the exact failing scenario and reading
the actual output — not just accepting Codex's report that something was fixed.
