from abc import ABCMeta, abstractmethod
from time import time
import numpy as np
from copy import deepcopy, copy
from .kpp import KPP, KPPExtension
from .separation import YCliqueSeparator, YZCliqueSeparator, ZCliqueSeparator, ProjectedCliqueSeparator
from .graph import decompose_graph


class KPPAlgorithmResults:

  def __init__(self, output):
    self.output = output

  def __getitem__(self, key):
    return self.output[key]

  def algorithm_params(self):
    return self.output['params']

  def preprocess_stats(self):
    if not self.output['params']['preprocess']:
      return None
    keys = ['preprocess time', 'preprocess components', 'largest components']
    return {k: self.output[k] for k in keys}

  def branch_and_bound_stats(self):
    keys = ['optimal value', 'branch and bound time', 'ub', 'lb']
    res = dict()
    if self.output['params']['preprocess']:
      if self.output['preprocess components'] == 0:
        for k in keys:
          res[k] = 0.0
        res['optimality'] = True
      else:
        for k in keys:
          res[k] = sum(self.output['solution'][k])
        if np.all(np.array(self.output['solution']['status']) == 2):
          res['optimality'] = True
        else:
          res['optimality'] = False
    else:
      for k in keys:
        res[k] = self.output['solution'][k]
      res['optimality'] = (self.output['solution']['status'] == 2)
    return res


class KPPAlgorithmBase(metaclass=ABCMeta):

  def __init__(self, G, k, **kwargs):
    kwargs = deepcopy(kwargs)
    self.output = dict()

    self.G = G
    self.k = k
    self.params = dict()
    self.params['preprocess'] = kwargs.pop('preprocess', False)
    self.params['y-cut'] = kwargs.pop('y-cut', [])
    self.params['y-cut removal'] = kwargs.pop('y-cut removal', 0)
    self.params['removal slack'] = kwargs.pop('removal slack', 1e-3)
    self.params['symmetry breaking'] = kwargs.pop('symmetry breaking', False)
    self.params['fractional y-cut'] = kwargs.pop('fractional y-cut', False)

    self.verbosity = kwargs.pop('verbosity', 1)

  @abstractmethod
  def solve_single_problem(self, g):
    pass

  def y_cut_phase(self, kpp, max_cliques, results):
    for p in self.params['y-cut']:
      kpp.add_separator(YCliqueSeparator(max_cliques, p, self.k))
    start = time()
    results['y-cut constraints added'] = kpp.cut()
    end = time()
    results['y-cut time'] = end - start
    results['y-cut lb'] = kpp.model.objVal
    if self.params['fractional y-cut']:
      res = kpp.add_fractional_cut()
      if self.verbosity > 0:
        if res:
          print(" Added fractional y-cut")
        else:
          print(" Fractional y-cut not appropriate")
    if self.params['y-cut removal']:
      results["y-cut constraints removed"] = kpp.remove_redundant_constraints(hard=(
          self.params['y-cut removal'] > 1), allowed_slack=self.params['removal slack'])
    kpp.sep_algs.clear()

  def run(self):
    self.output['params'] = copy(self.params)
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

    return KPPAlgorithmResults(self.output)


