"""Tests for engine.diff.changed_line_ranges."""

from pathlib import Path

from engine.diff import changed_line_ranges

DEMO_REPO = Path.home() / "projects" / "ibm-bob-2.0" / "counterexample-demo-checkout"


def test_changed_line_ranges_finds_pricing_changes() -> None:
    ranges = changed_line_ranges(str(DEMO_REPO), "main", "feature/stacked-coupons")

    assert "checkout/pricing.py" in ranges
    assert len(ranges["checkout/pricing.py"]) >= 1
    for start, end in ranges["checkout/pricing.py"]:
        assert start >= 1
        assert end >= start


def test_changed_line_ranges_only_includes_python_files() -> None:
    ranges = changed_line_ranges(str(DEMO_REPO), "main", "feature/stacked-coupons")

    for path in ranges:
        assert path.endswith(".py")
