## What this is
LearnLoop is an AI learning platform where students talk to a normal chat interface, but behind the scenes, AI agents decide the best way to teach instead of just answering questions. When a student asks something, the system figures out what they're really asking, checks what they've struggled with before, and picks a teaching strategy — a hint, a guiding question, or a worked example — before responding.

The platform tracks learning progress over time, finds skill gaps per topic, and gives dashboards for both students and educators to see how learning is actually going — including whether students are becoming more independent, not just how many messages they sent.

## Why
Today's AI tools are built for speed: ask a question, get a full answer. That's great for getting things done fast, but it quietly removes the struggle that's often where real learning happens. LearnLoop doesn't stop students from using AI — it changes what "using AI" looks like, so it coaches instead of just answering.

## How it works
Every student message goes through a small pipeline before a response comes back:

**Planner** — figures out the intent, difficulty, and subject/concept, then picks a teaching strategy.

**Coach** — gives the actual response using that strategy (a hint, a question that nudges the student toward the answer, or a worked example), always coaching instead of answering directly. Only after a limited number of coaching turns does Coach give the full answer, and that question gets logged as either "solved independently" or "needed full reveal."

**Assessor** — after the student replies, checks if they actually understood, and updates their progress record.

Every decision gets logged, so unlike a single fixed prompt, LearnLoop keeps a real, checkable history of how each student learns over time — including a **Learning Independence** score that tracks whether a student needs fewer hints as they practice.

There's also a basic safety layer that checks for content that's not appropriate for a learning tool before it reaches the coaching pipeline, and Coach is built to stay in its role even if asked to drop it.

## Who it's for
Students are the users. Schools, universities, and online course providers are the ones we expect to actually buy this, since they're the ones who want to know if students are really learning, not just finishing assignments.

## Tech stack
- Streamlit (chat UI + dashboards)
- GPT-5.6 (reasoning + generation)
- SQLite (learning memory, mastery tracking, agent decision log)
- Built with Codex

## How to test
1. Open the live app: https://learnloop-coach.streamlit.app
2. Enter any name to start (this is a simple demo identifier, not real authentication).
3. Ask a question in the chat — try a math problem (e.g. "solve x²-5x+6=0") or an open-ended question (e.g. "help me write a thesis about remote work"). Coach will guide you with hints and questions rather than giving the answer immediately — try pushing back with "just give me the answer" to see it hold its coaching approach.
4. Click "See agent activity" under any response to see the Planner/Coach/Assessor decision trace for that turn.
5. Use the sidebar to navigate to "My Progress" (student dashboard) and "Instructor View" (class-wide analytics) to see mastery tracking and the Learning Independence metric.

Note: the app is hosted on Streamlit Community Cloud's free tier, so it may take 20-30 seconds to "wake up" if it's been inactive — please allow a moment on first load.

## Built with Codex
We built the whole thing with Codex — the three agents, the chat interface in Streamlit, both dashboards, and the database that stores memory — using GPT-5.6 to actually power the Planner, Coach, and Assessor. We worked in one continuous Codex session, building one piece at a time: first the scaffold, then one agent at a time, testing each in a simple terminal loop before touching the UI at all.

**Where Codex helped speed things up:** generating the first project scaffold and database schema, writing the Planner/Coach/Assessor functions from our prompts, building the Streamlit pages and dashboards, and doing the UI polish (custom CSS, theming).

**Key decisions we made along the way:**
- Always-coach behavior (no toggle to skip coaching) instead of letting students turn it off, to keep the actual teaching intact
- Tracking topics as subject > concept > sub-concept instead of a fixed list, since that's what actually stayed readable once we tested it
- A hard limit of 3 coaching turns, so every question ends with either "solved independently" or "needed full reveal" — never stuck in a loop


**Real bugs Codex helped us catch and fix:**
- A scoring bug where mastery stayed at 0.0 even though attempts were counting up correctly
- A coaching loop that kept checking small arithmetic steps instead of realizing the actual question was already solved
- A regression where fixing one scenario (open-ended questions hitting the turn limit) broke a different one (math questions solved correctly right on that same limit)
- A crash that only happened after deploying to Streamlit Cloud, not locally — tied to a safety feature we'd added

Every fix here was checked by re-running the exact scenario that broke and looking at the real result — not just trusting Codex's word that it was fixed.
