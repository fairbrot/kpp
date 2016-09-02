import igraph as ig
from kpp import *

n, R = 30, 0.25
G = ig.Graph.GRG(n, R)
print(G)
print(G.maximal_cliques())
k = 3

kpp = KPP(G, k)

sep_alg_1 = CliqueSeparator(G.maximal_cliques(), k+1, k)
sep_alg_2 = CliqueSeparator(G.maximal_cliques(), k+2, k)
kpp.add_separator(sep_alg_1)
kpp.add_separator(sep_alg_2)
kpp.cut()
kpp.remove_redundant_constraints(True)
kpp.solve()
  
