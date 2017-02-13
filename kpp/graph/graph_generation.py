import igraph as ig
import numpy as np


def nbrs_of_nbr(graph):
  num_vertices = graph.vcount()
  G = graph.copy()
  for i in range(num_vertices):
    neigh = set(graph.neighbors(i))
    nbrs_of_nbrs_set = set()
    for j in neigh:
      for k in set(graph.neighbors(j)) - neigh:
        if k > i:
          nbrs_of_nbrs_set.add(k)
    for j in nbrs_of_nbrs_set:
      G.add_edge(i, j)
  return G


def torus_hypot(dx, dy):
  dx, dy = abs(dx), abs(dy)
  if dx > 0.5:
    dx = 1 - dx
  if dy > 0.5:
    dy = 1 - dy
  return np.hypot(dx, dy)


def disk_graph(points, r, torus=False):
  if torus:
    dist = torus_hypot
  else:
    dist = np.hypot
  G = ig.Graph()
  npts = len(points)
  for v in points:
    G.add_vertex(x=v[0], y=v[1])

  for i in range(npts):
    for j in range(i + 1, npts):
      x0, y0 = points[i][0], points[i][1]
      x1, y1 = points[j][0], points[j][1]
      if dist(x0 - x1, y0 - y1) < r:
        G.add_edge(i, j)
  return G


if __name__ == '__main__':
  npts = 100
  r = 0.08

  graph = ig.Graph.GRG(npts, r)
  print(graph)
  G = nbrs_of_nbr(graph)

  points = [(v['x'], v['y']) for v in graph.vs()]
  graph2 = disk_graph(points, r)
  print(graph2)
