from abc import ABCMeta, abstractmethod
import sys
from time import time
import igraph as ig
from .kpp import KPPExtension
from .separation import *
from .graph import decompose_graph

class KPPAlgorithm:
  def __init__(self, G, **kwargs):
    self.output = dict()
    self.G = G
    self.preprocess = kwargs.pop('preprocess', False)
    self.y_cut = kwargs.pop('y-cut', False)
    self.y_cut_clique_sizes = kwargs.pop('y-cut clique sizes', [])
    self.y_cut_removal = kwargs.pop('y-cut removal', 0)
    self.yz_cut = kwargs.pop('yz-cut', False)
    self.yz_cut_clique_sizes = kwargs.pop('yz-cut clique sizes', [])
    self.yz_cut_removal = kwargs.pop('yz-cut removal', 0)
    self.z_cut = kwargs.pop('z-cut', False)
    self.z_cut_clique_sizes = kwargs.pop('z-cut clique sizes', [])
    self.symmetry_breaking = kwargs.pop('symmetry breaking', False)
    self.verbosity = kwargs.pop('verbosity', 1)
    if kwargs:
        raise ValueError("Invalid arguments passed to constructor: %o" % kwargs.keys())

  def run(self):
    if self.verbosity > 1:
      print('Solving KPP Modulo-6 Extension Problem')
      print('Input graph has %d nodes and %d edges' % (self.G.vcount(), self.G.ecount()))
    if self.preprocess:
      start=time()
      graphs=decompose_graph(self.G, 3)
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
    if self.verbosity > 0: print("Running exact solution algorithm")
    results=dict()
    kpp=KPPExtension(g)
    if self.y_cut or self.yz_cut or self.z_cut:
      max_cliques=g.maximal_cliques()
      results["max clique size"] = max(len(nodes) for nodes in max_cliques)
            
    if self.y_cut:
      for p in self.y_cut_clique_sizes:
        kpp.add_separator(YCliqueSeparator(max_cliques, p, 3))
      start=time()
      kpp.cut()
      end=time()
      results["y-cut time"] = end-start
      results["y-cut lb"] = kpp.model.objVal
      if self.y_cut_removal:
        results["y-cut constraints removed"] = kpp.remove_redundant_constraints(hard=(self.y_cut_removal>1))
      kpp.sep_algs.clear()
                
    if self.yz_cut or self.z_cut:
      if self.yz_cut:
        for p in self.yz_cut_clique_sizes:
          kpp.add_separator(YZCliqueSeparator(max_cliques, p))
      if self.z_cut:
        for p in self.z_cut_clique_sizes:
          kpp.add_separator(ZCliqueSeparator(max_cliques, p))
      start=time()
      kpp.cut()
      end=time()
      results["yz-cut time"] = end-start
      if self.yz_cut_removal:
        results["yz-cut constraints removed"] = kpp.remove_redundant_constraints(hard=(self.yz_cut_removal>1))
      results["yz-cut lb"] = kpp.model.objVal
      kpp.sep_algs.clear()

    kpp.add_node_variables()
    if self.symmetry_breaking:
      kpp.break_symmetry()

    start=time()
    kpp.solve()
    end=time()
    if self.verbosity > 0: print('')
    results["brand and bound time"]=end-start
    results["optimal value"] = kpp.model.objVal
    return results
