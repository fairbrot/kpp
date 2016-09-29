from abc import ABCMeta, abstractmethod
import heapq
import sys
from itertools import combinations

class Structure:
  _fields=[]
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
  _fields=['x', 'y', 'z']

class Constraint(Structure):
  _fields=['x_coefs', 'y_coefs', 'z_coefs', 'rhs', 'op']
  def __str__(self):
    out = ""
    for e, coef in self.y_coefs:
      out+= "+ " + str(coef) + "y[" + str(e) + "]"
    if self.op=='<': out+=' <= '
    elif self.op=='>': out+=' >= '
    elif self.op=='=': out+=' == '
    out += str(self.rhs)
    return out

def p_edge_cliques(max_cliques, p):
  p_cliques=[]
  edge_cliques=[]
  for clq in max_cliques:
    if len(clq) < p: continue
    for p_clq in combinations(clq, p): p_cliques.append(p_clq)
  for clq in p_cliques:
    edge_clq = [(min(u,v), max(u,v)) for (u,v) in combinations(clq,2)]
    edge_cliques.append(edge_clq)
  return edge_cliques

class CliqueSeparator(metaclass=ABCMeta):
  def __init__(self, max_cliques, p):
    self.max_constraints=10
    self.out=sys.stdout
    self.eps=1e-3
    self.edge_cliques=p_edge_cliques(max_cliques,p)
    self.p = p # Clique size

  @abstractmethod
  def calculate_violation(self, sol, e_clq):
    pass

  def find_violated_cliques(self, sol):
    viol_edge_cliques=[]
    for e_clq in self.edge_cliques:
      viol = self.calculate_violation(sol, e_clq)
      if viol > self.eps:
        viol_edge_cliques.append((e_clq, viol))
    return viol_edge_cliques

  @abstractmethod
  def clique_constraint(self, e_clq):
    pass

  def find_violated_constraints(self, sol):
    cons=[]
    viol_edge_cliques=self.find_violated_cliques(sol)
    num_viol=len(viol_edge_cliques)
    to_add=min(num_viol, self.max_constraints)
    print(" Adding {}/{} violated {}-cliques".format(to_add, num_viol, self.p), file=self.out)
    if to_add < num_viol:
      viol_edge_cliques = heapq.nlargest(to_add, viol_edge_cliques,key=lambda s:s[1])
    for e_clq, viol in viol_edge_cliques:
      cons.append(self.clique_constraint(e_clq))
    return cons

class YCliqueSeparator(CliqueSeparator):
  def __init__(self, max_cliques, p, k):
    CliqueSeparator.__init__(self, max_cliques, p)
    self.k = k
    
  def calculate_violation(self, sol, e_clq):
    total = sum(sol.y[e] for e in e_clq)
    return clique_rhs(self.p, self.k) - total

  def clique_constraint(self, e_clq):
    return Constraint({}, {e:1.0 for e in e_clq}, {}, clique_rhs(self.p, self.k), '>')

class ZCliqueSeparator(CliqueSeparator):
  def __init__(self, max_cliques, p, k):
    CliqueSeparator.__init__(self, max_cliques, p)
    self.k = k
    
  def calculate_violation(self, sol, e_clq):
    total = sum(sol.z[e] for e in e_clq)
    return clique_rhs(self.p, self.k) - total

  def clique_constraint(self, e_clq):
    return Constraint({}, {}, {e:1.0 for e in e_clq}, clique_rhs(self.p, self.k),'>')


class YZCliqueSeparator(CliqueSeparator):
  def __init__(self, max_cliques, p):
    CliqueSeparator.__init__(self, max_cliques, p)

  def calculate_violation(self, sol, e_clq):
    lhs = 0.5*sum(sol.y[e] for e in e_clq) - sum(sol.z[e] for e in e_clq)

    return lhs - yz_clique_rhs(self.p)

  def clique_constraint(self, e_clq):
    return Constraint({}, {e:0.5 for e in e_clq}, {e:-1.0 for e in e_clq}, yz_clique_rhs(self.p),'<')

def clique_rhs(p,k):
  t=p//k
  r=p%k
  return 0.5*t*((t-1)*(k-r) + (t+1)*r)

def yz_clique_rhs(p):
  if p % 2: return (p-1)/4
  else: return p/4

