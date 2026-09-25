"""Run pytest per mutant in parallel and record killed/survived outcomes.

Responsible for taking the mutants produced by `mutate.py`, applying each one to
a working copy of the target repo, running its pytest suite, and recording
whether the mutant was killed (a test failed) or survived (all tests passed),
in parallel across mutants.

TODO: implement isolated per-mutant pytest execution (e.g. subprocess + tempdir
worktrees) with a parallel worker pool and a killed/survived result record.
"""
