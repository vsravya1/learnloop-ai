"""Small, on-demand health check for LearnLoop's OpenAI connection."""

from dotenv import load_dotenv
from openai import OpenAI

from .runtime import run_with_timeout


load_dotenv()


def check_openai_connection():
    """Return whether a real, minimal OpenAI request completes successfully."""
    try:
        client = OpenAI(timeout=20.0, max_retries=0)
        response = run_with_timeout(
            lambda: client.responses.create(
                model="gpt-5.6",
                input="Reply with exactly: Hi from LearnLoop",
            )
        )
        if response is None:
            return False, "Timed out while contacting OpenAI."
        return True, (response.output_text or "Connected.").strip()
    except Exception as error:
        print(f"OpenAI connectivity check failed: {error}")
        return False, f"Connection failed: {type(error).__name__}"
