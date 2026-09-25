"""Command-line entrypoint: `counterexample review --repo PATH --base main --head BRANCH`.

Parses CLI arguments and orchestrates diff.py, mutate.py, runner.py, and
receipt.py into a single `review` command that produces a Review Receipt
for a pull request, purely from a local git repo (no GitHub API calls).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.diff import changed_line_ranges
from engine.mutate import Mutant, generate_mutants
from engine.receipt import ClaimVerdict, render_receipt
from engine.runner import mutation_score, run_mutants


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="counterexample")
    subparsers = parser.add_subparsers(dest="command", required=True)

    review = subparsers.add_parser("review", help="Review a PR by comparing a base and head ref.")
    review.add_argument("--repo", required=True, help="Path to the target git repo.")
    review.add_argument("--base", default="main", help="Base ref (default: main).")
    review.add_argument("--head", required=True, help="Head ref.")
    review.add_argument("--claims", default=None, help="Path to a JSON file of claim verdicts.")
    review.add_argument("--out", default="review-receipt.html", help="Output HTML path.")

    return parser


def _load_claim_verdicts(claims_path: str | None) -> list[ClaimVerdict]:
    if claims_path is None:
        return []
    raw = json.loads(Path(claims_path).read_text())
    return [
        ClaimVerdict(
            claim_id=item["claim_id"],
            text=item["text"],
            verdict=item["verdict"],
            detail=item["detail"],
        )
        for item in raw
    ]


def _run_review(args: argparse.Namespace) -> None:
    ranges = changed_line_ranges(args.repo, args.base, args.head)

    all_mutants: list[Mutant] = []
    for file_path, changed_ranges in ranges.items():
        if not file_path.endswith(".py"):
            continue
        full_path = str(Path(args.repo) / file_path)
        all_mutants.extend(generate_mutants(full_path, changed_ranges))

    results = run_mutants(args.repo, all_mutants)
    score = mutation_score(results)

    claim_verdicts = _load_claim_verdicts(args.claims)

    pr_title = f"{args.head} vs {args.base}"
    html = render_receipt(pr_title, claim_verdicts, results)

    out_path = Path(args.out)
    out_path.write_text(html)

    print(f"Scanned {len(ranges)} changed file(s).")
    print(f"Generated {len(all_mutants)} mutant(s).")
    print(f"Mutation score: {score * 100:.0f}%")
    if claim_verdicts:
        print(f"Loaded {len(claim_verdicts)} claim(s).")
    print(f"Review Receipt written to {out_path}")


def main() -> None:
    """Entry point registered as the `counterexample` console script."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "review":
        _run_review(args)


if __name__ == "__main__":
    main()
