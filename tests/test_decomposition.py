import unittest
from random import seed
import igraph as ig
from kpp.graph import decompose_graph
from kpp import KPP, KPPExtension, YCliqueSeparator, YZCliqueSeparator, ZCliqueSeparator

seed(1)


def cut_and_solve_basic(kpp):
  max_cliques = kpp.G.maximal_cliques()
  k = kpp.k
  kpp.add_separator(YCliqueSeparator(max_cliques, 4, k))
  kpp.add_separator(YCliqueSeparator(max_cliques, 5, k))
  kpp.cut()
  kpp.solve()


def cut_and_solve_extension(kpp):
  max_cliques = kpp.G.maximal_cliques()
  k = kpp.k
  k2 = kpp.k2
  kpp.add_separator(YCliqueSeparator(max_cliques, 4, k))
  kpp.add_separator(YCliqueSeparator(max_cliques, 5, k))
  kpp.cut()
  kpp.sep_algs.clear()
  kpp.add_z_variables()
  kpp.add_separator(YZCliqueSeparator(max_cliques, 7, k, k2))
  kpp.add_separator(ZCliqueSeparator(max_cliques, 8, k, k2))
  kpp.cut()
  kpp.solve()


class TestDecomposition(unittest.TestCase):

  def setUp(self):
    pass

  def test_kpp_opt_val(self):
    print('\n\ntest_kpp_opt_val...\n')
    G = ig.Graph.GRG(100, 0.12)
    max_cliques = G.maximal_cliques()
    print(max_cliques)
    comps = decompose_graph(G, 3)
    comps_sum = 0.0
    for g in comps:
      kpp = KPP(g, 3)
      cut_and_solve_basic(kpp)
      comps_sum += kpp.model.objVal
    full_kpp = KPP(G, 3)
    cut_and_solve_basic(full_kpp)
    self.assertAlmostEqual(full_kpp.model.objVal, comps_sum)

  def test_kpp_extension_opt_val(self):
    print('\n\ntest_kpp_extension_opt_val...\n')
    G = ig.Graph.GRG(30, 0.35)
    max_cliques = G.maximal_cliques()
    print(max_cliques)
    comps = decompose_graph(G, 3)
    comps_sum = 0.0
    for g in comps:
      kpp = KPPExtension(g, 3, 2)
      cut_and_solve_extension(kpp)
      comps_sum += kpp.model.objVal
    full_kpp = KPPExtension(G, 3, 2)
    cut_and_solve_extension(full_kpp)
    self.assertAlmostEqual(full_kpp.model.objVal, comps_sum)


# unittest.main()
