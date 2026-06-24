import sys
import tempfile
import subprocess
from pathlib import Path

from mutation import generate_mutant_files


def _extract_assertions(test_code: str) -> list[str]:
    assertions = []
    for line in test_code.splitlines():
        stripped = line.strip()
        if stripped.startswith("assert"):
            assertions.append(stripped)
    return assertions


def _assertion_kills_mutant(assertion: str, mutant_code: str) -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "mutant.py").write_text(mutant_code)

        script = tmp / "run.py"
        script.write_text(
            f"from mutant import *\n\n"
            f"{assertion}\n"
        )

        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=10,
        )

        return result.returncode != 0


def greedy_minimize(test_code: str, put_code: str, mutants_dir: str | Path | None = None) -> str:
    assertions = _extract_assertions(test_code)
    if len(assertions) <= 1:
        return test_code

    print(f"   🔍 Minimizando {len(assertions)} asserções...")

    mutants_dir = Path(mutants_dir) if mutants_dir else Path(tempfile.mkdtemp())

    if not list(mutants_dir.glob("mutant_*.py")):
        print(f"     Gerando mutantes em {mutants_dir}...")
        generate_mutant_files(put_code, mutants_dir)

    mutant_files = sorted(mutants_dir.glob("mutant_*.py"))

    if not mutant_files:
        print("   ⚠ Nenhum mutante encontrado")
        return test_code

    mutant_codes = [f.read_text() for f in mutant_files]

    kill_data = []
    for i, assertion in enumerate(assertions):
        kills = set()
        for j, mcode in enumerate(mutant_codes):
            if _assertion_kills_mutant(assertion, mcode):
                kills.add(j)
        kill_data.append((i, kills, assertion))
        print(f"     Assert {i+1}: kills {len(kills)}/{len(mutant_codes)}")

    uncovered = set(range(len(mutant_codes)))
    selected_indices = set()

    while uncovered:
        best_idx = None
        best_new = set()

        for i, kills, _ in kill_data:
            if i in selected_indices:
                continue
            new_killed = kills & uncovered
            if len(new_killed) > len(best_new):
                best_new = new_killed
                best_idx = i

        if best_idx is None or not best_new:
            break

        selected_indices.add(best_idx)
        uncovered -= best_new

    selected = {assertions[i] for i in selected_indices}
    result_lines = []
    for line in test_code.splitlines():
        stripped = line.strip()
        if stripped.startswith("assert") and stripped not in selected:
            continue
        result_lines.append(line)

    minimized = "\n".join(result_lines)
    removed = len(assertions) - len(selected)
    print(f"   ✅ {len(assertions)} → {len(selected)} asserções ({-removed})")

    return minimized
