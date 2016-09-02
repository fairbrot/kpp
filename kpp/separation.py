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

class CliqueSeparator:
  def __init__(self, max_cliques, p, k):
    self.edge_cliques=p_edge_cliques(max_cliques,p)
    self.p=p
    self.k=k
    self.max_constraints=10
    self.eps=1e-3
    self.out=sys.stdout

  def find_violated_cliques(self, sol):
    viol_edge_cliques=[]
    y_values = sol.y
    for e_clq in self.edge_cliques:
      total = sum(y_values[e] for e in e_clq)
      diff = clique_rhs(self.p, self.k) - total
      if diff > self.eps:
        viol_edge_cliques.append((e_clq, diff))
    return viol_edge_cliques

  def find_violated_constraints(self, sol):
    cons=[]
    viol_edge_cliques=self.find_violated_cliques(sol)
    num_viol=len(viol_edge_cliques)
    to_add=min(num_viol, self.max_constraints)
    print(" Adding {}/{} violated {}-cliques".format(to_add, num_viol, self.p), file=self.out)
    if to_add < num_viol:
      viol_edge_cliques = heapq.nlargest(to_add, viol_edge_cliques,key=lambda s:s[1])
      
    #print(viol_edge_cliques)
    for e_clq, diff in viol_edge_cliques:
      #print(e_clq)
      cons.append(y_clique_constraint(e_clq, self.p, self.k))
    return cons

def y_clique_constraint(e_clq, p, k):
  y_coefs=dict()
  #print(e_clq)
  for e in e_clq:
    y_coefs[e]=1.0
  #print(y_coefs)
  return Constraint({}, y_coefs,{},clique_rhs(p,k),'>')

def clique_rhs(p,k):
  t=p//k
  r=p%k
  return 0.5*t*((t-1)*(k-r) + (t+1)*r)