class KPPBasicAlgorithm(KPPAlgorithmBase):

  def __init__(self, G, k, x_coefs=None, **kwargs):
    KPPAlgorithmBase.__init__(self, G, k, **kwargs)
    self.x_coefs = x_coefs
    if x_coefs and self.params['preprocess']:
      raise ArgumentError(
          'Cannot set x coefficients when preprocessing is enabled')
    self.params['x-cut'] = kwargs.pop('x-cut', [])
    self.params['x-cut colours'] = kwargs.pop('x-cut colours', [])
    self.params['x-cut removal'] = kwargs.pop('x-cut removal', 0)
    # Gurobi parameters
    self.gurobi_params = kwargs

  def x_cut_phase(self, kpp, max_cliques, results):
    for p in self.params['x-cut']:
      for colours in self.params['x-cut colours']:
        kpp.add_separator(ProjectedCliqueSeparator(max_cliques, p,
                                                   kpp.num_colours(), colours))
    start = time()
    results['x-cut constraints added'] = kpp.cut()
    end = time()
    results['x-cut time'] = end - start
    results['x-cut lb'] = kpp.model.objVal
    if self.params['x-cut removal']:
      results["x-cut constraints removed"] = kpp.remove_redundant_constraints(hard=(
          self.params['x-cut removal'] > 1), allowed_slack=self.params['removal slack'])
    kpp.sep_algs.clear()

  def solve_single_problem(self, g):
    if self.verbosity > 0:
      print("Running exact solution algorithm")
    results = dict()
    results['nodes'] = g.vcount()
    results['edges'] = g.ecount()
    kpp = KPP(g, self.k, x_coefs=self.x_coefs, verbosity=self.verbosity)
    for (key, val) in self.gurobi_params.items():
      kpp.model.setParam(key, val)

    if self.params['y-cut']:
      max_cliques = g.maximal_cliques()
      results["clique number"] = max(len(nodes) for nodes in max_cliques)
      self.y_cut_phase(kpp, max_cliques, results)

    kpp.add_node_variables()
    if self.params['x-cut']:
      self.x_cut_phase(kpp, max_cliques, results)

    if self.params['symmetry breaking']:
      kpp.break_symmetry()

    kpp.solve()
    if self.verbosity > 0:
      print('')

    results["optimality gap"] = kpp.model.MIPGap
    results["status"] = kpp.model.Status
    results["branch and bound time"] = kpp.model.Runtime
    if results["status"] == 2:
      results["optimal value"] = kpp.model.objVal
    else:
      results["optimal value"] = np.NaN

    if kpp.model.SolCount > 0:
      results["ub"] = kpp.model.objVal
    else:
      results["ub"] = np.Inf
    results["lb"] = kpp.model.objBound
    results["branch and bound nodes"] = int(kpp.model.NodeCount)
    return results


class KPPAlgorithm(KPPAlgorithmBase):

  def __init__(self, G, k, k2, **kwargs):
    KPPAlgorithmBase.__init__(self, G, k, **kwargs)
    self.k2 = k2
    self.params['yz-cut'] = kwargs.pop('yz-cut', [])
    self.params['yz-cut removal'] = kwargs.pop('yz-cut removal', 0)
    self.params['z-cut'] = kwargs.pop('z-cut', [])
    self.params['z-cut removal'] = kwargs.pop('z-cut removal', 0)
    # Gurobi parameters
    self.gurobi_params = kwargs

  def solve_single_problem(self, g):
    if self.verbosity > 0:
      print("Running exact solution algorithm")
    results = dict()
    results['nodes'] = g.vcount()
    results['edges'] = g.ecount()
    kpp = KPPExtension(g, self.k, self.k2, verbosity=self.verbosity)
    for (key, val) in self.gurobi_params.items():
      kpp.model.setParam(key, val)

    if self.params['y-cut'] or self.params['yz-cut'] or self.params['z-cut']:
      max_cliques = g.maximal_cliques()
      results["clique number"] = max(len(nodes) for nodes in max_cliques)

    if self.params['y-cut']:
      self.y_cut_phase(kpp, max_cliques, results)
    else:
      results['y-cut time'] = 0.0
      results['y-cut lb'] = 0.0
      results['y-cut constraints added'] = 0
      results['y-cut constraints removed'] = 0

    kpp.add_z_variables()
    if self.params['yz-cut']:
      for p in self.params['yz-cut']:
        kpp.add_separator(YZCliqueSeparator(max_cliques, p, self.k, self.k2))
      start = time()
      results['yz-cut constraints added'] = kpp.cut()
      end = time()
      results['yz-cut time'] = end - start
      results['yz-cut lb'] = kpp.model.objVal

      if self.params['yz-cut removal']:
        results["yz-cut constraints removed"] = kpp.remove_redundant_constraints(
            hard=(self.params['yz-cut removal']), allowed_slack=self.params['removal slack'])
      kpp.sep_algs.clear()
    else:
      results['yz-cut time'] = 0.0
      results['yz-cut lb'] = results['y-cut lb']
      results['yz-cut constraints added'] = 0
      results['yz-cut constraints removed'] = 0

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
    else:
      results['z-cut time'] = 0.0
      results['z-cut lb'] = results['yz-cut lb']
      results['z-cut constraints added'] = 0
      results['z-cut constraints removed'] = 0

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
