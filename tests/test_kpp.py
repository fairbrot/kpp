import unittest
from random import seed
import igraph as ig
from kpp import KPP, KPPExtension, YCliqueSeparator, ZCliqueSeparator, YZCliqueSeparator

seed(1)

class TestKPP(unittest.TestCase):
  def setUp(self):
    self.G = ig.Graph.GRG(20, 0.5)
    self.max_cliques = self.G.maximal_cliques()
    print(self.max_cliques)
    
  def test_kpp(self):
    plain_kpp = KPP(self.G, 3)
    plain_kpp.solve()
    plain_obj_val = plain_kpp.model.objVal

    cuts_kpp = KPP(self.G, 3)
    cuts_kpp.add_separator(YCliqueSeparator(self.max_cliques, 4, 3))
    cuts_kpp.add_separator(YCliqueSeparator(self.max_cliques, 5, 3))
    cuts_kpp.cut()
    cuts_kpp.solve()
    cuts_obj_val = cuts_kpp.model.objVal
    self.assertAlmostEqual(plain_obj_val, cuts_obj_val)

  def test_kpp_extension(self):
    plain_kpp = KPPExtension(self.G)
    plain_kpp.solve()
    plain_obj_val = plain_kpp.model.objVal

    cuts_kpp = KPPExtension(self.G)
    y_sep_alg_1 = YCliqueSeparator(self.max_cliques, 4, 3)
    y_sep_alg_2 = YCliqueSeparator(self.max_cliques, 5, 3)
    yz_sep_alg = YZCliqueSeparator(self.max_cliques, 7)
    z_sep_alg = ZCliqueSeparator(self.max_cliques, 8)
    cuts_kpp.add_separator(y_sep_alg_1)
    cuts_kpp.add_separator(y_sep_alg_2)
    cuts_kpp.cut()
    cuts_kpp.sep_algs=[]
    cuts_kpp.add_z_variables()
    cuts_kpp.add_separator(yz_sep_alg)
    cuts_kpp.add_separator(z_sep_alg)
    cuts_kpp.cut()
    cuts_kpp.solve()
    cuts_obj_val = cuts_kpp.model.objVal
    self.assertAlmostEqual(plain_obj_val, cuts_obj_val)

unittest.main()
