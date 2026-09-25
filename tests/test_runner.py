"""Tests for engine.runner."""

import subprocess
from pathlib import Path

from engine.diff import changed_line_ranges
from engine.mutate import Mutant, generate_mutants
from engine.runner import MutantResult, mutation_score, run_mutants

DEMO_REPO = Path.home() / "projects" / "ibm-bob-2.0" / "counterexample-demo-checkout"


def test_run_mutants_on_real_pr_yields_killed_and_survived(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    subprocess.run(
        ["git", "worktree", "add", str(worktree), "feature/stacked-coupons"],
        cwd=DEMO_REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        ranges = changed_line_ranges(str(DEMO_REPO), "main", "feature/stacked-coupons")
        pricing_ranges = ranges["checkout/pricing.py"]

        mutants = generate_mutants(str(worktree / "checkout" / "pricing.py"), pricing_ranges)
        assert mutants

        results = run_mutants(str(worktree), mutants)

        statuses = {result.status for result in results}
        assert "killed" in statuses
        assert "survived" in statuses
    finally:
        subprocess.run(
            ["git", "worktree", "remove", str(worktree), "--force"],
            cwd=DEMO_REPO,
            check=True,
            capture_output=True,
            text=True,
        )


def _fake_result(status: str) -> MutantResult:
    mutant = Mutant(file_path="f.py", line=1, description="d", mutated_source="")
    return MutantResult(mutant=mutant, status=status, detail="")  # type: ignore[arg-type]


def test_mutation_score_ignores_errors() -> None:
    results = [
        _fake_result("killed"),
        _fake_result("killed"),
        _fake_result("survived"),
        _fake_result("error"),
    ]
    assert mutation_score(results) == 2 / 3


def test_mutation_score_no_killed_or_survived_is_zero() -> None:
    results = [_fake_result("error")]
    assert mutation_score(results) == 0.0


def test_mutation_score_all_killed_is_one() -> None:
    results = [_fake_result("killed"), _fake_result("killed")]
    assert mutation_score(results) == 1.0
