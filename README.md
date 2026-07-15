# LearnLoop

## What this is

LearnLoop is an AI learning platform where students interact with a normal chat interface, but behind the scenes, AI agents decide the best way to teach instead of simply answering questions. When a student asks something, the system first figures out what they're really asking for, checks what they've struggled with before, and chooses a teaching strategy — a hint, a guiding
question, a worked example, or (when appropriate) a direct answer — before generating a response.

The platform tracks learning progress over time, identifies skill gaps per concept, and provides dashboards for both students and educators to see how learning is actually going, not just how many messages were exchanged.

## Why

Today's AI assistants are optimized for speed: ask a question, get a complete answer. That's great for productivity, but it quietly removes the struggle that's often where real learning happens. LearnLoop doesn't block students from using AI — it changes what "using AI" looks like, so the AI teaches
rather than just answers.

## How it works

Every student message goes through a small pipeline before a response is generated:

1. **Planner** — classifies intent, difficulty, and whether this is a repeat struggle, then picks a teaching strategy.
2. **Teacher** — generates the actual response using that strategy (a hint, a question that nudges them toward the answer themselves, a worked example, or (when appropriate) ), not a canned reply.
3. **Assessor** — after the student responds, evaluates whether they demonstrated understanding and updates their mastery record.

Every decision is logged, so unlike a single static system prompt, LearnLoop maintains a real history of how each student learns over time and can adapt future teaching to it.

## Who it's for

Students are the users. Educational institutions — universities, schools,online course providers — are the intended buyers, since they're the ones who want visibility into whether students are actually learning, not just completing assignments.

## Tech stack

- Streamlit (chat UI + dashboards)
- GPT-5.6 (reasoning + generation)
- SQLite (learning memory, mastery tracking, agent decision log)
- Built with Codex

