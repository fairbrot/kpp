import igraph as ig
import numpy as np

def decompose_graph(G, k):
  to_process = [G]
  components = []
  while len(to_process) > 0:
    graph = to_process.pop()
    bicomps = graph.biconnected_components()
    if len(bicomps) >1:
      for bicomp in bicomps: 
        to_process.append(graph.subgraph(bicomp))
      continue
    if min(graph.degree(range(graph.vcount()))) < k:
      core = graph.k_core(k)
      if core.vcount() > k:
        to_process.append(core)
      continue
    components.append(graph)
  return components

def avg_degree(graph):
  return np.mean(graph.degree(range(graph.vcount())))

def analyse_components(graph, comps):
  results=dict()
  # Reduction in edges
  orig_edges=graph.ecount()
  decomp_edges=sum(g.ecount() for g in comps)
  results['Edge Reduction'] = (orig_edges-decomp_edges)/orig_edges
  # Reduction in average degree
  # orig_avg_degree = avg_degree(graph)
  # union_graph = ig.Graph().disjoint_union(comps)
  # decomp_avg_degree = avg_degree(union_graph)
  # results["Average Degree Increase"] = (decomp_avg_degree-orig_avg_degree)/orig_avg_degree
  # Max vertices, edges and both
  if len(comps) > 0:
    results["Maximum Vertices"] = max(g.vcount() for g in comps)
    results["Maximum Edges"] = max(g.ecount() for g in comps)
    results["Maximum Size"] = max(g.vcount() + g.ecount() for g in comps)
  else:
    results["Maximum Vertices"] = 0
    results["Maximum Edges"] = 0
    results["Maximum Size"] = 0

  return results

if __name__=='__main__':
  npts = 100
  r = 0.10
  graph = ig.Graph.GRG(npts, r)

  #ig.plot(graph)
  k=3
  comps = decompose_graph(graph,k)
  
  print("Original Graph:")
  print("Vertices: ", graph.vcount())
  print("Edges: ", graph.ecount(), "\n")

  print("Decomposition Summary: ")
  for (k,val) in analyse_components(graph, comps).items():
    print(k,": ", val)
