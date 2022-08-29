#!/usr/bin/env python3
import ast
import sys
from decimal import Decimal
from fractions import Fraction  # TODO support display like this


ignores = dir(__builtins__)
# type_comment and ignore_types fields

# Problem: AST does not include normal comments
# Note that function names get capitalized

# TODO math constant, e, pi, ...
# numpy matmul
# Infinity / negative infinity (floats)
# all -> \forAll
# any -> \exists
# set operations
# abs(x) -> ||x||
# min, max
# math.ceil, floor
# trigonometry
# These should be doable with simple text replacements

# Idea
# set an attribute to check if already in math mode
# this reduces the number of delimiters
# $x$ + $y$ -> $x + y$ which is much more natural


class Python2Algorithm(ast.NodeVisitor):
    INDENTATION = "   "
    level = 0
    _lineno = -1
    _suppress_semicolon = False

    def visit_Module(self, node: ast.Module):
        docstring = ast.get_docstring(node)
        if docstring:
            # Or KwData
            # There is also \caption
            # and \label
            self._print(r"\KwResult{" + docstring + "}\n")
            for v in node.body[1:]:
                self.visit(v)
        else:
            for v in node.body:
                self.visit(v)

    def visit(self, node: ast.AST):
        if hasattr(node, "lineno") and node.lineno > self._lineno:
            if self._lineno != -1 and not self._suppress_semicolon:  # The first one
                print(r" \; ", end="\n")
                print(self.INDENTATION * self.level, end="")
            self._lineno = node.lineno
            self._suppress_semicolon = False
        return super().visit(node)

    def _print(self, value, end=" ", *kwarg, **kwargs):
        print(value, end=end, *kwarg, **kwargs)

    def visit_Constant(self, node):
        # https://stackoverflow.com/questions/67524641/convert-multiple-isinstance-checks-to-structural-pattern-matching
        # number
        # string
        # None
        # tuples
        # frozensets
        match node.value:
            case int():
                self._print(str(node.value))
            case str():
                self._print("``" + node.value + "'")
            case float() | Decimal():
                # rounding may be not desired! This probably confuses more so leave it out
                self._print(str(node.value))
            case frozenset():
                self._print(str(node.value))
            case tuple():
                self._print(str(node.value))
            case None:
                self._print(r"$\blacktriangle$")
            case _:
                raise TypeError("Unsupported type")

    def visit_FormattedValue(self, node: ast.FormattedValue):
        self.visit(node.value)
        # TODO this is just python
        match node.conversion:
            case -1:
                pass
            case 115:
                self._print("!s")
            case 114:
                self._print("!r")
            case 97:
                self._print("!a")
        if node.format_spec:
            self.visit(node.format_spec)

    def visit_JoinedStr(self, node: ast.JoinedStr):
        # TODO this is just python
        self._print("f'")
        for n in node.values:
            self.visit(n)
        self._print("'")

    def visit_List(self, node: ast.List):
        self._print("[")
        for n in node.elts[:-1]:
            self.visit(n)
            self._print(r",")
        if len(node.elts):
            self.visit(node.elts[-1])
        self._print("]")
        if isinstance(node.ctx, ast.Store):
            self._print(r"$\gets$")

    def visit_Tuple(self, node: ast.Tuple):
        self._print("(")
        for n in node.elts[:-1]:
            self.visit(n)
            self._print(r",")
        if len(node.elts):
            self.visit(node.elts[-1])
        self._print(")")
        if isinstance(node.ctx, ast.Store):
            self._print(r"$\gets$")

    def visit_Set(self, node: ast.Set):
        if len(node.elts) == 0:
            self._print(r"$\emptyset$")
        else:
            self._print(r"$\{$")
            for n in node.elts[:-1]:
                self.visit(n)
                self._print(r", ")
            if len(node.elts):
                self.visit(node.elts[-1])
            self._print(r"$\}$")

    def visit_Dict(self, node: ast.Dict):
        if not len(node.keys):
            self._print(r"Map()")  # TODO
        else:
            self._print(r"$\{$")
            for k, v in zip(node.keys, node.values):
                self.visit(k)
                self._print(r"\mapsto")
                self.visit(v)
                self._print(r", ")
            self._print(r"$\}$")

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self._print("$" + node.id + "$")
        elif isinstance(node.ctx, ast.Store):
            self._print(f"${node.id} \\gets $")
        elif isinstance(node.ctx, ast.Store):
            # TODO
            self._print(f"DEL {node.id}")

    def visit_Starred(self, node: ast.Starred):
        self._print(f"*")  # TODO just python
        self.visit(node.value)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        match node.op:
            case ast.UAdd():
                self._print("+")
            case ast.USub():
                self._print("-")
            case ast.Not():
                self._print(r"$\neg$")
            case ast.Invert():
                # self._print(r"\overline{")
                self._print(r" \ensuremath{\mathord{\sim}} ")
                self.visit(node.operand)
                # self._print(r"}")
                return
        self.visit(node.operand)

    def visit_BinOp(self, node: ast.BinOp):
        # Handle div as a special case because it requires a different order
        if isinstance(node.op, ast.Div | ast.FloorDiv):
            if isinstance(node.op, ast.FloorDiv):
                self._print(r"$\lfloor$")
            self._print(r"$\frac{ ")
            self.visit(node.left)
            self._print(r"}{")
            self.visit(node.right)
            self._print(r"}$")
            if isinstance(node.op, ast.FloorDiv):
                self._print(r"$\rfloor$")
        elif isinstance(node.op, ast.Pow):
            self._print("$")
            self.visit(node.left)
            self._print(r"^{")
            self.visit(node.right)
            self._print(r"}$")
        else:
            self.visit(node.left)
            match node.op:
                case ast.Add():
                    self._print("+")
                case ast.Sub():
                    self._print("-")
                case ast.Mult():
                    self._print(r"$\cdot$")
                case ast.Mod():
                    self._print(r"$\mod$")
                # https://tex.stackexchange.com/questions/14227/bitwise-operator-in-pseudo-code
                case ast.LShift():
                    self._print(r"$\ll$")
                case ast.RShift():
                    self._print(r"$\gg$")
                case ast.BitOr():
                    self._print(r"$\mathbin{|}$")
                case ast.BitAnd():
                    self._print(r"$\mathbin{\&}$")
                case ast.BitXor():
                    self._print(r"$\mathbin{\oplus}$")
                case ast.MatMult():
                    self._print(r"$\times$")
                case _:
                    raise TypeError("Unexpected Binary Operation")
            self.visit(node.right)

    def visit_BoolOp(self, node: ast.BoolOp):
        operator = r"$\land$ " if isinstance(node.op, ast.And) else r"$\mathbin{\lor}$"
        self.visit(node.values[0])
        for v in node.values[1:]:
            self._print(operator)
            self.visit(v)

    def visit_Compare(self, node: ast.Compare):
        self.visit(node.left)
        for op, comp in zip(node.ops, node.comparators):
            match op:
                case ast.Eq():
                    self._print(r"$=$")
                case ast.NotEq():
                    self._print(r"$\ne$")
                case ast.Lt():
                    self._print(r"$<$")
                case ast.LtE():
                    self._print(r"$\leq$")
                case ast.Gt():
                    self._print(r"$>$")
                case ast.GtE():
                    self._print(r"$\geq$")
                case ast.Is():
                    self._print(r"$\equiv$")
                case ast.IsNot():
                    self._print(r"$\not\equiv$")
                case ast.In():
                    self._print(r"$\in$")
                case ast.NotIn():
                    self._print(r"$\not\in$")
                case _:
                    raise TypeError("Unexpected Comparison Operation")
            self.visit(comp)

    def visit_Call(self, node: ast.Call):
        # TODO
        # self._print(f"CALL ")
        if isinstance(node.func, ast.Name):
            if node.func.id == "len":
                self._print(r"$\lvert$")
                for v in node.args:
                    self.visit(v)
                for v in node.keywords:
                    self.visit(v)
                self._print(r"$\rvert$")
                return
            elif node.func.id in ignores:
                self._print("\\" + node.func.id, end="")
            else:
                self._print("\\" + node.func.id.capitalize(), end="")
        elif isinstance(node.func, ast.Attribute):
            # self.visit(node.func)
            self._print("\\" + node.func.attr, end="")
        # self.visit(node.func)
        self._print("{")
        # self._print(r"(")
        for v in node.args:
            self.visit(v)
        for v in node.keywords:
            self.visit(v)
        # self._print(r")")
        self._print("}")

    def visit_keyword(self, node: ast.keyword):
        self._print(f"{node.arg}=")
        self.visit(node.value)

    # IfExp (ternary)

    def visit_Attribute(self, node: ast.Attribute):
        self.visit(node.value)
        self._print("." + node.attr)
        # TODO handle ctx: load, store, del

    def visit_NamedExpr(self, node: ast.NamedExpr):
        self.visit(node.target)
        self._print(r" := ")
        self.visit(node.value)

    # TODO Subscript, Slice
    # https://docs.python.org/3/library/ast.html?highlight=ast#ast.Subscript

    # TODO Comprehensions
    # This could be really nice in latex

    # Assign
    # AnnAssign
    # AugAssign
    # Raise
    # Assert
    # Delete
    # Pass
    # Import
    # ImportFrom
    # alias

    def visit_If(self, node: ast.If):
        self._suppress_semicolon = True
        self._print(r"\If{")
        self.level += 1
        self.visit(node.test)
        self._print(r"}{")
        for n in node.body:
            self.visit(n)
        self._print(r"}")
        if len(node.orelse):
            self._suppress_semicolon = True
            self._print(r"{")
            for v in node.orelse:
                self.visit(v)
            self._print(r"}")
        self._suppress_semicolon = True
        self.level -= 1

    def visit_For(self, node: ast.For):
        self._suppress_semicolon = True
        self._print(r"\ForAll{")
        self.level += 1
        self.visit(node.target)
        self._print(r"$\in$")
        self.visit(node.iter)
        self._print(r"}{")
        for n in node.body:
            self.visit(n)
        self._print(r"}")
        if len(node.orelse):
            self._suppress_semicolon = True
            self._print(r"{")
            for v in node.orelse:
                self.visit(v)
            self._print(r"}")
        self._suppress_semicolon = True
        self.level -= 1

    def visit_While(self, node: ast.While):
        self._suppress_semicolon = True
        self._print(r"\While{")
        self.level += 1
        self.visit(node.test)
        self._print(r"}{")
        for n in node.body:
            self.visit(n)
        self._print(r"}")
        if len(node.orelse):
            self._suppress_semicolon = True
            self._print(r"{")
            for v in node.orelse:
                self.visit(v)
            self._print(r"}")
        self._suppress_semicolon = True
        self.level -= 1

    # Break
    # Continue
    # Try
    # ExceptHandler
    # With
    # withitem

    # Match
    # match_case
    # MatchValue
    # MatchSingleton
    # MatchSequence
    # MatchStar
    # MatchMapping
    # MatchClass
    # MatchAs
    # MatchOr

    def visit_FunctionDef(self, node):
        # self._print("\\SetKwFunction{" + node.name + "}{" + node.name + "}")
        # self._print("DEF " + node.name)
        # doc = ast.get_docstring(node)
        # doc = doc if doc else ""
        self._print(r"\Fn{" + "\\" + node.name.capitalize() + "{")
        self.visit(node.args)
        self._print("}}{")
        self._suppress_semicolon = True
        self.level += 1
        # node.decorator_list
        for v in node.body:
            self.visit(v)
        self._print("}")
        self.level -= 1

    # Lambda
    # arguments
    # arg
    # Return
    # Yield
    # YieldFrom
    # Global
    # Nonlocal
    # ClassDef
    # AsyncFunctionDef
    # Await
    # AsyncFor
    # AsyncWith


