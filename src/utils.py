import re
from pathlib import Path


MUTPY = Path(__file__).parent.parent / ".venv" / "bin" / "mut.py"


def extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()