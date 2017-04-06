from random import seed
import igraph as ig
import yaml
from math import isclose
import pytest
import igraph as ig
from random import seed, random
from itertools import combinations
from kpp import KPP, KPPExtension, KPPBasicAlgorithm, KPPAlgorithm


seed(1)

G = ig.Graph.GRG(50, 0.25)
params = {'preprocess': True,
          'x-cut removal': 1,
          'y-cut removal': 1,
          'yz-cut removal': 1,
          'symmetry breaking': True,
          'fractional y-cut': True,
          'removal slack': 0.5,
          'MIPFocus': 1}


@pytest.mark.parametrize("n", [6, 7, 8, 9])
@pytest.mark.parametrize("k", [2, 3, 4])
def test_KPPBasicAlgorithm(n, k):
  graph = ig.Graph.Full(n)
  for e in graph.es():
    e["weight"] = random()
  kpp = KPP(graph, k, verbosity=0)
  kpp.solve()
  opt_val = kpp.model.objVal
  y_cut = range(k + 1, n + 1)
  x_cut = range(k + 1, n + 1)
  colours = [c for r in range(1, k) for c in combinations(range(k), r)]
  kpp_alg = KPPBasicAlgorithm(graph, k, y_cut=y_cut, x_cut=x_cut,
                              x_cut_colours=colours, ** params)
  results = kpp_alg.run()
  if params['preprocess']:
    new_opt_val = sum(results['solution']['optimal value'])
  else:
    new_opt_val = results['solution']['optimal value']
  assert isclose(opt_val, new_opt_val)


@pytest.mark.parametrize("n", [6, 7, 8])
@pytest.mark.parametrize("k", [2, 3])
@pytest.mark.parametrize("k2", [2, 3])
def test_KPPAlgorithm(n, k, k2):
  graph = ig.Graph.Full(n)
  for e in graph.es():
    e["weight"] = random()
  kpp = KPPExtension(graph, k, k2, verbosity=0)
  kpp.solve()
  opt_val = kpp.model.objVal
  y_cut = range(k + 1, n + 1)
  x_cut = range(k + 1, n + 1)
  z_cut = range(k * k2 + 1, n + 1)
  colours = [c for r in range(1, k) for c in combinations(range(k), r)]
  kpp_alg = KPPAlgorithm(graph, k, k2, y_cut=y_cut, x_cut=x_cut,
                         x_cut_colours=colours, z_cut=z_cut, ** params)
  results = kpp_alg.run()
  if params['preprocess']:
    new_opt_val = sum(results['solution']['optimal value'])
  else:
    new_opt_val = results['solution']['optimal value']
  assert isclose(opt_val, new_opt_val)


# k = 3
# k2 = 2
# kpp = KPPAlgorithm(G, k, k2, verbosity=1, **params)

# results = kpp.run()
# print(yaml.dump(results, indent=1))
