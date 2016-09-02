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
        if k > i: nbrs_of_nbrs_set.add(k)
    for j in nbrs_of_nbrs_set: G.add_edge(i, j)
  return G

def torus_hypot(dx,dy):
  dx, dy = abs(dx), abs(dy)
  if dx>0.5: dx=1-dx
  if dy>0.5: dy = 1-dy
  return np.hypot(dx,dy)

def disk_graph_torus(npts, r):
  G = ig.Graph()
  pts = np.random.random((npts, 2))
  for p in pts:
    G.add_vertex(x=p[0], y=p[1])
  for i in range(npts):
    for j in range(i):
      if torus_hypot(pts[i,0]-pts[j,0], pts[i,1]-pts[j,1]) < r:
        G.add_edge(j,i)
  return G

if __name__=='__main__':
  npts=100
  r=0.08
  graph = disk_graph_torus(npts,r)
  G = nbrs_of_nbr(graph)
