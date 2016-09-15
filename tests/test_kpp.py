import unittest
from random import seed
import igraph as ig
from kpp import KPP, KPPExtension, CliqueSeparator, YZCliqueSeparator

seed(1)

class TestKPP(unittest.TestCase):
  def setUp(self):
    pass
    
  def test_kpp(self):
    G = ig.Graph.GRG(100, 0.12)
    print(G.maximal_cliques())
    plain_kpp = KPP(G, 3)
    plain_kpp.solve()
    plain_obj_val = plain_kpp.model.objVal
    max_cliques = G.maximal_cliques()
    cuts_kpp = KPP(G, 3)
    cuts_kpp.add_separator(CliqueSeparator(max_cliques, 4, 3))
    cuts_kpp.add_separator(CliqueSeparator(max_cliques, 5, 3))
    cuts_kpp.cut()
    cuts_kpp.solve()
    cuts_obj_val = cuts_kpp.model.objVal
    self.assertAlmostEqual(plain_obj_val, cuts_obj_val)

  def test_kpp_extension(self):
    G = ig.Graph.GRG(20, 0.6)
    plain_kpp = KPPExtension(G)
    plain_kpp.solve()
    plain_obj_val = plain_kpp.model.objVal
    max_cliques = G.maximal_cliques()
    print(max_cliques)
    cuts_kpp = KPPExtension(G)
    y_sep_alg_1 = CliqueSeparator(max_cliques, 4, 3)
    y_sep_alg_2 = CliqueSeparator(max_cliques, 5, 3)
    yz_sep_alg = YZCliqueSeparator(max_cliques, 7)
    cuts_kpp.add_separator(y_sep_alg_1)
    cuts_kpp.add_separator(y_sep_alg_2)
    cuts_kpp.cut()
    cuts_kpp.sep_algs=[]
    cuts_kpp.add_z_variables()
    cuts_kpp.add_separator(yz_sep_alg)
    cuts_kpp.cut()
    cuts_kpp.solve()
    cuts_obj_val = cuts_kpp.model.objVal
    self.assertAlmostEqual(plain_obj_val, cuts_obj_val)


unittest.main()
