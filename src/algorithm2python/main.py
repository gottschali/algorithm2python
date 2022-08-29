#!/usr/bin/env python3

import sys
from algorithm2python.python2algorithm import Python2Algorithm

import ast


def main():
    with open("src/sample/bench.py") as f:
        source = "".join(f.readlines())
        tree = ast.parse(source, mode="exec")
        print(ast.dump(tree, indent=4), file=sys.stderr)
        Python2Algorithm().visit(tree)


if __name__ == "__main__":
    main()
