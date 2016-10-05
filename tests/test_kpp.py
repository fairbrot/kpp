import unittest
from random import seed
import igraph as ig
from kpp import KPP, KPPExtension, YCliqueSeparator, ZCliqueSeparator, YZCliqueSeparator

seed(1)

class TestKPP(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    super(TestKPP, cls).setUpClass()
    print("Running TestKPP...")
    cls.G = ig.Graph.GRG(30, 0.25)
    cls.max_cliques = cls.G.maximal_cliques()
    print(cls.max_cliques)
    plain_kpp = KPP(cls.G, 3, verbosity=0)
    plain_kpp.solve()
    cls.obj_val = plain_kpp.model.objVal

  def setUp(self):
    pass

  def test_cuts(self):
    print("\ttest_cuts...")
    cuts_kpp = KPP(self.G, 3, verbosity=0)
    cuts_kpp.add_separator(YCliqueSeparator(self.max_cliques, 4, 3))
    cuts_kpp.add_separator(YCliqueSeparator(self.max_cliques, 5, 3))
    cuts_kpp.cut()
    cuts_kpp.solve()
    obj_val = cuts_kpp.model.objVal
    self.assertAlmostEqual(self.obj_val, obj_val)

  def test_break_symmetry(self):
    print("\ttest_break_symmetry...")
    sym_kpp = KPP(self.G, 3, verbosity=0)
    sym_kpp.break_symmetry()
    sym_kpp.solve()
    obj_val = sym_kpp.model.objVal
    self.assertAlmostEqual(self.obj_val, obj_val)

  def test_cuts_and_break_symmetry(self):
    print("\ttest_cuts_and_break_symmetry...")
    kpp = KPP(self.G, 3, verbosity=0)
    kpp.add_separator(YCliqueSeparator(self.max_cliques, 4, 3))
    kpp.add_separator(YCliqueSeparator(self.max_cliques, 5, 3))
    kpp.cut()
    kpp.break_symmetry()
    kpp.solve()
    obj_val = kpp.model.objVal
    self.assertAlmostEqual(self.obj_val, obj_val)

class TestKPPExtension(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    super(TestKPPExtension, cls).setUpClass()
    print("Running TestKPPExtension...")
    cls.G = ig.Graph.GRG(14, 0.6)
    cls.max_cliques = cls.G.maximal_cliques()
    print(cls.max_cliques)
    plain_kpp = KPPExtension(cls.G, verbosity=0)
    plain_kpp.solve()
    cls.obj_val = plain_kpp.model.objVal

  def setUp(self):
    pass

  def test_cuts(self):
    print("\ttest_cuts...")
    cuts_kpp = KPPExtension(self.G, verbosity=0)
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
    self.assertAlmostEqual(self.obj_val, cuts_obj_val)

  def test_break_symmetry(self):
    print("\ttest_break_symmetry...")
    sym_kpp = KPPExtension(self.G, verbosity=0)
    sym_kpp.break_symmetry()
    sym_kpp.solve()
    obj_val = sym_kpp.model.objVal
    self.assertAlmostEqual(self.obj_val, obj_val)

  def test_cuts_and_break_symmetry(self):
    print("\ttest_cuts_and_break_symmetry...")
    kpp = KPPExtension(self.G, verbosity=0)
    y_sep_alg_1 = YCliqueSeparator(self.max_cliques, 4, 3)
    y_sep_alg_2 = YCliqueSeparator(self.max_cliques, 5, 3)
    yz_sep_alg = YZCliqueSeparator(self.max_cliques, 7)
    z_sep_alg = ZCliqueSeparator(self.max_cliques, 8)
    kpp.add_separator(y_sep_alg_1)
    kpp.add_separator(y_sep_alg_2)
    kpp.cut()
    kpp.sep_algs=[]
    kpp.add_z_variables()
    kpp.add_separator(yz_sep_alg)
    kpp.add_separator(z_sep_alg)
    kpp.cut()

    kpp.break_symmetry()
    kpp.solve()
    obj_val = kpp.model.objVal
    self.assertAlmostEqual(self.obj_val, obj_val)

unittest.main()
