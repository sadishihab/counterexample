"""Tests for engine.mutate.generate_mutants."""

import subprocess
from pathlib import Path

from engine.diff import changed_line_ranges
from engine.mutate import generate_mutants

DEMO_REPO = Path.home() / "projects" / "ibm-bob-2.0" / "counterexample-demo-checkout"

SOURCE = '''\
def inside_examples(a, b, c):
    if a > b:
        result = a + b
    else:
        result = a - b
    if a and b:
        result = result * c
    return result


def outside_examples(a, b):
    if a > b:
        return a + b
    return a
'''


def test_generate_mutants_only_inside_changed_range(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.py"
    file_path.write_text(SOURCE)

    mutants = generate_mutants(str(file_path), [(1, 8)])

    assert mutants
    for mutant in mutants:
        assert 1 <= mutant.line <= 8

    descriptions = {mutant.description for mutant in mutants}
    assert descriptions == {
        "changed > to >= at line 2",
        "changed + to - at line 3",
        "changed - to + at line 5",
        "changed and to or at line 6",
        "changed * to / at line 7",
        "changed return value to None at line 8",
    }

    for mutant in mutants:
        assert mutant.mutated_source != SOURCE

    gt_mutant = next(m for m in mutants if m.description == "changed > to >= at line 2")
    assert "a >= b" in gt_mutant.mutated_source

    add_mutant = next(m for m in mutants if m.description == "changed + to - at line 3")
    assert "a - b" in add_mutant.mutated_source

    sub_mutant = next(m for m in mutants if m.description == "changed - to + at line 5")
    assert "a + b" in sub_mutant.mutated_source

    bool_mutant = next(m for m in mutants if m.description == "changed and to or at line 6")
    assert "a or b" in bool_mutant.mutated_source

    mult_mutant = next(m for m in mutants if m.description == "changed * to / at line 7")
    assert "result / c" in mult_mutant.mutated_source

    return_mutant = next(m for m in mutants if m.description == "changed return value to None at line 8")
    assert "return None" in return_mutant.mutated_source


def test_generate_mutants_excludes_lines_outside_changed_range(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.py"
    file_path.write_text(SOURCE)

    mutants = generate_mutants(str(file_path), [(1, 8)])

    for mutant in mutants:
        assert mutant.line not in (12, 13, 14)


def test_generate_mutants_on_real_pr_diff(tmp_path: Path) -> None:
    ranges = changed_line_ranges(str(DEMO_REPO), "main", "feature/stacked-coupons")
    pricing_ranges = ranges["checkout/pricing.py"]

    pricing_source = subprocess.run(
        ["git", "show", "feature/stacked-coupons:checkout/pricing.py"],
        cwd=DEMO_REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    pricing_file = tmp_path / "pricing.py"
    pricing_file.write_text(pricing_source)

    mutants = generate_mutants(str(pricing_file), pricing_ranges)

    assert len(mutants) >= 2
