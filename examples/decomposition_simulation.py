import igraph as ig
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict

from kpp.graph import decompose_graph, analyse_components, disk_graph_torus, nbrs_of_nbr

def graph_generator(npts, r):
  return nbrs_of_nbr(disk_graph_torus(npts, r))

def simulate_decomposition(npts, radius_range, k, sample_size=1000):
  results = OrderedDict()
  keys = analyse_components(ig.Graph.Full(2), [ig.Graph.Full(2)]).keys()
  
  for r in radius_range:
    print("Radius: ", r)
    results[r] = dict()
    for key in keys: results[r][key] = np.empty(sample_size)
    for i in range(sample_size):
      G = graph_generator(npts, r)
      comps = decompose_graph(G, k)
      res = analyse_components(G, comps)
      for (key,val) in res.items():
        results[r][key][i] = val
  return results

def plot_results(p, results, key):
  radii = sorted(results.keys())
  y = [np.mean(results[r][key]) for r in radii]
  p.plot(radii, y, '--o')
  p.set_xlabel("Disk Radius")
  p.set_ylabel(key)
  

if __name__=='__main__':
  import pickle

  radius_range= np.linspace(0.01, 0.075, 12)
  npts = 200
  # radius_range= np.linspace(0.02, 0.15, 12)
  # npts = 100
  # radius_range=np.linspace(0.04, 0.3, 12)
  # npts = 50
  k=3

  
  simulation_results = simulate_decomposition(npts, radius_range, k, 100)
  
  
  fig = plt.figure(figsize=(9,3))
  p1 = plt.subplot(131)
  plt.xticks(rotation=45)
  plot_results(p1, simulation_results, "Edge Reduction")
  p2 = plt.subplot(132)
  plt.xticks(rotation=45)
  plot_results(p2, simulation_results, "Maximum Edges")
  p3 = plt.subplot(133)
  plt.xticks(rotation=45)
  plot_results(p3, simulation_results, "Maximum Vertices")
  
  fig.suptitle("Graph Decomposition, Original Graph: %d vertices" % npts)
  fig.tight_layout()
  
  fig.savefig("graph_decomp_simulation.pdf")
  
  
