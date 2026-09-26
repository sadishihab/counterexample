"""Render the HTML Review Receipt.

Takes the extracted PR claims (with their falsify-claim verdicts) and the
mutation testing results and renders a single self-contained HTML report
summarizing the evidence for or against the PR.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Literal

from engine.runner import MutantResult, mutation_score

_PASS_THRESHOLD = 0.8


@dataclass
class ClaimVerdict:
    """The falsify-claim outcome for one extracted PR claim."""

    claim_id: str
    text: str
    verdict: Literal["FALSIFIED", "HELD"]
    detail: str


def _claim_row(claim: ClaimVerdict) -> str:
    css_class = "falsified" if claim.verdict == "FALSIFIED" else "held"
    label = "✗ FALSIFIED" if claim.verdict == "FALSIFIED" else "✓ HELD"
    return f"""
    <div class="claim {css_class}">
      <div class="claim-label">{label}</div>
      <div class="claim-text">{escape(claim.text)}</div>
      <div class="claim-detail">{escape(claim.detail)}</div>
    </div>"""


def _focus_map(mutant_results: list[MutantResult]) -> list[tuple[str, int]]:
    distinct: list[tuple[str, int]] = []
    for result in mutant_results:
        if result.status != "survived":
            continue
        key = (result.mutant.file_path, result.mutant.line)
        if key not in distinct:
            distinct.append(key)
    return distinct


def _error_item(result: MutantResult) -> str:
    return f"""
    <div class="error-item">
      <code>{escape(result.mutant.file_path)}:{result.mutant.line}</code>
      <pre>{escape(result.detail)}</pre>
    </div>"""


def render_receipt(
    pr_title: str,
    claim_verdicts: list[ClaimVerdict],
    mutant_results: list[MutantResult],
) -> str:
    """Render a single self-contained HTML Review Receipt."""
    score = mutation_score(mutant_results)
    bugs_found = any(claim.verdict == "FALSIFIED" for claim in claim_verdicts) or score < _PASS_THRESHOLD

    banner_class = "bugs-found" if bugs_found else "looks-solid"
    banner_text = "BUGS FOUND" if bugs_found else "LOOKS SOLID"

    claim_rows = "".join(_claim_row(claim) for claim in claim_verdicts) or "<p>No claims extracted.</p>"

    focus_map = _focus_map(mutant_results)
    if focus_map:
        focus_items = "".join(
            f"<li><code>{escape(file_path)}:{line}</code></li>" for file_path, line in focus_map
        )
        focus_section = f"""
        <p>These lines need human review — the PR's tests did not catch a bug here:</p>
        <ul class="focus-map">{focus_items}</ul>"""
    else:
        focus_section = "<p>No surviving mutants — every mutation on changed lines was caught.</p>"

    errors = [result for result in mutant_results if result.status == "error"]
    if errors:
        error_items = "".join(_error_item(result) for result in errors)
        errors_section = f"""
        <h2>Errors</h2>
        <p>{len(errors)} mutant(s) could not be scored — investigate before trusting the score above:</p>
        {error_items}"""
    else:
        errors_section = ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Review Receipt — {escape(pr_title)}</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    margin: 0;
    padding: 2rem;
    background: #f7f7f8;
    color: #1a1a1a;
  }}
  h1 {{ margin: 0 0 0.5rem 0; font-size: 1.5rem; }}
  h2 {{ margin-top: 2rem; font-size: 1.1rem; }}
  .banner {{
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-weight: bold;
    color: #fff;
    margin-bottom: 1.5rem;
  }}
  .banner.bugs-found {{ background: #c0392b; }}
  .banner.looks-solid {{ background: #27ae60; }}
  .claim {{
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
  }}
  .claim.falsified {{ background: #fdecea; border-left: 4px solid #c0392b; }}
  .claim.held {{ background: #eafaf1; border-left: 4px solid #27ae60; }}
  .claim-label {{ font-weight: bold; }}
  .claim-text {{ margin-top: 0.25rem; }}
  .claim-detail {{ margin-top: 0.25rem; color: #555; font-size: 0.9rem; }}
  .score {{ font-size: 1.75rem; font-weight: bold; }}
  .focus-map {{ padding-left: 1.25rem; }}
  .focus-map li {{ margin-bottom: 0.25rem; }}
  code {{ background: #eee; padding: 0.1rem 0.3rem; border-radius: 3px; }}
  .error-item {{
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
    background: #fff8e1;
    border-left: 4px solid #f39c12;
  }}
  .error-item pre {{
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0.5rem 0 0 0;
    font-size: 0.85rem;
  }}
</style>
</head>
<body>
  <h1>Review Receipt: {escape(pr_title)}</h1>
  <div class="banner {banner_class}">{banner_text}</div>

  <h2>Claims</h2>
  {claim_rows}

  <h2>Mutation testing</h2>
  <p class="score">{score * 100:.0f}%</p>
  {focus_section}
  {errors_section}
</body>
</html>
"""
