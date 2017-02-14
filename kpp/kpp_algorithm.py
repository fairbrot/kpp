from abc import ABCMeta, abstractmethod
import sys
from time import time
import numpy as np
import igraph as ig
from .kpp import KPPExtension
from .separation import *
from .graph import decompose_graph


class KPPAlgorithm:

  def __init__(self, G, k, k2, **kwargs):
    self.output = dict()
    self.G = G
    self.k = k
    self.k2 = k2
    self.params = dict()
    self.params['preprocess'] = kwargs.pop('preprocess', False)
    self.params['y-cut'] = kwargs.pop('y-cut', [])
    self.params['y-cut removal'] = kwargs.pop('y-cut removal', 0)
    self.params['yz-cut'] = kwargs.pop('yz-cut', [])
    self.params['yz-cut removal'] = kwargs.pop('yz-cut removal', 0)
    self.params['removal slack'] = kwargs.pop('removal slack', 1e-3)
    self.params['z-cut'] = kwargs.pop('z-cut', [])
    self.params['z-cut removal'] = kwargs.pop('z-cut removal', 0)
    self.params['symmetry breaking'] = kwargs.pop('symmetry breaking', False)
    self.params['fractional y-cut'] = kwargs.pop('fractional y-cut', False)

    self.verbosity = kwargs.pop('verbosity', 1)

    # Gurobi parameters
    self.gurobi_params = kwargs

  def run(self):
    if self.verbosity > 1:
      print('Solving 2-Level KPP')
      print('Input graph has %d nodes and %d edges' %
            (self.G.vcount(), self.G.ecount()))
    if self.params['preprocess']:
      start = time()
      graphs = decompose_graph(self.G, self.k)
      end = time()
      self.output['preprocess time'] = end - start
      self.output['preprocess components'] = len(graphs)
      if len(graphs) > 0:
        self.output['largest components'] = max(g.vcount() for g in graphs)
      else:
        self.output['largest components'] = 0

      self.output['solution'] = dict()

      if self.verbosity:
        print('Graph preprocessing yields %d components' % len(graphs))

      for i, g in enumerate(graphs):
        if self.verbosity > 0:
          print(25 * '-')
          print('Solving for component %d' % i)
          print(25 * '-')
        res = self.solve_single_problem(g)
        if not self.output['solution']:
          for k, val in res.items():
            self.output['solution'][k] = [val]
        else:
          for k, val in res.items():
            self.output['solution'][k].append(val)

    else:
      res = self.solve_single_problem(self.G)
      self.output['solution'] = res

    return self.output

  def solve_single_problem(self, g):
    if self.verbosity > 0:
      print("Running exact solution algorithm")
    results = dict()
    kpp = KPPExtension(g, self.k, self.k2, verbosity=self.verbosity)
    for (key, val) in self.gurobi_params.items():
      kpp.model.setParam(key, val)
    if self.params['y-cut'] or self.params['yz-cut'] or self.params['z-cut']:
      max_cliques = g.maximal_cliques()
      results["clique number"] = max(len(nodes) for nodes in max_cliques)

    if self.params['y-cut']:
      for p in self.params['y-cut']:
        kpp.add_separator(YCliqueSeparator(max_cliques, p, self.k))
      start = time()
      results['y-cut constraints added'] = kpp.cut()
      end = time()
      results['y-cut time'] = end - start
      results['y-cut lb'] = kpp.model.objVal

      if self.params['y-cut removal']:
        results["y-cut constraints removed"] = kpp.remove_redundant_constraints(hard=(
            self.params['y-cut removal'] > 1), allowed_slack=self.params['removal slack'])
      kpp.sep_algs.clear()

    kpp.add_z_variables()
    if self.params['yz-cut']:
      for p in self.params['yz-cut']:
        kpp.add_separator(YZCliqueSeparator(max_cliques, p, self.k, self.k2))
      start = time()
      results['yz-cut constraints added'] = kpp.cut()
      end = time()
      results['yz-cut time'] = end - start
      results['yz-cut lb'] = kpp.model.objVal

      if self.params['fractional y-cut']:
        res = kpp.add_fractional_cut()
        if self.verbosity > 0:
          if res:
            print(" Added fractional y-cut")
          else:
            print(" Fractional y-cut not appropriate")

      if self.params['yz-cut removal']:
        results["yz-cut constraints removed"] = kpp.remove_redundant_constraints(
            hard=(self.params['yz-cut removal']), allowed_slack=self.params['removal slack'])
      kpp.sep_algs.clear()

    if self.params['z-cut']:
      for p in self.params['z-cut']:
        kpp.add_separator(ZCliqueSeparator(max_cliques, p, self.k, self.k2))
      start = time()
      results['z-cut constraints added'] = kpp.cut()
      end = time()
      results['z-cut time'] = end - start
      results['z-cut lb'] = kpp.model.objVal

      if self.params['z-cut removal']:
        results["z-cut constraints removed"] = kpp.remove_redundant_constraints(
            hard=(self.params['z-cut removal']), allowed_slack=self.params['removal slack'])
      kpp.sep_algs.clear()

    kpp.add_node_variables()
    if self.params['symmetry breaking']:
      kpp.break_symmetry()

    kpp.solve()
    if self.verbosity > 0:
      print('')

    results["optimality gap"] = kpp.model.MIPGap
    results["status"] = kpp.model.Status
    if results["status"] == 2:
      results["optimal value"] = kpp.model.objVal
      results["branch and bound time"] = kpp.model.Runtime
    else:
      results["optimal value"] = np.NaN
      results["branch and bound time"] = np.NaN

    results["branch and bound nodes"] = int(kpp.model.NodeCount)
    return results
