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
