from random import seed
import igraph as ig
import yaml
from kpp import KPP, KPPExtension, YCliqueSeparator, ZCliqueSeparator, YZCliqueSeparator, KPPAlgorithm

seed(1)

G = ig.Graph.GRG(50, 0.3)
params = {'preprocess': True,
          'y-cut': [4, 5, 7],
          'y-cut removal': 1,
          'yz-cut': [7, 8],
          'yz-cut removal': 1,
          'z-cut': [8],
          'symmetry breaking': True,
          'fractional y-cut': True,
          'removal slack': 0.5,
          'MIPFocus': 1}

k = 3
k2 = 2
kpp = KPPAlgorithm(G, k, k2, verbosity=1, **params)
results = kpp.run()
print(yaml.dump(results, indent=1))
