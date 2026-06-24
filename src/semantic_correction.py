import ast
import re
import sys
import tempfile
import subprocess
from pathlib import Path


def correct_semantic_errors(test_code: str, put_code: str) -> str:
    """
    Corrige asserções com valores esperados errados.
    Roda cada assert individualmente contra o PUT original;
    se falha com AssertionError, computa o valor correto e substitui.
    """
    asserts = _extract_asserts(test_code)
    if not asserts:
        return test_code

    print(f"   🔍 Corrigindo {len(asserts)} asserções semanticamente...")
    n_fixed = 0

    for i, (full_line, indent) in enumerate(asserts):
        expr = _parse_assert_expression(full_line)
        if not expr:
            continue

        actual = _compute_actual_value(expr.expression, put_code)
        if actual is None:
            continue

        fixed_line = _build_fixed_assert(full_line, expr, actual)
        if fixed_line and fixed_line != full_line:
            test_code = test_code.replace(full_line, fixed_line, 1)
            print(f"     ✅ Asserção {i+1}: {full_line.strip()} → {fixed_line.strip()}")
            n_fixed += 1

    if n_fixed:
        print(f"   ✅ {n_fixed} asserções corrigidas semanticamente")
    else:
        print(f"   ✅ Nenhuma correção semântica necessária")
    return test_code


class _AssertExpr:
    def __init__(self, expression: str, operator: str, expected: str):
        self.expression = expression.strip()
        self.operator = operator
        self.expected = expected.strip()


def _parse_assert_expression(line: str) -> _AssertExpr | None:
    stripped = line.strip()
    m = re.match(r"assert\s+(.+?)\s*(==|is|!=|is not|in|not in)\s*(.+)", stripped)
    if not m:
        return None
    return _AssertExpr(m.group(1), m.group(2), m.group(3))


def _compute_actual_value(expr: str, put_code: str) -> str | None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "put.py").write_text(put_code)
        script = (tmp / "compute.py")
        script.write_text(
            f"from put import *\n\n"
            f"try:\n"
            f"    result = {expr}\n"
            f"    print(repr(result))\n"
            f"except Exception as e:\n"
            f"    print(repr(e), file=open('/dev/null', 'w'))\n"
        )
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return None


def _build_fixed_assert(original_line: str, expr: _AssertExpr, actual_str: str) -> str | None:
    stripped = original_line.strip()

    if expr.operator not in ("==", "is"):
        return None

    try:
        actual_val = ast.literal_eval(actual_str)
    except (ValueError, SyntaxError):
        if actual_str in ("True", "False"):
            actual_val = actual_str == "True"
        else:
            return None

    current_str = expr.expected
    try:
        current_val = ast.literal_eval(current_str)
    except (ValueError, SyntaxError):
        return None

    if actual_val == current_val:
        return None

    new_expected = repr(actual_val)
    indent = original_line[:len(original_line) - len(original_line.lstrip())]
    new_line = f"{indent}assert {expr.expression} {expr.operator} {new_expected}"
    return new_line


def _extract_asserts(code: str) -> list[tuple[str, str]]:
    results = []
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("assert"):
            indent = line[:len(line) - len(line.lstrip())]
            results.append((line, indent))
    return results
