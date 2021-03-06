from abc import ABCMeta, abstractmethod
import sys
from math import ceil
from gurobipy import Model, GRB, LinExpr
from .separation import Solution


class KPPBase(metaclass=ABCMeta):

  def __init__(self, G, k, verbosity):
    self.G = G
    self.model = Model()
    self.model.modelSense = GRB.MINIMIZE
    self.k = k
    self.y = {}
    self.model.setParam("OutputFlag", 0)
    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      if 'weight' in e.attributes():
        self.y[u, v] = self.model.addVar(obj=e['weight'], ub=1.0)
      else:
        self.y[u, v] = self.model.addVar(obj=1.0, ub=1.0)
    self.x = {}
    self.z = {}
    self.discretized = False
    self.constraints = []
    self.sep_algs = []
    self.out = sys.stdout
    self.verbosity = verbosity

  def get_solution(self):
    return Solution(self.model.getAttr('x', self.x),
                    self.model.getAttr('x', self.y),
                    self.model.getAttr('x', self.z))

  def get_colouring(self):
    '''Map of colours to nodes with that colour'''
    if self.discretized and self.model.status == 2:
      n = self.G.vcount()
      K = self.num_colours()
      colouring = [[] for i in range(K)]
      x = self.get_solution().x
      for u in range(n):
        for i in range(K):
          if abs(x[u, i] - 1.0) < 1e-3:
            colouring[i].append(u)
      return colouring
    else:
      raise(RuntimeError('Can only extract colouring if KPP has been fully solved'))

  def add_fractional_cut(self):
    if self.x:
      raise RuntimeError(
          'Fractional y-cut can only be added before the x variables have been added')
    if not self.model.status == 2:
      raise RuntimeError(
          'Fractional y-cut can only be added after successful a cutting plane phase (and before constraint removal)')
    y_lb = sum(self.model.getAttr('x', self.y).values())
    eps = self.model.params.optimalityTol
    if abs(ceil(y_lb) - y_lb) > eps:
      sum_y = LinExpr()
      for e in self.G.es():
        u = min(e.source, e.target)
        v = max(e.source, e.target)
        sum_y.addTerms(1.0, self.y[u, v])
      self.model.addConstr(sum_y >= ceil(y_lb))
      return True

  def cut(self):
    if self.discretized:
      raise RuntimeError(
          'Cutting plan algorithm can only be used before model has been discretized')

    if self.verbosity > 0:
      print('Running cutting plane algorithms', file=self.out)

    it_count = 0
    total_added = 0
    while True:
      it_count += 1
      self.model.optimize()
      if self.verbosity > 1:
        print('\n', 10 * '-', 'Iteration ', it_count,
              10 * '-', file=self.out)
        print(" Objective value: ", self.model.objVal, file=self.out)
      new_constraints = []
      sol = self.get_solution()
      for sep_alg in self.sep_algs:
        constr_list = sep_alg.find_violated_constraints(
            sol, self.verbosity - 1)
        new_constraints.extend(constr_list)

      total_added += len(new_constraints)
      for constr in new_constraints:
        self.add_constraint(constr)
      if not new_constraints:
        if self.verbosity > 1:
          print(' Found no constraints to add; exiting cutting plane loop', file=self.out)
        if self.verbosity > 0:
          print(' Added a total of', total_added, 'constraints', file=self.out)
          print(' Lower bound: ', self.model.objVal)
        break

    return total_added

  def remove_redundant_constraints(self, hard=False, allowed_slack=1e-3):
    slack, dual = 0, 0
    to_remove = []

    for constr in self.constraints:
      if abs(constr.Slack) > allowed_slack:
        to_remove.append(constr)
        slack += 1
      elif hard and constr.Pi == 0.0:
        to_remove.append(constr)
        dual += 1

    for constr in to_remove:
      self.model.remove(constr)
      self.constraints.remove(constr)

    if self.verbosity > 0:
      print(" Removed", slack, "constraints with slack greater than",
            allowed_slack, file=self.out)
      print(" Removed", dual, "constraints with zero dual variable", file=self.out)
      print("", len(self.constraints), "constraints remaining", file=self.out)

    self.model.update()
    return slack + dual

  def add_separator(self, sep_alg):
    self.sep_algs.append(sep_alg)

  def add_constraint(self, constraint):
    expr = LinExpr()
    for e, coef in constraint.x_coefs.items():
      expr.addTerms(coef, self.x[e])
    for e, coef in constraint.y_coefs.items():
      expr.addTerms(coef, self.y[e])
    for e, coef in constraint.z_coefs.items():
      expr.addTerms(coef, self.z[e])
    if constraint.op == '<':
      cons = self.model.addConstr(expr <= constraint.rhs)
    elif constraint.op == '>':
      cons = self.model.addConstr(expr >= constraint.rhs)
    elif constraint.op == '==':
      cons = self.model.addConstr(expr == constraint.rhs)
    self.constraints.append(cons)

  def solve(self):
    if not self.x:
      self.add_node_variables()
    if not self.discretized:
      self.discretize()
    if self.verbosity > 0:
      print("Running branch-and-bound", file=self.out)
    self.model.optimize()
    if self.verbosity > 0:
      print(" Optimal objective value: ", self.model.objVal, file=self.out)

  @abstractmethod
  def add_node_variables(self):
    pass

  @abstractmethod
  def num_colours(self):
    pass

  def discretize(self):
    if not self.x:
      raise RuntimeError(
          "Cannot discretize problem before x variables have been added")
    for var in self.x.values():
      var.vtype = GRB.BINARY
    self.discretized = True

  @abstractmethod
  def print_solution(self):
    pass

  @abstractmethod
  def num_colours(self):
    pass


