a = None
b = "foo"
c = (1, 2, 3)
d = 3.13412342314234
def colorful_paths(V, N, gamma):
    for v in V:
        P[i][(u, v)] = set()
        for x in N(v):
            for S in P[i-1][x]:
                if gamma(v) not in S:
                    P[i][(u, v)] = P[i][(u, v)] | {S | { gamma(v) }}
