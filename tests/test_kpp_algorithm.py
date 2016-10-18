from random import seed
import igraph as ig
import yaml
from kpp import KPP, KPPExtension, YCliqueSeparator, ZCliqueSeparator, YZCliqueSeparator, KPPAlgorithm

seed(1)

G = ig.Graph.GRG(100, 0.15)
params={'preprocess': True,
        'y-cut': True,
        'y-cut clique sizes': [4,5,7],
        'y-cut removal':1,
        'yz-cut': True,
        'yz-cut clique sizes': [7,8],
        'yz-cut removal':1,
        'z-cut': True,
        'z-cut clique sizes': [8],
        'symmetry breaking': True}
  
kpp = KPPAlgorithm(G, 3, **params)
results = kpp.run()
print(yaml.dump(results, indent=1))