class KPP(KPPBase):

  def __init__(self, G, k, x_coefs=None, verbosity=1):
    KPPBase.__init__(self, G, k, verbosity)
    self.x_coefs = x_coefs

  def num_colours(self):
    return self.k

  def add_node_variables(self):
    n = self.G.vcount()
    for i in range(n):
      for j in range(self.k):
        self.x[i, j] = self.model.addVar(vtype=GRB.CONTINUOUS)
    if self.x_coefs:
      for ((i, c), coef) in self.x_coefs.items():
        self.x[i, c].obj = coef

    self.model.update()

    for i in range(n):
      total_assign = LinExpr()
      for j in range(self.k):
        total_assign.addTerms(1.0, self.x[i, j])
      self.model.addConstr(total_assign == 1.0)

    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      for i in range(self.k):
        self.model.addConstr(self.y[u, v] >= self.x[u, i] + self.x[v, i] - 1.0)
        self.model.addConstr(self.x[u, i] >= self.x[v, i] + self.y[u, v] - 1.0)
        self.model.addConstr(self.x[v, i] >= self.x[u, i] + self.y[u, v] - 1.0)
    self.model.update()

  def break_symmetry(self):
    if self.verbosity > 0:
      print("Adding symmetry breaking constraints")
    if not self.x:
      self.add_node_variables()
    for i in range(self.k - 1):
      sym = LinExpr()
      for j in range(i + 1):
        sym.addTerms(1.0, self.x[i, j])
    self.model.addConstr(sym == 1)
    self.model.update()

  def print_solution(self):
    sol = self.get_solution()
    x, y = sol.x, sol.y
    clusters = []
    for i in range(self.k):
      cluster = []
      for j in range(self.G.vcount()):
        if abs(x[j, i] - 1.0) < 1e-4:
          cluster.append(j)
      clusters.append(cluster)
    for i in range(self.k):
      print("Colour", i, ": ", clusters[i], file=self.out)

    print("Clashes: ", file=self.out)
    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      if abs(y[u, v] - 1.0) < 1e-4:
        print((u, v), end=', ', file=self.out)
    print('\n', file=self.out)

  def num_colours(self):
    return self.k


class KPPExtension(KPPBase):

  def __init__(self, G, k1, k2, verbosity=1):
    KPPBase.__init__(self, G, k1, verbosity)
    self.k2 = k2

  def num_colours(self):
    return self.k * self.k2

  def add_z_variables(self):
    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      self.z[u, v] = self.model.addVar(obj=1.0, ub=1.0)

  def add_node_variables(self):
    if not self.z:
      self.add_z_variables()
    n = self.G.vcount()
    for i in range(n):
      for j in range(self.k2 * self.k):
        self.x[i, j] = self.model.addVar(vtype=GRB.CONTINUOUS)

    self.model.update()

    for i in range(n):
      total_assign = LinExpr()
      for j in range(self.k2 * self.k):
        total_assign.addTerms(1.0, self.x[i, j])
      self.model.addConstr(total_assign == 1.0)

    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      for c in range(self.k):
        mod_k_clashes = LinExpr()
        for j in range(self.k2):
          mod_k_clashes.addTerms(1.0, self.x[u, c + j * self.k])
          mod_k_clashes.addTerms(1.0, self.x[v, c + j * self.k])
        self.model.addConstr(self.y[u, v] >= mod_k_clashes - 1.0)

    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      for c in range(self.k2 * self.k):
        self.model.addConstr(self.z[u, v] >= self.x[u, c] + self.x[v, c] - 1.0)
        self.model.addConstr(self.x[u, c] >= self.x[v, c] + self.z[u, v] - 1.0)
        self.model.addConstr(self.x[v, c] >= self.x[u, c] + self.z[u, v] - 1.0)

  def break_symmetry(self):
    if not self.G.vcount() > self.k2 * self.k:
      if self.verbosity > 0:
        print('Too few nodes to add symmetry breaking constraints')
    else:
      if self.verbosity > 0:
        print("Adding symmetry breaking constraints")
      if not self.x:
        self.add_node_variables()
      n = self.G.vcount()
      for v in range(n):
        for c in range(self.k2 * self.k):
          if (c // self.k) + (c % self.k) >= v + 1:
            self.x[v, c].ub = self.x[v, c].start = 0.0
    self.model.update()

  def print_solution(self):
    sol = self.get_solution()
    x, y, z = sol.x, sol.y, sol.z
    clusters = []
    n = self.G.vcount()
    if x:
      for c in range(self.k2 * self.k):
        cluster = []
        for j in range(n):
          if abs(x[j, c] - 1.0) < 1e-4:
            cluster.append(j)
        clusters.append(cluster)
      for i in range(self.k2 * self.k):
        print("Colour", i, ": ", clusters[i], file=self.out)

    print("3-Clashes: ")
    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      if abs(y[u, v] - 1.0) < 1e-4:
        print((u, v), end=', ', file=self.out)
    print('\n', file=self.out)

    print("6-Clashes: ")
    for e in self.G.es():
      u = min(e.source, e.target)
      v = max(e.source, e.target)
      if abs(z[u, v] - 1.0) < 1e-4:
        print((u, v), end=', ', file=self.out)
    print('\n', file=self.out)

  def num_colours(self):
    return self.k * self.k2
