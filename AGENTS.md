# AGENTS.md

## Project purpose

Counterexample is a PR verification tool. For a given pull request, it extracts the
behavior claims the PR makes (from the diff and any linked issue), writes adversarial
tests to try to falsify each claim, and runs diff-scoped mutation testing to measure
whether the PR's own tests would actually catch a bug in the changed lines. It outputs
a "Review Receipt" summarizing the evidence.

## Core principle

Evidence over opinions. Every finding must be backed by an executed test.

## Scope

- Python repositories using pytest only.
- Mutations are applied only to lines changed by the PR (diff-scoped), never to
  unrelated code.

## Mutation operators

- Comparison flips: `>` <-> `>=`, `<` <-> `<=`, `==` <-> `!=`
- Off-by-one on integer constants
- Boolean negation: `and` <-> `or`, removal of `not`
- Arithmetic swaps: `+` <-> `-`, `*` <-> `/`
- Return-value tweaks: `return x` -> `return None` / `return 0`

## Code rules

- Type hints everywhere.
- Prefer the standard library first; avoid unnecessary dependencies.
- Small, pure functions.
- No network calls in the engine.
- Every module has tests under `tests/`.

## Attribution rule

Note in every commit message whether the work was done by "IBM Bob" or "Claude Code".
