"""Run pytest per mutant in parallel and record killed/survived outcomes.

Takes the mutants produced by `mutate.py`, applies each one to an isolated
temp copy of the target repo, runs its pytest suite there, and records
whether the mutant was killed (a test failed) or survived (all tests
passed), running mutants in parallel across a small worker pool.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Literal

from engine.mutate import Mutant

_TIMEOUT_SECONDS = 30
_MAX_WORKERS = 4
_DETAIL_TAIL_LINES = 10


@dataclass
class MutantResult:
    """The outcome of running one mutant's test suite."""

    mutant: Mutant
    status: Literal["killed", "survived", "error"]
    detail: str


def _tail(text: str) -> str:
    lines = text.strip().splitlines()
    return "\n".join(lines[-_DETAIL_TAIL_LINES:])


def _run_single_mutant(repo_path: str, mutant: Mutant) -> MutantResult:
    if Path(mutant.file_path).is_absolute():
        # Path("/tmp/x") / "/abs/path" silently discards the left side and
        # returns "/abs/path" — an absolute mutant.file_path would make the
        # write below escape the isolated temp copy and land on the real
        # repo file instead. mutant.file_path must always be repo-relative.
        raise ValueError(f"Mutant.file_path must be repo-relative, got absolute path: {mutant.file_path}")

    tmp_dir = tempfile.mkdtemp(prefix="counterexample-mutant-")
    try:
        dest = Path(tmp_dir) / "repo"
        shutil.copytree(repo_path, dest, ignore=shutil.ignore_patterns(".git"))
        (dest / mutant.file_path).write_text(mutant.mutated_source)

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=dest,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return MutantResult(
                mutant=mutant, status="error", detail=f"timed out after {_TIMEOUT_SECONDS}s"
            )
        except OSError as exc:
            return MutantResult(mutant=mutant, status="error", detail=f"failed to run pytest: {exc}")

        output = proc.stdout or proc.stderr

        if proc.returncode == 0:
            return MutantResult(mutant=mutant, status="survived", detail="all tests passed")
        if proc.returncode == 1:
            return MutantResult(mutant=mutant, status="killed", detail=_tail(output))
        return MutantResult(
            mutant=mutant, status="error", detail=_tail(output) or f"pytest exited {proc.returncode}"
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def run_mutants(repo_path: str, mutants: list[Mutant]) -> list[MutantResult]:
    """Run each mutant's test suite in its own temp copy of the repo, in parallel."""
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        return list(executor.map(partial(_run_single_mutant, repo_path), mutants))


def mutation_score(results: list[MutantResult]) -> float:
    """Return killed / (killed + survived), ignoring errors. 0.0 if none to score."""
    killed = sum(1 for r in results if r.status == "killed")
    survived = sum(1 for r in results if r.status == "survived")
    total = killed + survived
    if total == 0:
        return 0.0
    return killed / total
