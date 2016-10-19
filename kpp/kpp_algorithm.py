from abc import ABCMeta, abstractmethod
import sys
from time import time
import numpy as np
import igraph as ig
from .kpp import KPPExtension
from .separation import *
from .graph import decompose_graph

class KPPAlgorithm:
  def __init__(self, G, k, **kwargs):
    self.output = dict()
    self.G = G
    self.k = k
    self.params = dict()
    self.params['preprocess'] = kwargs.pop('preprocess', False)
    self.params['y-cut'] = kwargs.pop('y-cut', [])
    self.params['phase 1 removal'] = kwargs.pop('phase 1 removal', 0)
    self.params['yz-cut'] = kwargs.pop('yz-cut', [])
    self.params['phase 2 removal'] = kwargs.pop('phase 2 removal', 0)
    self.params['z-cut'] = kwargs.pop('z-cut', [])
    self.params['symmetry breaking']  = kwargs.pop('symmetry breaking', False)
    self.verbosity = kwargs.pop('verbosity', 1)

    # Gurobi parameters
    self.gurobi_params = kwargs

  def run(self):
    if self.verbosity > 1:
      print('Solving KPP Modulo-6 Extension Problem')
      print('Input graph has %d nodes and %d edges' % (self.G.vcount(), self.G.ecount()))
    if self.params['preprocess']:
      start=time()
      graphs=decompose_graph(self.G, self.k)
      end=time()
      self.output['preprocess time'] = end-start
      self.output['preprocess components'] = len(graphs)
      self.output['largest components'] = max(g.vcount() for g in graphs)
      self.output['solution'] = dict()

      if self.verbosity:
        print('Graph preprocessing yields %d components' % len(graphs))
      
      for i,g in enumerate(graphs):
        if self.verbosity > 0:
          print(25*'-')
          print('Solving for component %d' % i)
          print(25*'-')
        res = self.solve_single_problem(g)
        if not self.output['solution']:
          for k,val in res.items():
            self.output['solution'][k] = [val]
        else:
          for k,val in res.items():
            self.output['solution'][k].append(val)

    else:
      res = self.solve_single_problem(self.G)
      self.output['solution'] = res

    return self.output
                    
  def solve_single_problem(self, g):
    if self.verbosity > 0: 
      print("Running exact solution algorithm")
    results=dict()
    kpp=KPPExtension(g, self.k)
    for (key,val) in self.gurobi_params.items(): kpp.model.setParam(key, val)
    if self.params['y-cut'] or self.params['yz-cut'] or self.params['z-cut']:
      max_cliques=g.maximal_cliques()
      results["clique number"] = max(len(nodes) for nodes in max_cliques)
            
    if self.params['y-cut']:
      for p in self.params['y-cut']:
        kpp.add_separator(YCliqueSeparator(max_cliques, p, self.k))
      start=time()
      results['phase 1 constraints added'] = kpp.cut()
      end=time()
      results['phase 1 time'] = end-start
      results['phase 1 lb'] = kpp.model.objVal
      if self.params['phase 1 removal']:
        results["phase 1 constraints removed"] = kpp.remove_redundant_constraints(hard=(self.params['phase 1 removal'] > 1))
      kpp.sep_algs.clear()

    kpp.add_z_variables()
    if self.params['yz-cut'] or self.params['z-cut']:
      for p in self.params['yz-cut']:
          kpp.add_separator(YZCliqueSeparator(max_cliques, p, self.k))
      for p in self.params['z-cut']:
          kpp.add_separator(ZCliqueSeparator(max_cliques, p, self.k))
      start=time()
      results['phase 2 constraints added'] = kpp.cut()
      end=time()
      results['phase 2 time'] = end-start
      results['phase 2 lb'] = kpp.model.objVal
      if self.params['phase 2 removal']:
        results["phase 2 constraints removed"] = kpp.remove_redundant_constraints(hard=(self.params['phase 2 removal']))
      kpp.sep_algs.clear()

    kpp.add_node_variables()
    if self.params['symmetry breaking']:
      kpp.break_symmetry()

    kpp.solve()
    if self.verbosity > 0: print('')

    results["optimality gap"] = kpp.model.MIPGap
    results["status"] = kpp.model.Status
    if results["status"] == 2:
      results["optimal value"] = kpp.model.objVal
      results["branch and bound time"] = kpp.model.Runtime
    else: 
      results["optimal value"] = np.NaN
      results["branch and bound time"] = np.NaN

    results["branch and bound nodes"] = kpp.model.NodeCount
    return results
