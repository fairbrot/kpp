import unittest
from random import seed
import igraph as ig
from kpp.graph import decompose_graph
from kpp import KPP, KPPExtension

seed(1)

class TestDecomposition(unittest.TestCase):
  def setUp(self):
    pass
    
  def test_kpp_opt_val(self):
    G = ig.Graph.GRG(100, 0.12)
    print(G.maximal_cliques())
    comps = decompose_graph(G, 3)
    comps_sum = 0.0
    for g in comps:
      kpp=KPP(g,3)
      kpp.solve()
      comps_sum+=kpp.model.objVal
    full_kpp = KPP(G,3)
    full_kpp.solve()
    self.assertAlmostEqual(full_kpp.model.objVal, comps_sum)
  
  def test_kpp_extension_opt_val(self):
    G = ig.Graph.GRG(100, 0.12)
    print(G.maximal_cliques())
    comps = decompose_graph(G, 3)
    comps_sum = 0.0
    for g in comps:
      kpp=KPPExtension(g)
      kpp.solve()
      comps_sum+=kpp.model.objVal
    full_kpp = KPP(G,3)
    full_kpp.solve()
    self.assertAlmostEqual(full_kpp.model.objVal, comps_sum)

    
unittest.main()
