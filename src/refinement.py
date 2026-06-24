import sys
import tempfile
import subprocess
from pathlib import Path

from utils import extract_code
from llm_option import llm_generate


def refine_test(test_code: str, put_code: str, llm: str) -> str:
    test_code = extract_code(test_code)
    if "def test_" not in test_code:
        test_code = _wrap_as_pytest(test_code)

    test_code = _sanitize_test(test_code)

    passes = _check_test_execution(test_code, put_code)
    if passes:
        return test_code

    print("   ⚠ Test has errors, requesting fix from LLM...")
    fix_prompt = (
        "The following test has errors when executed. Fix it.\n\n"
        f"```python\n{test_code}\n```\n\n"
        "Return ONLY the corrected test code."
    )
    try:
        fixed = llm_generate(fix_prompt, llm)
        fixed = extract_code(fixed)
        fixed = _sanitize_test(fixed)
        if _check_test_execution(fixed, put_code):
            print("   ✅ Test fixed successfully")
            return fixed
    except Exception as e:
        print(f"   ⚠ Fix attempt failed: {e}")

    return test_code


def _wrap_as_pytest(code: str) -> str:
    lines = code.strip().splitlines()
    if any(l.startswith("def test_") for l in lines):
        return code
    return f"def test_function():\n    {code}"


def _sanitize_test(code: str) -> str:
    lines = []
    for line in code.splitlines():
        stripped = line.strip()
        if not stripped.startswith("```") and stripped != "python":
            lines.append(line)
    return "\n".join(lines)


def _check_test_execution(test_code: str, put_code: str) -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "put.py").write_text(put_code)
        (tmp / "test_put.py").write_text(f"from put import *\n\n{test_code}")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_put.py", "--tb=short", "-q"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
