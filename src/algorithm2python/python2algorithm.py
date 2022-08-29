#!/usr/bin/env python3
import ast
import sys
from decimal import Decimal
from fractions import Fraction  # TODO support display like this
from typing import Any


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

MATH = 1
NOMATH = -1


class Python2Algorithm(ast.NodeVisitor):
    INDENTATION = "   "
    level = 0
    _lineno = -1
    _suppress_semicolon = False
    _math_level = 0

    def __init__(self, output=sys.stdout) -> None:
        super().__init__()
        self._output_file = output

    def define_Functions_First(self, node: ast.AST):
        # to allow recursive function definitions we run it before
        # for f in ignores:
        # print("\\SetKwFunction{" + f + "}{" + f + "}")
        kwe = KwFunctionExtractor()
        kwe.visit(node)
        if kwe.needs:
            self._print("\\setkwprog{Fn}{Function}{:}{end}")
        for f in kwe.needs:
            self._print("\\SetKwFunction{" + f + "}{" + f + "}")

    def visit_Module(self, node: ast.Module):
        self.define_Functions_First(node)

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
        # Finally
        if self._math_level > 0:
            # Finish the last open math env
            self._print("$")

    def visit(self, node: ast.AST):
        if hasattr(node, "lineno") and node.lineno > self._lineno:
            if self._lineno != -1 and not self._suppress_semicolon:  # The first one
                if self._math_level > 0:
                    # Finish the last open math env on the line
                    self._print("$")
                    self._math_level = 0
                self._print(r" \; ", end="\n")
                self._print(self.INDENTATION * self.level, end="")
            self._lineno = node.lineno
            self._suppress_semicolon = False
        return super().visit(node)

    def _print(self, value: str, math=None, end=" ", *kwarg, **kwargs):
        if math:
            if math == MATH:
                if self._math_level == 0:
                    value = "$" + value
                self._math_level = 1
            if math == NOMATH:
                if self._math_level == 1:
                    value = "$" + value
                self._math_level = 0
        print(value, end=end, file=self._output_file, *kwarg, **kwargs)

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
                self._print("``" + node.value + "'", math=NOMATH)
            case float() | Decimal():
                # rounding may be not desired! This probably confuses more so leave it out
                self._print(str(node.value))
            case frozenset():
                self._print(str(node.value))
            case tuple():
                self._print(str(node.value))
            case None:
                self._print(r"\blacktriangle", math=MATH)
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
            self._print(r"\gets", math=MATH)

    def visit_Tuple(self, node: ast.Tuple):
        self._print("(")
        for n in node.elts[:-1]:
            self.visit(n)
            self._print(r",")
        if len(node.elts):
            self.visit(node.elts[-1])
        self._print(")")
        if isinstance(node.ctx, ast.Store):
            self._print(r"\gets", math=MATH)

    def visit_Set(self, node: ast.Set):
        if len(node.elts) == 0:
            self._print(r"\emptyset", math=MATH)
        else:
            self._print(r"\{", math=MATH)
            for n in node.elts[:-1]:
                self.visit(n)
                self._print(r",")
            if len(node.elts):
                self.visit(node.elts[-1])
            self._print(r"\}", math=MATH)

    def visit_Dict(self, node: ast.Dict):
        if not len(node.keys):
            self._print(r"Map()")  # TODO
        else:
            self._print(r"\{", math=MATH)
            for k, v in zip(node.keys, node.values):
                self.visit(k)
                self._print(r"\mapsto", math=MATH)
                self.visit(v)
                self._print(r",")
            self._print(r"\}", math=MATH)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self._print(node.id, math=MATH)
        elif isinstance(node.ctx, ast.Store):
            self._print(f"{node.id} \\gets", math=MATH)
        elif isinstance(node.ctx, ast.Store):
            # TODO
            self._print(f"DEL {node.id}", math=NOMATH)

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
                self._print(r"\neg", math=MATH)
            case ast.Invert():
                # self._print(r"\overline{")
                self._print(r"\mathord{\sim}", math=MATH)
                self.visit(node.operand)
                # self._print(r"}")
                return
        self.visit(node.operand)

    def visit_BinOp(self, node: ast.BinOp):
        # Handle div as a special case because it requires a different order
        if isinstance(node.op, ast.Div | ast.FloorDiv):
            if isinstance(node.op, ast.FloorDiv):
                self._print(r"\lfloor", math=MATH)
            self._print(r"\frac{", math=MATH)
            self.visit(node.left)
            self._print(r"}{")
            self.visit(node.right)
            self._print(r"}", math=MATH)
            if isinstance(node.op, ast.FloorDiv):
                self._print(r"\rfloor", math=MATH)
        elif isinstance(node.op, ast.Pow):
            # self._print("$", math=ENTER)
            self.visit(node.left)
            self._print(r"^{", math=MATH)
            self.visit(node.right)
            self._print(r"}", math=MATH)
        else:
            self.visit(node.left)
            match node.op:
                case ast.Add():
                    self._print("+")
                case ast.Sub():
                    self._print("-")
                case ast.Mult():
                    self._print(r"\cdot", math=MATH)
                case ast.Mod():
                    self._print(r"\mod", math=MATH)
                # https://tex.stackexchange.com/questions/14227/bitwise-operator-in-pseudo-code
                case ast.LShift():
                    self._print(r"\ll", math=MATH)
                case ast.RShift():
                    self._print(r"\gg", math=MATH)
                case ast.BitOr():
                    self._print(r"\mathbin{|}", math=MATH)
                case ast.BitAnd():
                    self._print(r"\mathbin{\&}", math=MATH)
                case ast.BitXor():
                    self._print(r"\mathbin{\oplus}", math=MATH)
                case ast.MatMult():
                    self._print(r"\times", math=MATH)
                case _:
                    raise TypeError("Unexpected Binary Operation")
            self.visit(node.right)

    def visit_BoolOp(self, node: ast.BoolOp):
        operator = r"\land " if isinstance(node.op, ast.And) else r"\mathbin{\lor}"
        self.visit(node.values[0])
        for v in node.values[1:]:
            self._print(operator, math=MATH)
            self.visit(v)

    def visit_Compare(self, node: ast.Compare):
        self.visit(node.left)
        for op, comp in zip(node.ops, node.comparators):
            match op:
                case ast.Eq():
                    self._print(r"=", math=MATH)
                case ast.NotEq():
                    self._print(r"\ne", math=MATH)
                case ast.Lt():
                    self._print(r"<", math=MATH)
                case ast.LtE():
                    self._print(r"\leq", math=MATH)
                case ast.Gt():
                    self._print(r">", math=MATH)
                case ast.GtE():
                    self._print(r"\geq", math=MATH)
                case ast.Is():
                    self._print(r"\equiv", math=MATH)
                case ast.IsNot():
                    self._print(r"\not\equiv", math=MATH)
                case ast.In():
                    self._print(r"\in", math=MATH)
                case ast.NotIn():
                    self._print(r"\not\in", math=MATH)
                case _:
                    raise TypeError("Unexpected Comparison Operation")
            self.visit(comp)

    def visit_Call(self, node: ast.Call):
        # TODO
        # self._print(f"CALL ")
        if isinstance(node.func, ast.Name):
            if node.func.id == "len":
                self._print(r"\lvert", math=MATH)
                for v in node.args:
                    self.visit(v)
                for v in node.keywords:
                    self.visit(v)
                self._print(r"\rvert", math=MATH)
                return
            elif node.func.id in ignores:
                self._print("\\" + node.func.id, end="", math=NOMATH)
            else:
                self._print("\\" + node.func.id.capitalize(), end="", math=NOMATH)
        elif isinstance(node.func, ast.Attribute):
            # self.visit(node.func)
            self._print("\\" + node.func.attr, end="", math=NOMATH)
        # self.visit(node.func)
        self._print("{", math=NOMATH)
        # self._print(r"(")
        for v in node.args:
            self.visit(v)
        for v in node.keywords:
            self.visit(v)
        # self._print(r")")
        self._print("}", math=NOMATH)

    def visit_keyword(self, node: ast.keyword):
        self._print(f"{node.arg}=", math=NOMATH)
        self.visit(node.value)

    # IfExp (ternary)

    def visit_Attribute(self, node: ast.Attribute):
        self.visit(node.value)
        self._print("." + node.attr, math=NOMATH)
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
        self._print(r"\If{", math=NOMATH)
        self.level += 1
        self.visit(node.test)
        self._print(r"}{", math=NOMATH)
        for n in node.body:
            self.visit(n)
        self._print(r"}", math=NOMATH)
        if len(node.orelse):
            self._suppress_semicolon = True
            self._print(r"{", math=NOMATH)
            for v in node.orelse:
                self.visit(v)
            self._print(r"}", math=NOMATH)
        self._suppress_semicolon = True
        self.level -= 1

    def visit_For(self, node: ast.For):
        self._suppress_semicolon = True
        self._print(r"\ForAll{", math=NOMATH)
        self.level += 1
        self.visit(node.target)
        self._print(r"\in", math=MATH)
        self.visit(node.iter)
        self._print(r"}{", math=NOMATH)
        for n in node.body:
            self.visit(n)
        self._print(r"}", math=NOMATH)
        if len(node.orelse):
            self._suppress_semicolon = True
            self._print(r"{", math=NOMATH)
            for v in node.orelse:
                self.visit(v)
            self._print(r"}", math=NOMATH)
        self._suppress_semicolon = True
        self.level -= 1

    def visit_While(self, node: ast.While):
        self._suppress_semicolon = True
        self._print(r"\While{", math=NOMATH)
        self.level += 1
        self.visit(node.test)
        self._print(r"}{", math=NOMATH)
        for n in node.body:
            self.visit(n)
        self._print(r"}", math=NOMATH)
        if len(node.orelse):
            self._suppress_semicolon = True
            self._print(r"{", math=NOMATH)
            for v in node.orelse:
                self.visit(v)
            self._print(r"}", math=NOMATH)
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
        self._print(r"\Fn{" + "\\" + node.name.capitalize() + "{", math=NOMATH)
        self.visit(node.args)
        self._print("}}{", math=NOMATH)
        self._suppress_semicolon = True
        self.level += 1
        # node.decorator_list
        for v in node.body:
            self.visit(v)
        self._print("}", math=NOMATH)
        self.level -= 1

    def visit_Lambda(self, node: ast.Lambda) -> Any:
        self._print(r"\lambda", math=MATH)
        self.visit(node.args)
        self._print(r":")
        self.visit(node.body)

    def visit_arguments(self, node: ast.arguments) -> Any:
        # vararg, kwargs, kw_defaults, default
        for p in node.posonlyargs:
            self.visit(p)
        for p in node.args:
            self.visit(p)
        for p in node.kwonlyargs:
            self.visit(p)
        # return super().visit_arguments(node)

    def visit_arg(self, node: ast.arg) -> Any:
        self._print(node.arg, math=MATH)

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
    def __init__(self) -> None:
        super().__init__()
        self.needs = set()

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
