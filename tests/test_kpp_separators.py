from math import isclose
import pytest
import igraph as ig
from random import seed, random
from itertools import combinations
from kpp import KPP, YCliqueSeparator, ProjectedCliqueSeparator

seed(1)


@pytest.mark.parametrize("n", [6, 7, 8, 9])
@pytest.mark.parametrize("k", [2, 3, 4])
def test_YCliqueSeparator(n, k):
  graph = ig.Graph.Full(n)
  for e in graph.es():
    e["weight"] = random()
  kpp = KPP(graph, k, verbosity=0)
  kpp.solve()
  opt_val = kpp.model.objVal
  max_cliques = graph.maximal_cliques()  # [graph.vs()]
  kpp_sep = KPP(graph, k, verbosity=0)
  for p in range(k + 1, n + 1):
    kpp_sep.add_separator(YCliqueSeparator(max_cliques, p, k))
  kpp_sep.cut()
  kpp_sep.add_node_variables()
  kpp_sep.solve()
  new_opt_val = kpp_sep.model.objVal
  assert isclose(opt_val, new_opt_val)


@pytest.mark.parametrize("n", [6, 7, 8])
@pytest.mark.parametrize("k", [2, 3, 4])
def test_ProjectedCliqueSeparator(n, k):
  graph = ig.Graph.Full(n)
  for e in graph.es():
    e["weight"] = random()
  kpp = KPP(graph, k, verbosity=0)
  kpp.solve()
  opt_val = kpp.model.objVal
  max_cliques = graph.maximal_cliques()  # [graph.vs()]
  kpp_sep = KPP(graph, k, verbosity=0)
  for p in range(1, n + 1):
    for r in range(max(k - p + 1, 1), k):
      for c in combinations(range(k), r):
        kpp_sep.add_separator(ProjectedCliqueSeparator(max_cliques, p, k, c))
  kpp_sep.add_node_variables()
  num = kpp_sep.cut()
  print("Added ", num, "projected clique inequalities")
  kpp_sep.solve()
  new_opt_val = kpp_sep.model.objVal
  assert isclose(opt_val, new_opt_val)
