import scipy.sparse
import scipy.sparse.csgraph
import glob
import time
import numpy as np

OUT_DIR = "tests"

def graph(t: str) -> scipy.sparse.csgraph:
    """Converts a string representation of a graph to a scipy graph"""
    v = []
    lines = t.split("\n")
    for line in lines:
        if line.startswith("node="):
            v.append(line[5:])

    e = []

    for line in lines:
        if line.startswith("link="):
            a, b, delay, bandwidth = line[5:].split(",")
            e.append((a, b, {"delay": delay, "bandwidth": bandwidth}))

    g = np.zeros((len(v), len(v)))
    g2 = np.zeros((len(v), len(v)))

    for a, b, data in e:
        g[v.index(a), v.index(b)] = data["delay"]
        g2[v.index(a), v.index(b)] = data["bandwidth"]

    return scipy.sparse.csr_matrix(g), g2


def str_path(path):
    """Converts a path to a string"""
    return "|".join(map(str, path))

def path(a, b, predecessors):
    """Returns the path from a to b given the predecessors matrix"""
    if predecessors[a, b] == -9999:
        return []

    path = [b]
    while a != b:
        b = predecessors[a, b]
        path = [b] + path

    return path

def bandwidth(path, bandwidth_graph):
    """Returns the bandwidth from a to b"""
    if len(path) == 0:
        return 0

    bandwidth = float("inf")

    for i in range(len(path) - 1):
        bandwidth = min(bandwidth, bandwidth_graph[path[i], path[i + 1]])

    return int(bandwidth)


def write(name, dist_matrix, bandwidth_graph, predecessors):
    with open(f"{OUT_DIR}/{name}.solution", "w") as f:
        for i in range(dist_matrix.shape[0]):
            for j in range(dist_matrix.shape[1]):
                d = dist_matrix[i, j]
                p = path(i, j, predecessors)
                f.write(f"link={i},{j},{int(d) if not d == float('inf') else 'inf'},{bandwidth(p, bandwidth_graph)},{str_path(p)}\n")


if __name__ == "__main__":
    # get all the test graphs
    graphs = []
    graphs2 = {}

    for filename in glob.glob("tests/*.graph"):
        t = time.time()
        with open(filename, "r") as f:
            g, g2 = graph(f.read())
            graphs.append({filename: g})
            graphs2[filename] = g2

        print(f"parsed {filename} in {time.time() - t}s")

    # make floyd warshall tests
    for g in graphs:
        for filename, graph in g.items():
            t = time.time()
            dist_matrix, predecessors = scipy.sparse.csgraph.floyd_warshall(
                graph,
                return_predecessors=True,
                directed=True,
            )
            print(f"ran floyd warshall on {filename} in {time.time() - t}s")

            name = filename.replace("tests/", "").replace(".graph", "")

            write(name, dist_matrix, graphs2[filename], predecessors)

            print(f"wrote {name}.solution in {time.time() - t}s ")