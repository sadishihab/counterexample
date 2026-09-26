"""Tests for engine.cli via the installed `counterexample` console script."""

import subprocess
import sys
from pathlib import Path

DEMO_REPO = Path.home() / "projects" / "ibm-bob-2.0" / "counterexample-demo-checkout"


def test_review_command_produces_receipt(tmp_path: Path) -> None:
    out_path = tmp_path / "receipt.html"
    counterexample_bin = Path(sys.executable).parent / "counterexample"

    proc = subprocess.run(
        [
            str(counterexample_bin),
            "review",
            "--repo",
            str(DEMO_REPO),
            "--base",
            "main",
            "--head",
            "feature/stacked-coupons",
            "--out",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr

    assert out_path.exists()
    html = out_path.read_text()
    assert "LOOKS SOLID" in html or "BUGS FOUND" in html

    assert "mutation score" in proc.stdout.lower()


def test_review_checks_out_head_before_scanning(tmp_path: Path) -> None:
    """The demo repo starts on `main`; review's own --head checkout must fix that up."""
    counterexample_bin = Path(sys.executable).parent / "counterexample"

    subprocess.run(["git", "checkout", "main"], cwd=DEMO_REPO, check=True, capture_output=True, text=True)
    try:
        out_path = tmp_path / "receipt.html"

        proc = subprocess.run(
            [
                str(counterexample_bin),
                "review",
                "--repo",
                str(DEMO_REPO),
                "--base",
                "main",
                "--head",
                "feature/stacked-coupons",
                "--out",
                str(out_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        assert proc.returncode == 0, proc.stderr
        assert "Checking out feature/stacked-coupons" in proc.stdout

        # Without the checkout fix, this run would scan main's working tree
        # against feature/stacked-coupons' line numbers and silently produce
        # a bogus 0%/empty result instead of the real mutation score.
        assert "Mutation score: 0%" not in proc.stdout
        assert "Generated 0 mutant" not in proc.stdout
        assert "Mutation score: 100%" in proc.stdout
    finally:
        subprocess.run(["git", "checkout", "main"], cwd=DEMO_REPO, check=True, capture_output=True, text=True)
