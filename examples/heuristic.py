import igraph as ig
from kpp import KPPAlgorithm, two_stage_kpp_heuristic

n = 20
dens = 0.55

samples = 10

k1, k2 = 3, 2

params = dict()
params['y-cut'] = range(k1 + 1, n)
params['z-cut'] = range(k1 + k2 + 1, n)


for i in range(samples):
  G = ig.Graph.GRG(n, dens)
  kpp = KPPAlgorithm(G, k1, k2, verbosity=0, **params)
  out = kpp.run()['solution']
  print('exact: ', out['optimal value'], end=', ')
  print('heuristic: ', two_stage_kpp_heuristic(G, k1, k2))
