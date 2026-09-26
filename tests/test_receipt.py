"""Tests for engine.receipt.render_receipt."""

from engine.mutate import Mutant
from engine.receipt import ClaimVerdict, render_receipt
from engine.runner import MutantResult


def _mutant(file_path: str, line: int) -> Mutant:
    return Mutant(file_path=file_path, line=line, description="d", mutated_source="")


def test_render_receipt_bugs_found_when_claim_falsified() -> None:
    claims = [
        ClaimVerdict(
            claim_id="claim-1",
            text="Total never goes below zero.",
            verdict="FALSIFIED",
            detail="got -10.00, expected 20.00",
        ),
        ClaimVerdict(
            claim_id="claim-2",
            text="Duplicate coupon kinds raise ValueError.",
            verdict="HELD",
            detail="test passed",
        ),
    ]
    results = [
        MutantResult(mutant=_mutant("checkout/pricing.py", 56), status="killed", detail="1 failed"),
        MutantResult(mutant=_mutant("checkout/pricing.py", 63), status="survived", detail="all tests passed"),
    ]

    html = render_receipt("feat: support stacked coupons (closes #42)", claims, results)

    assert html.startswith(("<!DOCTYPE html", "<html"))
    assert "feat: support stacked coupons (closes #42)" in html
    assert "FALSIFIED" in html
    assert "HELD" in html
    assert "BUGS FOUND" in html
    assert "checkout/pricing.py:63" in html


def test_render_receipt_looks_solid_when_all_held_and_high_score() -> None:
    claims = [
        ClaimVerdict(
            claim_id="claim-1",
            text="Total never goes below zero.",
            verdict="HELD",
            detail="test passed",
        ),
        ClaimVerdict(
            claim_id="claim-2",
            text="Duplicate coupon kinds raise ValueError.",
            verdict="HELD",
            detail="test passed",
        ),
    ]
    results = [
        MutantResult(mutant=_mutant("checkout/pricing.py", 56), status="killed", detail="1 failed"),
        MutantResult(mutant=_mutant("checkout/pricing.py", 60), status="killed", detail="1 failed"),
        MutantResult(mutant=_mutant("checkout/pricing.py", 63), status="killed", detail="1 failed"),
    ]

    html = render_receipt("feat: checkout pricing with single coupon", claims, results)

    assert "LOOKS SOLID" in html
    assert "BUGS FOUND" not in html
    assert "FALSIFIED" not in html
    assert "HELD" in html


def test_render_receipt_shows_error_details_for_unscored_mutants() -> None:
    results = [
        MutantResult(
            mutant=_mutant("checkout/pricing.py", 63),
            status="error",
            detail="timed out after 30s",
        ),
        MutantResult(
            mutant=_mutant("tests/test_pricing.py", 32),
            status="error",
            detail="failed to run pytest: [Errno 2] No such file or directory: 'pytest'",
        ),
    ]

    html = render_receipt("feat: support stacked coupons (closes #42)", [], results)

    assert "Errors" in html
    assert "checkout/pricing.py:63" in html
    assert "timed out after 30s" in html
    assert "tests/test_pricing.py:32" in html
    assert "failed to run pytest: [Errno 2] No such file or directory: &#x27;pytest&#x27;" in html


def test_render_receipt_no_errors_section_when_none_present() -> None:
    results = [
        MutantResult(mutant=_mutant("checkout/pricing.py", 56), status="killed", detail="1 failed"),
    ]

    html = render_receipt("feat: checkout pricing with single coupon", [], results)

    assert "Errors" not in html
