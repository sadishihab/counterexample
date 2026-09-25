"""Generate AST mutations restricted to changed lines.

Walks the AST of a file and produces mutant variants using the operators
defined in AGENTS.md (comparison flips, boolean negation, arithmetic swaps,
return-value tweaks), applied only to nodes whose source line falls within
the changed line ranges reported by `diff.py`.
"""

from __future__ import annotations

import ast
import copy
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

_COMPARE_SYMBOLS: dict[type[ast.cmpop], str] = {
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Eq: "==",
    ast.NotEq: "!=",
}
_COMPARE_FLIPS: dict[type[ast.cmpop], type[ast.cmpop]] = {
    ast.Gt: ast.GtE,
    ast.GtE: ast.Gt,
    ast.Lt: ast.LtE,
    ast.LtE: ast.Lt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
}

_BOOL_SYMBOLS: dict[type[ast.boolop], str] = {ast.And: "and", ast.Or: "or"}
_BOOL_FLIPS: dict[type[ast.boolop], type[ast.boolop]] = {ast.And: ast.Or, ast.Or: ast.And}

_ARITH_SYMBOLS: dict[type[ast.operator], str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
}
_ARITH_FLIPS: dict[type[ast.operator], type[ast.operator]] = {
    ast.Add: ast.Sub,
    ast.Sub: ast.Add,
    ast.Mult: ast.Div,
    ast.Div: ast.Mult,
}


@dataclass
class Mutant:
    """A single AST mutation applied to one file."""

    file_path: str
    line: int
    description: str
    mutated_source: str


def _in_changed_ranges(lineno: int, changed_ranges: list[tuple[int, int]]) -> bool:
    return any(start <= lineno <= end for start, end in changed_ranges)


def _clone_with_mutation(
    tree: ast.Module, node_index: int, mutate: Callable[[ast.AST], None]
) -> ast.Module:
    cloned = copy.deepcopy(tree)
    target = list(ast.walk(cloned))[node_index]
    mutate(target)
    ast.fix_missing_locations(cloned)
    return cloned


def _compare_mutants(
    tree: ast.Module, index: int, node: ast.Compare, file_path: str, lineno: int
) -> list[Mutant]:
    mutants: list[Mutant] = []
    for op_index, op in enumerate(node.ops):
        flipped_type = _COMPARE_FLIPS.get(type(op))
        if flipped_type is None:
            continue

        def mutate(
            target: ast.AST, op_index: int = op_index, flipped_type: type[ast.cmpop] = flipped_type
        ) -> None:
            target.ops[op_index] = flipped_type()  # type: ignore[attr-defined]

        cloned = _clone_with_mutation(tree, index, mutate)
        description = (
            f"changed {_COMPARE_SYMBOLS[type(op)]} to {_COMPARE_SYMBOLS[flipped_type]} "
            f"at line {lineno}"
        )
        mutants.append(
            Mutant(
                file_path=file_path,
                line=lineno,
                description=description,
                mutated_source=ast.unparse(cloned),
            )
        )
    return mutants


def _boolop_mutant(
    tree: ast.Module, index: int, node: ast.BoolOp, file_path: str, lineno: int
) -> Mutant | None:
    flipped_type = _BOOL_FLIPS.get(type(node.op))
    if flipped_type is None:
        return None

    def mutate(target: ast.AST) -> None:
        target.op = flipped_type()  # type: ignore[attr-defined]

    cloned = _clone_with_mutation(tree, index, mutate)
    description = (
        f"changed {_BOOL_SYMBOLS[type(node.op)]} to {_BOOL_SYMBOLS[flipped_type]} at line {lineno}"
    )
    return Mutant(
        file_path=file_path, line=lineno, description=description, mutated_source=ast.unparse(cloned)
    )


def _binop_mutant(
    tree: ast.Module, index: int, node: ast.BinOp, file_path: str, lineno: int
) -> Mutant | None:
    flipped_type = _ARITH_FLIPS.get(type(node.op))
    if flipped_type is None:
        return None

    def mutate(target: ast.AST) -> None:
        target.op = flipped_type()  # type: ignore[attr-defined]

    cloned = _clone_with_mutation(tree, index, mutate)
    description = (
        f"changed {_ARITH_SYMBOLS[type(node.op)]} to {_ARITH_SYMBOLS[flipped_type]} at line {lineno}"
    )
    return Mutant(
        file_path=file_path, line=lineno, description=description, mutated_source=ast.unparse(cloned)
    )


def _return_none_mutant(tree: ast.Module, index: int, file_path: str, lineno: int) -> Mutant:
    def mutate(target: ast.AST) -> None:
        target.value = ast.Constant(value=None)  # type: ignore[attr-defined]

    cloned = _clone_with_mutation(tree, index, mutate)
    description = f"changed return value to None at line {lineno}"
    return Mutant(
        file_path=file_path, line=lineno, description=description, mutated_source=ast.unparse(cloned)
    )


def generate_mutants(file_path: str, changed_ranges: list[tuple[int, int]]) -> list[Mutant]:
    """Generate mutants for `file_path`, restricted to `changed_ranges`.

    Applies comparison flips, boolean negation, arithmetic swaps, and
    return-value tweaks to AST nodes whose line falls within one of the
    given inclusive (start, end) ranges. Each match produces exactly one
    mutant, with the rest of the file left untouched.
    """
    source = Path(file_path).read_text()
    tree = ast.parse(source, filename=file_path)
    nodes = list(ast.walk(tree))

    mutants: list[Mutant] = []
    for index, node in enumerate(nodes):
        lineno = getattr(node, "lineno", None)
        if lineno is None or not _in_changed_ranges(lineno, changed_ranges):
            continue

        if isinstance(node, ast.Compare):
            mutants.extend(_compare_mutants(tree, index, node, file_path, lineno))
        elif isinstance(node, ast.BoolOp):
            mutant = _boolop_mutant(tree, index, node, file_path, lineno)
            if mutant is not None:
                mutants.append(mutant)
        elif isinstance(node, ast.BinOp):
            mutant = _binop_mutant(tree, index, node, file_path, lineno)
            if mutant is not None:
                mutants.append(mutant)
        elif isinstance(node, ast.Return) and isinstance(node.value, (ast.Name, ast.Constant)):
            mutants.append(_return_none_mutant(tree, index, file_path, lineno))

    return mutants
