import re
import tempfile
import subprocess
from pathlib import Path

from utils import MUTPY


class MutantInfo:
    def __init__(self, mid: int, operator: str, description: str, status: str, mutant_code: str | None):
        self.id = mid
        self.operator = operator
        self.description = description
        self.status = status
        self.mutant_code = mutant_code

    def __repr__(self):
        return f"Mutant({self.id}, {self.operator}, {self.status})"


def apply_diff_line(line: str, original_lines: list[str]) -> str:
    """Apply a MutPy diff line format to generate mutant code.
    
    MutPy diff uses:
      2:     return a + b      (unchanged)
    - 2:     return a + b      (removed in mutant)
    + 2:     return a - b      (added in mutant)
    """
    m = re.match(r"^[-+]?\s*(\d+):(.*)", line)
    if not m:
        return None
    lineno = int(m.group(1))
    content = m.group(2)
    return content


def parse_mutpy_output(output: str, put_code: str) -> tuple[float, list[MutantInfo]]:
    ms_match = re.search(r"Mutation score.*?(\d+\.?\d*)%", output)
    if not ms_match:
        print("[!] Could not parse mutation score from MutPy output")
        return 0.0, []

    ms = float(ms_match.group(1))

    mutants = []
    original_lines = put_code.splitlines()

    blocks = re.split(r"- \[#\s*(\d+)\]", output)[1:]
    for i in range(0, len(blocks), 2):
        mid = int(blocks[i])
        block = blocks[i + 1]

        op_match = re.search(r"(\S+)\s+(\S+):", block)
        operator = op_match.group(1) if op_match else "UNKNOWN"

        status_match = re.search(r"\[[\d.]+\s*s\]\s*(killed|survived)", block)
        status = status_match.group(1) if status_match else "unknown"

        if status == "survived":
            mutant_lines = list(original_lines)
            for line in block.splitlines():
                m = re.match(r"^([-+])\s*(\d+):\s(.*)", line)
                if m:
                    prefix, str_lineno, content = m.group(1), m.group(2), m.group(3)
                    idx = int(str_lineno) - 1
                    if idx < len(mutant_lines) and prefix == "+":
                        mutant_lines[idx] = content

            desc_match = re.search(r"\[#\s*\d+\]\s*(.*?):", block)
            desc = f"{operator} mutation" if not desc_match else f"{desc_match.group(1)}: {operator}"
            mutant_code = "\n".join(mutant_lines)
            mutants.append(MutantInfo(mid, operator, desc.strip(), status, mutant_code))
        else:
            mutants.append(MutantInfo(mid, operator, f"{operator} mutation", status, None))

    return ms, mutants


def run_mutation_testing(put_code: str, test_code: str) -> tuple[float, list[MutantInfo], str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        put_path = tmp / "put.py"
        put_path.write_text(put_code)

        test_path = tmp / "test_put.py"
        test_path.write_text(f"from put import *\n\n{test_code}")

        result = subprocess.run(
            [str(MUTPY), "--target", "put", "--unit-test", "test_put",
             "--runner", "pytest", "-m", "-c"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=60,
        )

        output = result.stdout + result.stderr

        if result.returncode != 0:
            print(f"[!] MutPy warning (exit {result.returncode}):")
            print(output[-500:])

        ms, mutants = parse_mutpy_output(output, put_code)
        return ms, mutants, output
