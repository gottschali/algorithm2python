#!/usr/bin/env python3

a = None
b = "foo"
c = (1, 2, 3)
d = 3.13412342314234
e = {4, 5, 6}
f = frozenset({7, 8})
g = set()
h = not a + ~b + (-d) + (+d)


def foo(x, y):
    if x in y:
        bar(x)
        return True
    else:
        h = []
        while x < y:
            for q in y:
                x += 1
            h.append(x)
        return False


def bar(y):
    pass
