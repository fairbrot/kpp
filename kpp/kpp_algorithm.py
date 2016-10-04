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
    self.y_cut = kwargs.pop('y_cut', False)
    self.y_cut_clique_sizes = kwargs.pop('y_cut_clique_sizes', [])
    self.y_cut_removal = kwargs.pop('y_cut_removal', 0)
    self.yz_cut = kwargs.pop('yz_cut', False)
    self.yz_cut_clique_sizes = kwargs.pop('yz_cut_clique_sizes', [])
    self.yz_cut_removal = kwargs.pop('yz_cut_removal', 0)
    self.z_cut = kwargs.pop('z_cut', False)
    self.z_cut_clique_sizes = kwargs.pop('z_cut_clique_sizes', [])
    self.symmetry_breaking = kwargs.pop('symmetry_breaking', False)
    if kwargs:
        raise ValueError("Invalid arguments passed to constructor: %o" % kwargs.keys())

  def run(self):
    if self.preprocess:
      start=time()
      graphs=decompose_graph(self.G, 3)
      end=time()
      self.output['preprocess_time'] = end-start
      self.output['preprocess_components'] = len(graphs)
      self.output['largest_components'] = max(g.vcount() for g in graphs)
      self.output['solution'] = dict()

      for g in graphs:
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
    results=dict()
    kpp=KPPExtension(g)
    if self.y_cut or self.yz_cut or self.z_cut:
      max_cliques=g.maximal_cliques()
      results["max_clique_size"] = max(len(nodes) for nodes in max_cliques)
            
    if self.y_cut:
      for p in self.y_cut_clique_sizes:
        kpp.add_separator(YCliqueSeparator(max_cliques, p, 3))
      start=time()
      kpp.cut()
      end=time()
      results["y_cut_time"] = end-start
      results["y_cut_lb"] = kpp.model.objVal
      if self.y_cut_removal:
        results["y_cut_constraints_removed"] = kpp.remove_redundant_constraints(hard=(self.y_cut_removal>1))
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
      results["yz_cut_time"] = end-start
      if self.yz_cut_removal:
        results["yz_cut_constraints_removed"] = kpp.remove_redundant_constraints(hard=(self.yz_cut_removal>1))
      results["yz_cut_lb"] = kpp.model.objVal
      kpp.sep_algs.clear()

    kpp.add_node_variables()
    start=time()
    kpp.solve()
    end=time()
    results["brand_and_bound_time"]=end-start
    results["optimal value"] = kpp.model.objVal
    return results

            
        
