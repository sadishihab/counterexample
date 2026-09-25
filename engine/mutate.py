"""Generate AST mutations restricted to changed lines.

Responsible for walking the Python AST of changed files and producing mutant
variants using the operators defined in AGENTS.md (comparison flips, off-by-one,
boolean negation, arithmetic swaps, return-value tweaks), applied only to nodes
whose source lines fall within the changed line ranges from `diff.py`.

TODO: implement AST-based mutation generation restricted to diff-scoped line ranges.
"""
