from random import seed
from itertools import product
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
params = {'preprocess': False,
          'x-cut removal': 1,
          'y-cut removal': 1,
          'symmetry breaking': False,
          'fractional y-cut': True,
          'removal slack': 0.5,
          'MIPFocus': 1,
          'verbosity': 0}


@pytest.mark.parametrize("n", [6, 7, 8, 9])
@pytest.mark.parametrize("k", [2, 3, 4])
def test_KPPBasicAlgorithm(n, k):
  graph = ig.Graph.Full(n)
  x_coefs = dict()
  for (i, c) in product(range(n), range(k)):
    x_coefs[i, c] = random()

  for e in graph.es():
    e["weight"] = random()
  # kpp = KPP(graph, k, x_coefs=x_coefs, verbosity=0)
  kpp = KPP(graph, k, verbosity=0)
  kpp.solve()
  opt_val = kpp.model.objVal
  params['y-cut'] = range(k + 1, n + 1)
  params['x-cut'] = range(k + 1, n + 1)
  params['x-cut colours'] = [c for r in range(1, k)
                             for c in combinations(range(k), r)]
  # kpp_alg = KPPBasicAlgorithm(graph, k, x_coefs=x_coefs, **params)
  kpp_alg = KPPBasicAlgorithm(graph, k, **params)
  results = kpp_alg.run()
  if params['preprocess']:
    new_opt_val = sum(results['solution']['optimal value'])
  else:
    new_opt_val = results['solution']['optimal value']
  assert isclose(opt_val, new_opt_val)


params_ext = {'preprocess': False,
              'y-cut removal': 1,
              'yz-cut removal': 1,
              'symmetry breaking': True,
              'fractional y-cut': True,
              'removal slack': 0.5,
              'MIPFocus': 1,
              'verbosity': 0}


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
  params_ext['y-cut'] = range(k + 1, n + 1)
  params_ext['yz-cut'] = range(k + 1, n + 1)
  params_ext['z-cut'] = range(k * k2 + 1, n + 1)
  kpp_alg = KPPAlgorithm(graph, k, k2, **params_ext)
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
