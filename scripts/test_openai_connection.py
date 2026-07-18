"""Minimal OpenAI connectivity check for LearnLoop."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.health import check_openai_connection


def main():
    """Send one small request and report whether the OpenAI API is reachable."""
    success, detail = check_openai_connection()
    if success:
        print("OpenAI connection succeeded.")
        print(f"Response: {detail}")
        return 0
    print(f"OpenAI connection failed: {detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
