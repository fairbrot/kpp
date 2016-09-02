import igraph as ig
from kpp import *

import random

random.seed(1)

n, R = 50, 0.25
G = ig.Graph.GRG(n, R)
print(G)
print(G.maximal_cliques())
k = 3

# kpp = KPP(G, k)

# sep_alg_1 = CliqueSeparator(G.maximal_cliques(), k+1, k)
# sep_alg_2 = CliqueSeparator(G.maximal_cliques(), k+2, k)
# kpp.add_separator(sep_alg_1)
# kpp.add_separator(sep_alg_2)
# kpp.cut()
# kpp.remove_redundant_constraints(True)
# kpp.solve()

max_cliques = G.maximal_cliques()
y_sep_alg_1 = CliqueSeparator(max_cliques, 4, 3)
y_sep_alg_2 = CliqueSeparator(max_cliques, 5, 3)
yz_sep_alg = YZCliqueSeparator(max_cliques, 7)

kpp_extension = KPPExtension(G)
kpp_extension.add_separator(y_sep_alg_1)
kpp_extension.add_separator(y_sep_alg_2)
kpp_extension.cut()
kpp_extension.sep_algs=[]
kpp_extension.add_z_variables()
kpp_extension.add_separator(yz_sep_alg)
kpp_extension.cut()


kpp_extension.solve()
kpp_extension.print_solution()