class KwFunctionExtractor(ast.NodeVisitor):
    needs = set()

    def visit_Call(self, node: ast.Call):
        # TODO
        # self._print(f"CALL ")
        if isinstance(node.func, ast.Name):
            if node.func.id in ignores:
                self.needs.add(node.func.id)
            else:
                self.needs.add(node.func.id.capitalize())
        elif isinstance(node.func, ast.Attribute):
            # self.visit(node.func)
            self.needs.add(node.func.attr)
        for v in node.args:
            self.visit(v)
        for v in node.keywords:
            self.visit(v)

    def visit_FunctionDef(self, node):
        name = node.name.capitalize()
        print("\\SetKwFunction{" + name + "}{" + name + "}")
        self.visit(node.args)
        # node.decorator_list
        for v in node.body:
            self.visit(v)


def main():
    with open("bench.py") as f:
        source = "".join(f.readlines())
        tree = ast.parse(source, mode="exec")
        print(ast.dump(tree, indent=4), file=sys.stderr)
    # To allow recursive function definitions we run it before
    # for f in ignores:
    # print("\\SetKwFunction{" + f + "}{" + f + "}")
    kwe = KwFunctionExtractor()
    kwe.visit(tree)
    print("\SetKwProg{Fn}{Function}{:}{end}")
    for f in kwe.needs:
        print("\\SetKwFunction{" + f + "}{" + f + "}")
    Python2Algorithm().visit(tree)


if __name__ == "__main__":
    main()
