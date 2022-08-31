def euler_tour(graph):
    # We may start at any node in the graph (why? because cycle)
    start = next(iter(graph))
    print(start)
    # Erster Zyklus (fencepost)
    visited = set()
    achilles = random_tour(graph, start)
    print(achilles)
    start = achilles[-1]
    end = achilles[0]
    tour = []
    turtle = achilles.pop()
    # If we reach the end of the first Zyklus we are really done (exited all recursions so to say)
    while turtle != end:
        # Walk backwards until we find a node with unvisited edges
        while turtle != end and not len(graph[turtle]):
            print(turtle)
            tour.append(turtle)
            turtle = achilles.pop()
        zyklus = random_tour(graph, turtle)
        print(zyklus)
        achilles.extend(reversed(zyklus))  # Ingore the last one
    tour.append(end)
    tour.append(start)
    return tour


# Careful, the graph will be consumed!
def random_tour(g, start):
    graph = dict(g)
    node = start
    walk = []
    # While we are not on an isolated node
    while len(graph[node]):
        neighbor = graph[node].pop()  # Take any neighbor and remove the edge
        graph[neighbor].remove(node)
        walk.append(neighbor)
        node = neighbor
    return walk
