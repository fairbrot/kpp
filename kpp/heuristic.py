from .kpp import KPP


def two_stage_kpp_heuristic(G, k1, k2, verbosity=0):
  k1pp = KPP(G, k1, verbosity=verbosity)
  k1pp.solve()
  k_col = k1pp.get_colouring()
  obj = k1pp.model.objVal
  for i, nds in zip(range(k1), k_col):
    g = G.subgraph(nds)
    k2pp = KPP(g, k2, verbosity=verbosity)
    k2pp.solve()
    obj += k2pp.model.objVal
  return obj
