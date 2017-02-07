from math import isclose
import igraph as ig
from random import seed
from kpp import KPP, YCliqueSeparator, ProjectedCliqueSeparator


def test_CliqueSeparator(graph, k, clique_sizes, mode,
                         opt_val=None, max_cliques=None):
  if not opt_val:
    kpp = KPP(graph, k, verbosity=0)
    opt_val = kpp.solve()
  if not max_cliques:
    max_cliques = graph.maximal_cliques()
  kpp_sep = KPP(graph, k, verbosity=0)
  for p in clique_sizes:
    if mode == 'basic':
      kpp_sep.add_separator(YCliqueSeparator(max_cliques, p, k))
    elif mode == 'projected':
      colours = range(1, k - 1)
      kpp_sep.add_separator(
          ProjectedCliqueSeparator(max_cliques, p, k, colours))
  if mode == 'projected':
    kpp_sep.add_node_variables()
  kpp_sep.cut()
  kpp_sep.solve()
  new_opt_val = kpp_sep.model.objVal
  assert isclose(opt_val, new_opt_val), \
      "Optimal value changes for k = %d and clique sizes %s" \
      " from %.2f to %.2f when adding %s inequalities" \
      % (k, clique_sizes, opt_val, new_opt_val, mode)


seed(1)
G = ig.Graph.GRG(15, 0.9)
max_cliques = G.maximal_cliques()
print("Maximal clique size: ", max(len(clq) for clq in max_cliques))

print("Testing standard and projected clique inequalities for KPP...")

for k in range(3, 6):
  kpp = KPP(G, k, verbosity=0)
  clique_sizes = range(k + 1, 2 * k)
  kpp.solve()
  opt_val = kpp.model.objVal
  test_CliqueSeparator(G, k, clique_sizes, 'basic', opt_val, max_cliques)
  test_CliqueSeparator(G, k, clique_sizes, 'projected', opt_val, max_cliques)
