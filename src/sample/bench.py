#!/usr/bin/env python3
"""
This is a module docstring
"""
from math import floor, ceil

a = None
b = "foo"
c = (1 / 2, 2**5, 3 * 5)
d = 3.13412342314234
e = {4 << 2, 5 >> 5, 6 ^ 3}
f = frozenset({7, 8})
g = set()
h = not a + ~b + (-d) + (+d)


def foo(x, y):
    if x in y:
        yield from bar(x)
        return True
    else:
        h = []
        while x < y:
            if len(h) == 0:
                print("hello")
            else:
                break
            for q in y:
                x += 1
            h.append(x)
        return False


def bar(y):
    x1 = len(y)
    x2 = all(y)
    x3 = any(y)
    x4 = abs(y)
    x5 = min(y, max(y, 5))
    x7 = ceil(floor(y))
    yield 1
