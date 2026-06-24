import argparse
import os
import sys
import textwrap
from pathlib import Path
from dotenv import load_dotenv

from llm_option import llm_generate
from prompts import build_initial_prompt, build_augmented_prompt
from mutation import run_mutation_testing
from refinement import refine_test


load_dotenv()


def run_pipeline(put_path: str, llm: str = "gemini", shot: str = "zero", max_iterations: int = 3):
    print("╔════════════════════════════════════════════╗")
    print("║         MuTAP - Test Generation           ║")
    print("║   LLM + Mutation Testing Feedback Loop    ║")
    print("╚════════════════════════════════════════════╝")
    print()

    put_code = Path(put_path).read_text()
    print(f"📄 PUT: {Path(put_path).name}")
    print(f"🔤 LLM: {llm.upper()} | Shot: {shot}")
    print()

    print("🤖 [LLM] Gerando teste inicial...")
    prompt = build_initial_prompt(put_code, shot)
    raw_test = llm_generate(prompt, llm)
    test_code = refine_test(raw_test, put_code, llm)
    print(f"   → Teste gerado:\n{textwrap.indent(test_code, '     ')}")
    print()

    print("🧬 Executando teste de mutação...")
    ms, mutants, output = run_mutation_testing(put_code, test_code)
    print(f"   → MS inicial: {ms}%")

    survivors = [m for m in mutants if m.status == "survived"]
    killed = [m for m in mutants if m.status == "killed"]
    print(f"   → Mortos: {len(killed)}  |  Sobreviventes: {len(survivors)}")
    print()

    iteration = 0
    all_tests = [test_code]

    while survivors and iteration < max_iterations:
        iteration += 1
        mutant = survivors[0]
        print(f"🔄 [Iteração {iteration}/{max_iterations}] Prompt aumentado...")
        print(f"   Mutante #{mutant.id}: {mutant.operator} - {mutant.description}")
        print(f"   Código mutante:\n{textwrap.indent(mutant.mutant_code, '     ')}")
        print()

        current_test = "\n\n".join(all_tests)
        aug_prompt = build_augmented_prompt(mutant.mutant_code, current_test)
        new_raw = llm_generate(aug_prompt, llm)
        new_test = refine_test(new_raw, put_code, llm)
        all_tests.append(new_test)

        combined = "\n\n".join(all_tests)
        ms_new, mutants, _ = run_mutation_testing(put_code, combined)
        print(f"   → MS após iteração {iteration}: {ms_new}%")

        survivors = [m for m in mutants if m.status == "survived"]
        killed = [m for m in mutants if m.status == "killed"]
        print(f"   → Mortos: {len(killed)}  |  Sobreviventes: {len(survivors)}")
        print()
        ms = ms_new

    print("📊 RESULTADO FINAL")
    print(f"   MS final: {ms}%")
    if ms < 100:
        print(f"   Mutantes sobreviventes: {len(survivors)}")


def main():
    parser = argparse.ArgumentParser(description="MuTAP: Test Generation with LLMs + Mutation Testing")
    parser.add_argument("put", help="Path to the Program Under Test (.py file)")
    parser.add_argument("--llm", choices=["gemini", "ollama"], default="gemini", help="LLM to use")
    parser.add_argument("--shot", choices=["zero", "few"], default="zero", help="Prompt type")
    parser.add_argument("--max-iterations", type=int, default=3, help="Max augmentation iterations")
    args = parser.parse_args()

    if not os.path.exists(args.put):
        print(f"Error: file not found: {args.put}")
        sys.exit(1)

    run_pipeline(args.put, args.llm, args.shot, args.max_iterations)


if __name__ == "__main__":
    main()

"""
Uso:
    python mutap_pipeline.py put_examples/calculator.py
    python mutap_pipeline.py put_examples/calculator.py --llm ollama
    python mutap_pipeline.py put_examples/calculator.py --shot few
"""
