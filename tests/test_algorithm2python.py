#!/usr/bin/env python3
import pytest
import ast
import re

import algorithm2python.main as main
from algorithm2python.python2algorithm import Python2Algorithm


def test_main_succeeds():
    try:
        main.main()
    except Exception as e:
        assert False


def test_hello_world():
    source = """x=1"""
    tree = ast.parse(source, mode="exec")
    with open("test_output", "w") as f:
        Python2Algorithm(output=f).visit(tree)
    with open("test_output", "r") as f:
        tex = "\n".join(f.readlines())
        assert "x" in tex
        assert "\\gets" in tex
        assert "1" in tex


def test_fraction():
    source = """x=1/2
y=1+2/(5 + x)"""
    tree = ast.parse(source, mode="exec")
    with open("test_output", "w") as f:
        Python2Algorithm(output=f).visit(tree)
    with open("test_output", "r") as f:
        tex = "\n".join(f.readlines())
        assert "\\frac{ 1 }{ 2 }" in tex
        assert "\\frac{ 2 }{ 5 + x }" in tex


def test_lambda():
    source = """lambda x: x**2"""
    tree = ast.parse(source, mode="exec")
    with open("test_output", "w") as f:
        Python2Algorithm(output=f).visit(tree)
    with open("test_output", "r") as f:
        tex = "\n".join(f.readlines())
        assert "\\lambda x : x ^{ 2 }" in tex
