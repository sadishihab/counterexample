"""Parse a PR diff into changed line ranges per file.

Turns a `git diff` between a base and head ref into a mapping of file path ->
changed line ranges, so downstream mutation testing can be restricted to only
the lines a PR actually touches.
"""

from __future__ import annotations

import re
import subprocess

_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def changed_line_ranges(repo_path: str, base: str, head: str) -> dict[str, list[tuple[int, int]]]:
    """Return changed line ranges per Python file, from `base` to `head`.

    Each range is an inclusive (start_line, end_line) pair of lines added or
    modified in `head` relative to `base`, as reported by a zero-context
    `git diff`. Files with only deleted lines, and non-Python files, are
    omitted.
    """
    diff_output = subprocess.run(
        ["git", "diff", "--unified=0", f"{base}..{head}"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    ranges: dict[str, list[tuple[int, int]]] = {}
    current_path: str | None = None

    for line in diff_output.splitlines():
        if line.startswith("+++ "):
            new_file = line[len("+++ ") :]
            if new_file == "/dev/null":
                current_path = None
                continue
            current_path = new_file.removeprefix("b/")
            if not current_path.endswith(".py"):
                current_path = None
            continue

        if current_path is None:
            continue

        match = _HUNK_HEADER.match(line)
        if not match:
            continue

        start = int(match.group(1))
        count = int(match.group(2)) if match.group(2) is not None else 1
        if count == 0:
            continue

        ranges.setdefault(current_path, []).append((start, start + count - 1))

    return ranges
