FEW_SHOT_EXAMPLES = """
Example 1:
def add(a, b):
    return a + b

Tests:
def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


Example 2:
def is_positive(n):
    return n > 0

Tests:
def test_is_positive():
    assert is_positive(5) is True
    assert is_positive(-1) is False
    assert is_positive(0) is False
"""


def build_initial_prompt(put_code: str, shot: str) -> str:
    if shot == "zero":
        return (
            "Generate pytest unit tests for the following Python function. "
            "Return ONLY the test code, no explanations.\n\n"
            f"```python\n{put_code}\n```"
        )
    else:
        return (
            f"{FEW_SHOT_EXAMPLES}\n\n"
            "Now generate pytest unit tests for this function. "
            "Return ONLY the test code, no explanations.\n\n"
            f"```python\n{put_code}\n```"
        )


def build_augmented_prompt(mutant_code: str, current_test: str) -> str:
    return (
        "The following test function cannot detect the fault in the code below.\n\n"
        "Faulty code:\n"
        f"```python\n{mutant_code}\n```\n\n"
        "Current test:\n"
        f"```python\n{current_test}\n```\n\n"
        "Generate a NEW specific test case that can detect this fault. "
        "Return ONLY the new test function code, no explanations."
    )
