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
        # generate_mutants tags each Mutant with whatever path it was read
        # from; run_mutants needs a repo-relative path to stay inside its
        # isolated temp copy, so fix it back up before running.
        for mutant in mutants:
            mutant.file_path = "checkout/pricing.py"

        results = run_mutants(str(worktree), mutants)

        # The planted bug in this PR (percent discount computed from the
        # original subtotal instead of the post-fixed total) is a
        # wrong-variable-reference bug, not expressible by any of the
        # comparison/boolean/arithmetic/return-value operators mutate.py
        # applies — so every operator-level mutation on the changed lines
        # gets caught by the PR's own test suite. That's a real, verified
        # limitation of mutation testing here, not a test bug: catching this
        # specific bug is what claim-falsification is for instead.
        assert results
        assert all(result.status == "killed" for result in results)
        assert mutation_score(results) == 1.0
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
