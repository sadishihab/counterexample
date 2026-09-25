"""Parse a PR diff into changed line ranges per file.

Responsible for turning a `git diff` (or GitHub PR diff) between a base and head
ref into a structured mapping of file path -> changed line ranges, so downstream
mutation testing can be restricted to only the lines a PR actually touches.

TODO: implement diff parsing (e.g. via `git diff --unified=0` or a unidiff parser)
and produce a typed structure of per-file changed line ranges.
"""
