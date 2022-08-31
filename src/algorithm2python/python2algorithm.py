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

# TODO methods (Calls with attributes)
# Infinity / negative infinity (floats)
# numpy matmul
# TODO These should be doable with simple text replacements
# - math constant, e, pi, ...
# - Also do this for other greek stuff
# - trigonometry
# -> replace alpha with \alpha, ...

# set operations
# Can't differentiate with normal booleans so far

MATH = 1
NOMATH = -1


class Python2Algorithm(ast.NodeVisitor):
    """
    This class overloads almost all visitor methods of the python AST.
    When visiting it will print corresponding LaTeX code compatible with algorithm2e to STDOUT or the file output if given.
    """

    _INDENTATION = "   "
    # The level of indentation
    # Is manually incremented for example when entering the body of a while expression
    # After leaving it you have to decrement again
    level = 0
    # Keep track of the line number in the source code to be able to print newlines in the produced latex
    # This is strictly not necessary but makes the code much more readable
    _lineno = -1
    # algorithm2e wants a \; to terminate each line.
    # If we naïvely do this for every line we get undesirable output
    # for example a hanging line after the condition of a while loop
    # To prevent this we manually set this flag when we don't want this semicolon printed.
    # It is cleared automatically
    _suppress_semicolon = False

    # Flag if we are currently writing an equation
    in_equation = False
    # Previously we wrapped each symbol preemptively with delimiters
    # But in this way we can make the produced more  natural like a human would write it
    # and also reduce the number of characters needed.
    # $x$ + $y$ -> $x + y$

    def __init__(self, output=sys.stdout) -> None:
        super().__init__()
        self._output_file = output

    def define_Functions_First(self, node: ast.AST):
        """
        To allow recursive function definition we need to traverse the entire AST an extract all function definitions
        before we can traverse it normally and call them.
        Otherwise we might use \Foo
        before we have defined it with \\SetKfFunction{Foo}{Foo}
        """
        # to allow recursive function definitions we run it before
        # print("\\SetKwFunction{" + f + "}{" + f + "}")
        kwe = KwFunctionExtractor()
        kwe.visit(node)

        # Define additional keywords
        self._print("\\SetKw{Yield}{yield}\n")
        self._print("\\SetKw{YieldFrom}{yield from}\n")
        self._print("\\SetKw{Break}{break}\n")
        self._print("\\SetKw{Continue}{continue}\n")
        self._print("\\SetKw{Pass}{pass}\n")

        # TODO SetKwData: what?

        if kwe.needs:
            self._print("\\SetKwProg{Fn}{Function}{:}{end}\n")
        for f in kwe.needs:
            self._print("\\SetKwFunction{" + f + "}{" + f + "}\n")

    def visit_Module(self, node: ast.Module):
        self.define_Functions_First(node)

        docstring = ast.get_docstring(node)
        if docstring:
            # Or KwData
            # \TitleOfAlgo
            # \caption
            self._print(r"\KwResult{" + docstring + "}\n")
            for v in node.body[1:]:
                self.visit(v)
        else:
            for v in node.body:
                self.visit(v)
        # Finally
        if self.in_equation > 0:
            # Finish the last open math env
            self._print("$")

    def visit(self, node: ast.AST):
        """This is called for every ast node so we can hijack it to perform line number checks"""
        if hasattr(node, "lineno") and node.lineno > self._lineno:
            if self._lineno != -1 and not self._suppress_semicolon:
                if self.in_equation:  # We may need to close an equation.
                    self._print("$")
                    self.in_equation = False
                self._print(r" \; ", end="\n")
                self._print(self._INDENTATION * self.level, end="")
            else:
                self._print("\n" + self._INDENTATION * self.level, end="")
            self._lineno = node.lineno
            self._suppress_semicolon = False
        return super().visit(node)

    def _print(self, value: str, math=None, end=" ", *kwarg, **kwargs):
        """
        Internal print wrapper to print latex output.
        Pass math=MATH if you require to be in an math environment.
        For example $\frac{1}{2}$ would not work without the inline euqation delimiters ($)
        If math=NOMATH then it is written NOT in a math env.
        Otherwise there is no guarantee.
        """
        if math == MATH:
            # We need to start a new equation
            if not self.in_equation:
                value = "$" + value
            # Otherwise we are already in an equation
            self.in_equation = True
        if math == NOMATH:
            # We need to terminate an equation
            if self.in_equation:
                value = "$" + value
            self.in_equation = False
        print(value, end=end, file=self._output_file, *kwarg, **kwargs)

    def visit_Constant(self, node):
        # https://stackoverflow.com/questions/67524641/convert-multiple-isinstance-checks-to-structural-pattern-matching
        # number
        # string
        # None
        # tuples
        # frozensets
        match node.value:
            case True:
                self._print(r"\top", math=MATH)
            case False:
                self._print(r"\bot", math=MATH)
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
                self._print("(+")
                self.visit(node.operand)
                self._print(")")
            case ast.USub():
                self._print("(-")
                self.visit(node.operand)
                self._print(")")
            case ast.Not():
                self._print(r"\neg", math=MATH)
                self.visit(node.operand)
            case ast.Invert():
                self._print(r"\mathord{\sim}", math=MATH)
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
            if node.func.id == "set":
                if len(node.args) == 0:
                    self._print(r"\emptyset")
                else:
                    self.visit(ast.Set(node.args[0].elts))
                return
            elif node.func.id == "len":
                self._print(r"\lvert", math=MATH)
                for v in node.args:
                    self.visit(v)
                for v in node.keywords:
                    self.visit(v)
                self._print(r"\rvert", math=MATH)
                return
            elif node.func.id == "all":
                self._print(r"\forall", math=MATH)
                for v in node.args:
                    self.visit(v)
                for v in node.keywords:
                    self.visit(v)
                return
            elif node.func.id == "any":
                self._print(r"\exists", math=MATH)
                for v in node.args:
                    self.visit(v)
                for v in node.keywords:
                    self.visit(v)
                return
            elif node.func.id == "abs":
                self._print(r"\|", math=MATH)
                for v in node.args:
                    self.visit(v)
                for v in node.keywords:
                    self.visit(v)
                self._print(r"\|", math=MATH)
                return
            elif node.func.id == "min":
                self._print(r"\min", math=MATH)
                for v in node.args:
                    self.visit(v)
                for v in node.keywords:
                    self.visit(v)
                return
            elif node.func.id == "max":
                self._print(r"\max", math=MATH)
                for v in node.args:
                    self.visit(v)
                for v in node.keywords:
                    self.visit(v)
                return
            elif node.func.id == "ceil":
                self._print(r"\lceil", math=MATH)
                for v in node.args:
                    self.visit(v)
                for v in node.keywords:
                    self.visit(v)
                self._print(r"\rceil", math=MATH)
                return
            elif node.func.id == "floor":
                self._print(r"\lfloor", math=MATH)
                for v in node.args:
                    self.visit(v)
                for v in node.keywords:
                    self.visit(v)
                self._print(r"\rfloor", math=MATH)
                return
            else:
                name = normalize_function_name(node.func.id)
                self._print("\\" + name, end="", math=NOMATH)
        elif isinstance(node.func, ast.Attribute):
            # self.visit(node.func)
            # name = normalize_function_name(node.func.attr)
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
    def visit_Subscript(self, node: ast.Subscript) -> Any:
        self.visit(node.value)
        self._print(r"[", math=MATH)
        self.visit(node.slice)
        self._print(r"]", math=MATH)

    # TODO Comprehensions
    # This could be really nice in latex
    #
    def visit_Assign(self, node: ast.Assign) -> Any:
        self.visit(node.targets[0])
        # self._print(r"\gets")
        for t in node.targets[1:]:
            # self._print(r"\gets", math=MATH)
            self.visit(t)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        self.visit(node.target)
        self.visit(node.target)
        self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> Any:
        normal_node = ast.BinOp(node.target, node.op, node.value)
        self.visit(normal_node)

    # Raise
    # Assert
    # Delete
    def visit_Delete(self, node: ast.Delete) -> Any:
        self._print(r"\mathrm{del}")
        for t in node.targets:
            self.visit(t)

    def visit_Pass(self, node: ast.Pass) -> Any:
        self._print(r"\Pass", math=NOMATH)

    #
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
        # we don't want the \gets arrow that will be produced by a store otehrwise
        if isinstance(node.target, ast.Name):
            self._print(node.target.id)
        else:
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

    def visit_Break(self, node: ast.Break) -> Any:
        self._print(r"\Break")

    def visit_Continue(self, node: ast.Continue) -> Any:
        self._print(r"\Continue")

    # TODO
    # Try
    # ExceptHandler
    # With
    # withitem

    def visit_Match(self, node: ast.Match) -> Any:
        self._print(r"\Switch{", math=NOMATH)
        self.visit(node.subject)
        self._print(r"}{", math=NOMATH)
        self.level += 1
        for c in node.cases:
            self.visit(c)
        self._print(r"{", math=NOMATH)
        self.level -= 1

    def visit_match_case(self, node: ast.match_case) -> Any:
        self._print(r"\Case{", math=NOMATH)
        self.visit(node.pattern)
        self.visit(node.guard)  # todo
        self._print(r"}{", math=NOMATH)
        self.level += 1
        for b in node.body:
            self.visit(b)
        self._print(r"{", math=NOMATH)
        self.level -= 1

    def visit_MatchValue(self, node: ast.MatchValue) -> Any:
        self.visit(node.value)

    def visit_MatchSingleton(self, node: ast.MatchSingleton) -> Any:
        self._print(node.value)

    # TODO
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
        name = normalize_function_name(node.name)
        self._print(r"\Fn{" + "\\" + name + "{", math=NOMATH)
        self._suppress_semicolon = True
        self.visit(node.args)
        self._print("}}{", math=NOMATH)
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
            self._print(",")
        for p in node.args:
            self.visit(p)
            self._print(",")
        for p in node.kwonlyargs:
            self.visit(p)
            self._print(",")

    def visit_arg(self, node: ast.arg) -> Any:
        self._print(node.arg, math=MATH)

    def visit_Return(self, node: ast.Return) -> Any:
        self._print(r"\Return{", math=NOMATH)
        self.visit(node.value)
        self._print(r"}", math=NOMATH)

    def visit_Yield(self, node: ast.Yield) -> Any:
        self._print(r"\Yield{", math=NOMATH)
        self.visit(node.value)
        self._print(r"}", math=NOMATH)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> Any:
        self._print(r"\YieldFrom{", math=NOMATH)
        self.visit(node.value)
        self._print(r"}", math=NOMATH)

    # I think we shouldnt support global and nonlocal
    # as they are generally bad practice and should
    # have no place in pseudocode
    def visit_Global(self, node: ast.Global) -> Any:
        # self._print(r"\Global{", math=NOMATH)
        for n in node.names:
            self.visit(n)
        # self._print(r"}", math=NOMATH)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> Any:
        # self._print(r"\NonLocal{", math=NOMATH)
        for n in node.names:
            self.visit(n)
        # self._print(r"}", math=NOMATH)

    # I would argue that classes have also no place here
    # They require a precise semantic
    # But different programming languages vary alot
    # So it is not clear what it would be in pseudocode
    # TODO ClassDef
    # As an alternative maybe allow classes as a kind of wrapper
    # So put the attributes as global vars
    # and the methods as normal functions
    # Then we need to be careful with "self"

    # TODO async
    # AsyncFunctionDef
    # Await
    # AsyncFor
    # AsyncWith


def normalize_function_name(func: str):
    return func.replace("_", "").capitalize()


class KwFunctionExtractor(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.needs = set()

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            self.needs.add(node.func.id.capitalize())
        elif isinstance(node.func, ast.Attribute):
            self.needs.add(node.func.attr)
        for v in node.args:
            self.visit(v)
        for v in node.keywords:
            self.visit(v)

    def visit_FunctionDef(self, node):
        name = normalize_function_name(node.name)
        self.needs.add(name)
        self.visit(node.args)
        # node.decorator_list
        for v in node.body:
            self.visit(v)

    def visit_AsyncFunctionDef(self, node):
        name = normalize_function_name(node.name)
        self.needs.add(name)
        self.visit(node.args)
        # node.decorator_list
        for v in node.body:
            self.visit(v)
