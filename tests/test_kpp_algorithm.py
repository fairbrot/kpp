from random import seed
import igraph as ig
import yaml
from kpp import KPP, KPPExtension, YCliqueSeparator, ZCliqueSeparator, YZCliqueSeparator, KPPAlgorithm

seed(1)

G = ig.Graph.GRG(100, 0.15)
params={'preprocess': True,
        'y_cut': True,
        'y_cut_clique_sizes': [4,5,7],
        'y_cut_removal':1,
        'yz_cut': True,
        'yz_cut_clique_sizes': [7,8],
        'yz_cut_removal':1,
        'z_cut': True,
        'z_cut_clique_sizes': [8],
        'symmetry_breaking': True}
  
kpp = KPPAlgorithm(G, **params)
results = kpp.run()
print(yaml.dump(results, indent=1))
