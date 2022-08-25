#!/usr/bin/env python3
import ast
import sys
from decimal import Decimal
from fractions import Fraction  # TODO

with open("bench.py") as f:
    source = "".join(f.readlines())
    tree = ast.parse(source, mode="exec")
    print(ast.dump(tree, indent=4), file=sys.stderr)

# type_comment


class FuncLister(ast.NodeVisitor):
    INDENTATION = "   "
    level = 0
    _lineno = -1

    def visit(self, node: ast.AST):
        if hasattr(node, "lineno") and node.lineno > self._lineno:
            if self._lineno != -1:  # The first one
                self._print(r" \; ", end="\n")
            self._lineno = node.lineno
        return super().visit(node)

    def _print(self, value, end=" ", *kwarg, **kwargs):
        if end != "\n":
            print(value, end=end, *kwarg, **kwargs)
        else:
            print(self.INDENTATION * self.level + value, *kwarg, **kwargs)

    def visit_FunctionDef(self, node):
        self._print("FUNCTION" + node.name)
        self.generic_visit(node)

    def visit_Constant(self, node):
        # https://stackoverflow.com/questions/67524641/convert-multiple-isinstance-checks-to-structural-pattern-matching
        # number
        # string
        # None
        # tuples
        # frozensets
        match node.value:
            case int():
                self._print(str(node.value), end=" ")
            case str():
                self._print("'" + node.value + "'", end=" ")
            case float() | Decimal():
                # rounding may be not desired!
                self._print(str(round(node.value, 5)), end=" ")
            case frozenset():
                self._print(str(node.value))
            case tuple():
                self._print(str(node.value))
            case None:
                self._print(r"$\bot$ ")
            case _:
                raise TypeError("Unsupported type")

    def visit_Set(self, node):
        if len(node.elts) == 0:
            this._print(r"$\emptyset$", end="")
        else:
            self._print(r"\{", end="")
            for n in node.elts:
                self.visit(n)
                self._print(r", ", end="")
            self._print(r"\}")

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self._print("$" + node.id + "$", end=" ")
        elif isinstance(node.ctx, ast.Store):
            self._print(f"${node.id} \\gets $", end=" ")
        elif isinstance(node.ctx, ast.Store):
            # TODO
            self._print(f"DEL {node.id}")

    def visit_For(self, node):
        self._print(r"\forAll{", end="")
        self.level += 1
        self.generic_visit(node.target)
        self.generic_visit(node.iter)
        self._print(r"}{")
        for n in node.body:
            self.visit(n)
        self._print(r"}")
        # TODO node.orelse
        self.level -= 1

    def visit_If(self, node):
        self._print(r"\If{", end="")
        self.level += 1
        self.generic_visit(node.test)
        self._print(r"}{")
        for n in node.body:
            self.visit(n)
        self._print(r"}")
        # TODO node.orelse
        self.level -= 1


FuncLister().visit(tree)
