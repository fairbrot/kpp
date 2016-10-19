from random import seed
import igraph as ig
import yaml
from kpp import KPP, KPPExtension, YCliqueSeparator, ZCliqueSeparator, YZCliqueSeparator, KPPAlgorithm

seed(1)

G = ig.Graph.GRG(100, 0.15)
params={'preprocess': True,
        'y-cut': [4,5,7],
        'phase 1 removal':1,
        'yz-cut': [7,8],
        'phase 2 removal':1,
        'z-cut': [8],
        'symmetry breaking': True,
        'MIPFocus': 1}
  
kpp = KPPAlgorithm(G, 3, **params)
results = kpp.run()
print(yaml.dump(results, indent=1))
