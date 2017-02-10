from abc import ABCMeta, abstractmethod
import heapq
import sys
from itertools import combinations


class Structure:
  _fields = []

  def __init__(self, *args, **kwargs):
    if len(args) > len(self._fields):
      raise TypeError('Expected {} arguments'.format(len(self._fields)))

    # Set all of the positional arguments
    for name, value in zip(self._fields, args):
      setattr(self, name, value)

    # Set the remaining keyword arguments
    for name in self._fields[len(args):]:
      setattr(self, name, kwargs.pop(name))

    # Check for any remaining unknown arguments
    if kwargs:
      raise TypeError('Invalid argument(s): {}'.format(','.join(kwargs)))


class Solution(Structure):
  _fields = ['x', 'y', 'z']


class Constraint(Structure):
  _fields = ['x_coefs', 'y_coefs', 'z_coefs', 'rhs', 'op']

  def __str__(self):
    out = ""
    for e, coef in self.y_coefs:
      out += "+ " + str(coef) + "y[" + str(e) + "]"
    if self.op == '<':
      out += ' <= '
    elif self.op == '>':
      out += ' >= '
    elif self.op == '=':
      out += ' == '
    out += str(self.rhs)
    return out


def p_cliques(max_cliques, p):
  p_cliques = []
  for clq in max_cliques:
    if len(clq) < p:
      continue
    for p_clq in combinations(clq, p):
      p_cliques.append(p_clq)
  return p_cliques


def edge_clique(clq):
  e_clq = [(min(u, v), max(u, v)) for (u, v) in combinations(clq, 2)]
  return e_clq


class CliqueSeparator(metaclass=ABCMeta):

  def __init__(self, max_cliques, p, k):
    self.max_constraints = 10
    self.out = sys.stdout
    self.eps = 1e-3
    self.cliques = p_cliques(max_cliques, p)
    self.edge_cliques = [edge_clique(clq) for clq in self.cliques]
    self.k = k
    self.p = p  # Clique size

  @abstractmethod
  def calculate_violation(self, sol, nodes, edges):
    pass

  def find_violated_cliques(self, sol):
    viol_clqs = []
    for nodes, edges in zip(self.cliques, self.edge_cliques):
      viol = self.calculate_violation(sol, nodes, edges)
      if viol > self.eps:
        viol_clqs.append((nodes, edges, viol))
    return viol_clqs

  @abstractmethod
  def clique_constraint(self, nodes, edges):
    pass

  def find_violated_constraints(self, sol, verbosity=1):
    cons = []
    viol_clqs = self.find_violated_cliques(sol)
    num_viol = len(viol_clqs)
    to_add = min(num_viol, self.max_constraints)
    if verbosity > 0:
      msg = " Adding {}/{} violated {}-cliques".format(
          to_add, num_viol, self.p)
      print(msg, file=self.out)
    if to_add < num_viol:
      viol_clqs = heapq.nlargest(
          to_add, viol_clqs, key=lambda s: s[2])
    for nodes, edges, viol in viol_clqs:
      cons.append(self.clique_constraint(nodes, edges))
    return cons


class YCliqueSeparator(CliqueSeparator):

  def __init__(self, max_cliques, p, k):
    CliqueSeparator.__init__(self, max_cliques, p, k)

  def calculate_violation(self, sol, nodes, edges):
    total = sum(sol.y[e] for e in edges)
    return clique_rhs(self.p, self.k) - total

  def clique_constraint(self, nodes, edges):
    return Constraint({}, {e: 1.0 for e in edges}, {}, clique_rhs(self.p, self.k), '>')


class ZCliqueSeparator(CliqueSeparator):

  def __init__(self, max_cliques, p, k, k2):
    CliqueSeparator.__init__(self, max_cliques, p, k)
    self.k2 = k2

  def calculate_violation(self, sol, nodes, edges):
    total = sum(sol.z[e] for e in edges)
    return clique_rhs(self.p, self.k2 * self.k) - total

  def clique_constraint(self, nodes, edges):
    return Constraint({}, {}, {e: 1.0 for e in edges}, clique_rhs(self.p, self.k2 * self.k), '>')


class YZCliqueSeparator(CliqueSeparator):

  def __init__(self, max_cliques, p, k, k2):
    CliqueSeparator.__init__(self, max_cliques, p, k)
    self.k2 = k2

  def calculate_violation(self, sol, nodes, edges):
    lhs = sum(sol.y[e] for e in edges) - self.k2 * sum(sol.z[e] for e in edges)
    t2 = self.p // self.k2
    r2 = self.p % self.k2
    rhs = t2 * nc2(self.k2) + nc2(r2)
    return lhs - rhs

  def clique_constraint(self, nodes, edges):
    t2 = self.p // self.k2
    r2 = self.p % self.k2
    return Constraint({}, {e: 1.0 for e in edges}, {e: -self.k2 for e in edges},
                      t2 * nc2(self.k2) + nc2(r2), '<')


class ProjectedCliqueSeparator(CliqueSeparator):

  def __init__(self, max_cliques, p, k, colours):
    CliqueSeparator.__init__(self, max_cliques, p, k)
    self.colours = colours

  def calculate_violation(self, sol, nodes, edges):
    lhs = sum(sol.x[v, c] for v in nodes for c in self.colours) + \
        sum(sol.y[u, v] for (u, v) in edges)
    return clique_rhs(self.p + len(self.colours), self.k) - lhs

  def clique_constraint(self, nodes, edges):
    return Constraint({(v, c): 1.0 for v in nodes for c in self.colours},
                      {e: 1.0 for e in edges}, {},
                      clique_rhs(self.p + len(self.colours), self.k), '>')


def nc2(n):
  return (n * (n - 1)) // 2


def clique_rhs(p, k):
  t = p // k
  r = p % k
  return 0.5 * t * ((t - 1) * (k - r) + (t + 1) * r)
